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
        self.load_dir = global_paths.TRAFFIC_PROFILE_DIR
        self.utils_dir = global_paths.UTILS_DIR
        self.dpdk_profile_dir = global_paths.DPDK_PROFILE_DIR
        self.scripts_dir = global_paths.SCRIPTS_DIR
        self.trex_pid = None
        self.stl_env = None
        self.stl_process = None
        self.stl_state = None
        self.stl_filename = None
        self.stl_args = None
        self.stl_duration = None
        self.stl_start_time = None
        self.traffic_gen_name = None
        self.traffic_gen_dir = global_paths.TGEN_DIR
        self.traffic_gen_server_dir = None
        self.traffic_gen_client_dir = None
        self.stl_client = None
        self.stl_connected = False

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------
    @staticmethod
    def _read_yaml(filepath) -> Optional[Dict[str, Any]]:
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)

    @staticmethod
    def _find_trex_processes() -> List[str]:
        result = subprocess.run(["pgrep", "-a", "_t-rex-64"], capture_output=True, text=True)
        return [line.split()[0] for line in result.stdout.strip().splitlines() if line]

    @staticmethod
    def _extract_config_path(cmd: str) -> str:
        if "--cfg" not in cmd:
            return "Unknown"
        try:
            return cmd[cmd.find("--cfg") + 5:].split()[0].strip()
        except IndexError:
            return "Unknown"

    def _ensure_generator_selected(self) -> bool:
        """Garantiza que hay un generador seleccionado; si no, elige el primero."""
        if self.traffic_gen_server_dir is not None:
            return True
        try:
            generators = [f.name for f in global_paths.TGEN_DIR.iterdir() if f.is_dir()]
        except Exception:
            print("Failed to initialize traffic generator")
            return False
        if not generators:
            print("No traffic generators found")
            return False
        return self.select_traffic_gen(generators[0])

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
            config = self._read_yaml(filepath_cfg)
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

    def start_trex_server(self, sleep_seconds: int = 15, file_cfg: Optional[str] = None) -> bool:
        if not self._ensure_generator_selected():
            print("Traffic generator server directory not initialized")
            return False

        trex_pids = self._find_trex_processes()
        if trex_pids:
            self.stop_trex_server()

        if file_cfg is None:
            files = [f.name for f in self.traffic_gen_server_dir.iterdir() if f.name.startswith("trex_") and f.suffix == ".yaml"]
            if not files:
                return False
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

        try:
            from trex.stl.api import STLClient  # type: ignore
            self.stl_client = STLClient()
            self.stl_client.connect()
            self.stl_connected = True
            print("STL client connected successfully")
        except Exception as e:
            print(f"Error establishing STL client connection: {e}")
            self.stl_connected = False

        return True

    def stop_trex_server(self) -> bool:
        if self.stl_connected and self.stl_client:
            try:
                self.stl_client.disconnect()
                self.stl_connected = False
                print("STL client disconnected successfully")
            except Exception as e:
                print(f"Error disconnecting STL client: {e}")

        if self.trex_pid is not None:
            try:
                subprocess.run(["sudo", "kill", "-TERM", str(self.trex_pid)], check=True, capture_output=True)
                self.trex_pid = None
                return True
            except subprocess.CalledProcessError:
                pass

        for pid in self._find_trex_processes():
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
                    return {
                        "pid": self.trex_pid,
                        "config": self._extract_config_path(result.stdout.strip()),
                        "status": "Running"
                    }
            except (subprocess.CalledProcessError, ValueError):
                self.trex_pid = None

        pids = self._find_trex_processes()
        if not pids:
            return {"pid": None, "config": "None", "status": "Stopped"}

        result = subprocess.run(["ps", "-p", pids[0], "-o", "cmd="], capture_output=True, text=True)
        self.trex_pid = int(pids[0])
        return {
            "pid": pids[0],
            "config": self._extract_config_path(result.stdout.strip()),
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
            dpdk_drivers = {"igb_uio", "vfio-pci", "uio_pci_generic"}

            for line in result.stdout.splitlines():
                if not (line.strip() and line[0].isdigit() and ":" in line[:5]):
                    continue
                parts = line.split()
                if len(parts) < 4:
                    continue
                driver = next((part.split("=", 1)[1] for part in parts if part.startswith("drv=")), "None")
                if driver in dpdk_drivers:
                    active_devices.append({
                        "slot": parts[0],
                        "device": parts[1].strip("'"),
                        "driver": driver
                    })
        except Exception as e:
            print(f"Error parsing dpdk_devbind output: {e}")

        return active_devices

    def get_trex_stats(self) -> Optional[Dict[str, Any]]:
        # Verificar si el cliente está conectado antes de intentar obtener estadísticas
        if not self.stl_connected or self.stl_client is None:
            error_msg = "TRex server is not connected. Please start the TRex server first."
            print(error_msg)
            return {"error": error_msg}

        try:
            ports = self.stl_client.get_all_ports()
            return {
                "stats": self.stl_client.get_stats(ports),
                "port_attrs": {port_id: self.stl_client.get_port_attr(port_id) for port_id in ports}
            }
        except Exception as e:
            error_msg = f"Error comunicando con TRex: {e}"
            print(error_msg)
            return {"error": error_msg}

    def clear_trex_stats(self) -> bool:
        try:
            self.stl_client.clear_stats()
            return True
        except Exception as e:
            error_msg = f"Error clearing TRex stats: {e}"
            print(error_msg)
            return False

    def start_stl_program(
        self,
        file_cfg: Optional[Path] = None,
        stl_duration: Optional[int] = None,
        stl_output: Optional[str] = None
    ) -> bool:
        if not self._ensure_generator_selected():
            print("Traffic generator client directory not initialized")
            return False

        if self.stl_process and self.stl_process.poll() is None:
            return False

        if file_cfg:
            filepath_cfg = file_cfg
        else:
            files = [str(f.relative_to(self.load_dir)) for f in self.load_dir.rglob("*.yaml") if f.is_file()]
            if not files:
                return False
            filepath_cfg = self.load_dir / files[0]

        stl = self._read_yaml(filepath_cfg)

        self.stl_filename = stl.get("traffic_gen_stl_program")

        stl_args = stl.get("traffic_gen_stl_args", {})
        if stl_duration and stl_output:
            self.stl_duration = stl_duration
            self.stl_args = [str(stl_duration)] + [str(v) for v in stl_args.values()] + [str(stl_output)]
        else:
            self.stl_duration = stl_args.get("duration")
            self.stl_args = [str(v) for v in stl_args.values()]

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
