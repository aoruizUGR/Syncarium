import os
import time
import subprocess
import yaml
import sys

from pathlib import Path
from typing import Optional, Dict, List, Any

import path_config.global_paths as global_paths
import syncarium.utils.config_hugepages as hugepages_module


class TrafficGenerator:

    def __init__(self) -> None:
        self.load_dir: Path = global_paths.TRAFFIC_PROFILE_DIR
        self.utils_dir: Path = global_paths.UTILS_DIR
        self.dpdk_profile_dir: Path = global_paths.DPDK_PROFILE_DIR
        self.scripts_dir: Path = global_paths.SCRIPTS_DIR
        self.trex_pid: Optional[int] = None
        self.stl_env: Optional[Dict] = None
        self.stl_process: Optional[Any] = None
        self.stl_state: Optional[str] = None
        self.stl_filename: Optional[str] = None
        self.stl_args: Optional[List[str]] = None
        self.stl_duration: Optional[float] = None
        self.stl_start_time: Optional[float] = None
        self.traffic_gen_name: Optional[str] = None
        self.traffic_gen_dir: Path = global_paths.TGEN_DIR
        self.traffic_gen_server_dir: Optional[Path] = None
        self.traffic_gen_client_dir: Optional[Path] = None

    def select_traffic_gen(self, selected_name: str) -> bool:
        import streamlit as st
        self.traffic_gen_dir = global_paths.TGEN_DIR
        
        if not self.traffic_gen_dir.exists():
            return False
        
        self.traffic_gen_name = selected_name
        self.traffic_gen_server_dir = self.traffic_gen_dir / self.traffic_gen_name / "server"
        self.traffic_gen_client_dir = self.traffic_gen_dir / self.traffic_gen_name / "client"
        
        if not self.traffic_gen_server_dir.exists():
            print(f"Server directory does not exist: {self.traffic_gen_server_dir}")
            return False
        
        self.stl_env = os.environ.copy()
        trex_interactive = self.traffic_gen_server_dir / "automation/trex_control_plane/interactive"
        trex_external_libs = self.traffic_gen_server_dir / "external_libs/scapy-2.4.3"

        for p in [str(trex_interactive), str(trex_external_libs)]:
            if p not in sys.path:
                sys.path.insert(0, p)
        
        st.session_state["selected_generator"] = selected_name
        
        return True
    
    def load_dpdk_driver(self, file_cfg: Optional[str] = None) -> bool:  
        if file_cfg:
            filepath_cfg = (self.dpdk_profile_dir / file_cfg).resolve()
        else:
            files = [f.name for f in self.dpdk_profile_dir.iterdir() if f.suffix == ".yaml"]
            if not files:
                return False
            filepath_cfg = (self.dpdk_profile_dir / files[0]).resolve()

        try:
            with open(filepath_cfg, 'r') as f:
                config: Dict = yaml.safe_load(f)
        except Exception as e:
            print(f"Error reading config file {filepath_cfg}: {e}")
            return False

        dpdk_driver = config.get("dpdk_driver")
        n_ports = config.get("n_ports")

        if not dpdk_driver or not isinstance(n_ports, int):
            print(f"Invalid configuration in {filepath_cfg}: dpdk_driver or n_ports missing/invalid")
            return False

        ports = [config.get(f"pci_bus_port{i}") for i in range(n_ports)]
        ports = [p for p in ports if p is not None and str(p).strip() != ""] 
        
        if not ports:
            print(f"No valid ports found in {filepath_cfg}")
            return False

        try:
            subprocess.run(["sudo", "-S", "modprobe", dpdk_driver], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running modprobe {dpdk_driver}: {e.stderr.strip()}")
            return False

        nic_bind_script = (self.utils_dir / "dpdk_devbind.py").resolve()
        cmd = ["sudo", "-S", "python3", str(nic_bind_script), "-b", dpdk_driver] + ports
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running dpdk_devbind.py: {e.stderr.strip()}")
            return False
        
        return True

    def start_trex_server(self, sleep_seconds: int = 10, file_cfg: Optional[str] = None) -> bool:
        if not hasattr(self, 'traffic_gen_server_dir') or self.traffic_gen_server_dir is None:
            try:
                generators = [f.name for f in global_paths.TGEN_DIR.iterdir() if f.is_dir()]
                if generators:
                    self.select_traffic_gen(generators[0])
                else:
                    print("No traffic generators found")
                    return False
            except Exception:
                print("Failed to initialize traffic generator")
                return False
        
        if not hasattr(self, 'traffic_gen_server_dir') or self.traffic_gen_server_dir is None:
            print("Traffic generator server directory not initialized")
            return False
            
        result = subprocess.run(["pgrep", "-a", "_t-rex-64"], capture_output=True, text=True)
        if result.stdout.strip():
            self.stop_trex_server()
        
        if file_cfg is None:
            files = [f.name for f in self.traffic_gen_server_dir.iterdir() if f.name.startswith("trex_") and f.suffix == ".yaml"]
            if not files: return False
            filepath_cfg = self.traffic_gen_server_dir / files[0]
        else:
            filepath_cfg = self.traffic_gen_server_dir / file_cfg
        
        try:
            result = hugepages_module.configure_hugepages()
            if not result:
                print("Error running config_hugepages.py")
                return False
        except Exception as e:
            print(f"Error running config_hugepages.py: {e}")
            return False
        
        command = [str(self.traffic_gen_server_dir / "t-rex-64"), "-i", "--software", "--no-scapy-server", "--cfg", str(filepath_cfg.resolve())]
        
        try:
            process = subprocess.Popen(
                ["sudo"] + command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                cwd=self.traffic_gen_server_dir
            )
            self.trex_pid = process.pid
        except Exception as e:
            print(f"Error starting TRex server: {e}")
            return False
        
        time.sleep(sleep_seconds)
        
        return True

    def stop_trex_server(self) -> bool:
        if self.trex_pid is not None:
            try:
                subprocess.run(["sudo", "kill", "-TERM", str(self.trex_pid)], check=True, capture_output=True)
                self.trex_pid = None
                return True
            except subprocess.CalledProcessError:
                pass

        result = subprocess.run(["pgrep", "-a", "_t-rex-64"], capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()
        if not lines:
            return True
        
        for line in lines:
            pid = line.split()[0]
            try:
                subprocess.run(["sudo", "kill", "-9", pid], check=True)
            except subprocess.CalledProcessError:
                pass
        self.trex_pid = None
        return True

    def get_server_status(self) -> Dict[str, Any]:
        if self.trex_pid is not None:
            try:
                result = subprocess.run(["ps", "-p", str(self.trex_pid), "-o", "pid,cmd"], capture_output=True, text=True)
                if result.returncode == 0 and self.trex_pid == int(result.stdout.split()[0]):
                    cmd = result.stdout.strip()
                    config_path = "Unknown"
                    if "--cfg" in cmd:
                        try:
                            cfg_idx = cmd.find("--cfg")
                            config_path = cmd[cfg_idx + 5:].split()[0].strip()
                        except IndexError:
                            pass
                    return {
                        "pid": self.trex_pid,
                        "config": config_path,
                        "status": "Running"
                    }
            except (subprocess.CalledProcessError, ValueError):
                self.trex_pid = None

        result = subprocess.run(["pgrep", "-a", "_t-rex-64"], capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()
        
        if not lines:
            return {
                "pid": None,
                "config": "None",
                "status": "Stopped"
            }
        
        line = lines[0]
        parts = line.split()
        pid = parts[0]
        
        config_path = "Unknown"
        if "--cfg" in line:
            try:
                cfg_idx = line.find("--cfg")
                config_path = line[cfg_idx + 5:].split()[0].strip()
            except IndexError:
                pass
        
        self.trex_pid = int(pid)
        return {
            "pid": pid,
            "config": config_path,
            "status": "Running"
        }

    def get_active_dpdk_drivers(self) -> List[Dict[str, str]]:
        active_devices = []
        
        try:
            result = subprocess.run(
                ["python3", str(self.utils_dir / "dpdk_devbind.py"), "-s"],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout
            lines = output.splitlines()
            dpdk_drivers = ["igb_uio", "vfio-pci", "uio_pci_generic"]
            
            for line in lines:
                if line.strip() and line[0].isdigit() and ":" in line[:5]:
                    parts = line.split()
                    if len(parts) >= 4:
                        slot = parts[0]
                        device_name = parts[1].strip("'")
                        
                        driver = "None"
                        for part in parts:
                            if part.startswith("drv="):
                                driver = part.split("=")[1]
                                break
                        
                        if driver in dpdk_drivers:
                            active_devices.append({
                                "slot": slot,
                                "device": device_name,
                                "driver": driver
                            })
        except Exception as e:
            print(f"Error parsing dpdk_devbind output: {e}")
            
        return active_devices

    def get_trex_stats(self) -> Optional[Dict[str, Any]]:
        from trex.stl.api import STLClient # pyright: ignore[reportMissingImports]

        if STLClient is None:
            print("Error: STLClient is not available. Check the TRex path configuration.")
            return {"error": "STLClient is not available. Check the TRex path configuration."}

        client = STLClient()
        try:
            client.connect()
            
            ports = client.get_all_ports()
            stats = client.get_stats(ports)
            port_attrs = {}
            for port_id in ports:
                port_attrs[port_id] = client.get_port_attr(port_id)
            return {
                "stats": stats,
                "port_attrs": port_attrs
            }
            
        except Exception as e:
            error_msg = f"Error comunicando con TRex: {e}"
            print(error_msg)
            return {"error": error_msg}
            
        finally:
            try:
                client.disconnect()
            except Exception:
                pass

    def start_stl_program(
        self,
        file_cfg: Optional[Path] = None,
        stl_duration: Optional[int] = None,
        stl_output: Optional[str] = None
    ) -> bool:

        if not hasattr(self, 'traffic_gen_client_dir') or self.traffic_gen_client_dir is None:
            try:
                generators = [f.name for f in global_paths.TGEN_DIR.iterdir() if f.is_dir()]
                if generators:
                    self.select_traffic_gen(generators[0])
                else:
                    print("No traffic generators found")
                    return False
            except Exception:
                print("Failed to initialize traffic generator")
                return False

        if not hasattr(self, 'traffic_gen_client_dir') or self.traffic_gen_client_dir is None:
            print("Traffic generator client directory not initialized")
            return False

        if self.stl_process and self.stl_process.poll() is None:
            return False

        if file_cfg:
            filepath_cfg = file_cfg
        else:
            files = [str(f.relative_to(self.load_dir)) for f in self.load_dir.rglob("*.yaml") if f.is_file()]
            if not files: return False
            filepath_cfg = self.load_dir / files[0]

        with open(filepath_cfg, 'r') as f:
            stl = yaml.safe_load(f)

        self.stl_filename = stl.get("traffic_gen_stl_program")
        
        if stl_duration and stl_output:
            self.stl_duration = stl_duration
            self.stl_args = [str(self.stl_duration)] + [str(v) for v in stl.get("traffic_gen_stl_args", {}).values()] + [str(stl_output)]
        else:
            self.stl_duration = stl.get("traffic_gen_stl_args", {}).get("duration")
            self.stl_args = [str(v) for v in stl.get("traffic_gen_stl_args", {}).values()]

        stl_filepath = self.traffic_gen_client_dir / self.stl_filename
        if not stl_filepath.exists():
            return False

        self.stl_start_time = time.time()
        cmd = ["python", str(stl_filepath)] + self.stl_args
        
        self.stl_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            env=self.stl_env,
            start_new_session=True
        )

        self.stl_state = "Launched"
        return True

    def stop_stl_program(self, preconfirmation: bool = False) -> bool:

        if self.stl_state != "Launched":
            return True

        try:
            if self.stl_process:
                self.stl_process.terminate()
            self.stl_state = "Forced Stop"
            return True
        except Exception:
            return False
