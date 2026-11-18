import os
import time
import subprocess
import yaml
import psutil

from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

import path_config.global_paths as global_paths


class LocalManager:

    def __init__(self) -> None:
        self.config_dir: Path = global_paths.NAMESPACES_PROFILE_DIR
        self.linuxptp_dir: Path = global_paths.LINUXPTP_DIR
        self.ptp_clients_profile_dir: Path = global_paths.PTP_CLIENTS_PROFILE_DIR
        self.linuxptp_profile_dir: Path = global_paths.LINUXPTP_PROFILE_DIR
        self.log_dir: Path = global_paths.LOG_DIR

        self.loaded_clients: Dict[str, Dict[str, str]] = {}

    def load_namespaces(self, file_cfg: Optional[str] = None) -> tuple[bool, Optional[str]]:
        if not file_cfg:
            return False, "Configuration file path is missing."

        filepath_cfg: Path = Path(file_cfg)
        if not filepath_cfg.is_absolute():
            filepath_cfg = self.config_dir / file_cfg

        if not filepath_cfg.exists():
            return False, f"Configuration file not found: {filepath_cfg}"

        try:
            with open(filepath_cfg, 'r') as f:
                config: Dict = yaml.safe_load(f)
            
            if config is None:
                return False, "Configuration file is empty."

            if config.get("namespaces") is None:
                return False, "Configuration file does not contain a 'namespaces' key."
            
            return True, None
        except Exception as e:
            return False, f"YAML Parsing Error: {str(e)}"

    def start_namespaces(self, file_cfg: Optional[str] = None) -> tuple[bool, Optional[str]]:
        success, error_msg = self.load_namespaces(file_cfg)
        if not success:
            return False, error_msg
        
        filepath_cfg: Path = Path(file_cfg)
        if not filepath_cfg.is_absolute():
            filepath_cfg = self.config_dir / file_cfg

        try:
            with open(filepath_cfg, 'r') as f:
                config: Dict = yaml.safe_load(f)
        except Exception as e:
            return False, f"Error reading file: {str(e)}"
        
        namespaces_cfg = config.get("namespaces", {})
        
        for key, cfg in namespaces_cfg.items():
            ns = key
            ip_mask = cfg.get("IP/mask")
            gw = cfg.get("gateway")
            iface = cfg.get("interface")

            if not all([ns, ip_mask, iface]):
                continue

            try:
                subprocess.run(f"ip netns add {ns}", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(f"ip link set {iface} netns {ns}", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(f"ip netns exec {ns} ip addr add {ip_mask} dev {iface}", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(f"ip netns exec {ns} ip link set dev {iface} up", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                if gw:
                    subprocess.run(f"ip netns exec {ns} ip route add default via {gw} dev {iface}", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                subprocess.run(f"ip netns exec {ns} sysctl -w net.ipv6.conf.{iface}.disable_ipv6=1", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError as e:
                return False, f"Error creating/configuring namespace '{ns}': {str(e)}"
        
        return True, None

    def stop_namespaces(self) -> tuple[bool, Optional[str]]:
        try:
            result = subprocess.run(["ip", "netns", "list"], capture_output=True, text=True, check=True)
            namespaces: List[str] = [
                line.split()[0] for line in result.stdout.strip().splitlines() if line
            ]

            for ns in namespaces:
                subprocess.run(["ip", "netns", "delete", ns], check=True)

            return True, None

        except subprocess.CalledProcessError as e:
            return False, str(e)

    def load_clients(self, file_cfg: Optional[str] = None) -> bool:
        if not file_cfg:
            return False

        # Corregir el path para archivos relativos
        if not Path(file_cfg).is_absolute():
            filepath_cfg = self.ptp_clients_profile_dir / file_cfg
        else:
            filepath_cfg = Path(file_cfg)

        if not filepath_cfg.exists():
            return False

        try:
            with open(filepath_cfg, 'r') as f:
                yaml_data: Dict = yaml.safe_load(f)
                self.loaded_clients = yaml_data.get("ptp_clients", {})

            ns_result = subprocess.run(["ip", "netns", "list"], stdout=subprocess.PIPE, text=True, check=True)
            existing_namespaces: set[str] = {
                line.split()[0] for line in ns_result.stdout.strip().splitlines()
            }

            # Eliminar clientes cuyo namespace no exista
            for client_name, client_data in list(self.loaded_clients.items()):
                ns = client_data.get("namespace")
                if ns not in existing_namespaces:
                    del self.loaded_clients[client_name]

            return len(self.loaded_clients) > 0

        except Exception as e:
            return False

    def start_ptp(self, stop_existing: bool = True) -> List[Dict[str, Any]]:
        if stop_existing:
            self.stop_ptp()

        if not self.loaded_clients:
            return []

        launched_processes = []
        for client_name, data in self.loaded_clients.items():
            config_path: Path = self.linuxptp_profile_dir / data["config"]
            namespace: str = data["namespace"]
            log_path: Path = self.log_dir / f"ptp-{client_name}.log"

            self.log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_path, 'w') as f:
                f.write(f"[{datetime.now()}] Log reset for {client_name}\n")

            ptp4l_bin = self.linuxptp_dir / "ptp4l"
            command: list[str] = [
                "sudo", "ip", "netns", "exec", namespace,
                ptp4l_bin, "-f", str(config_path), "-H", "-q", "-m"
            ]

            try:
                with open(log_path, 'a') as log_file:
                    ptp_process = subprocess.Popen(
                        command,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        stdin=subprocess.DEVNULL,
                        close_fds=True,
                        preexec_fn=os.setpgrp
                    )

                time.sleep(0.8)

                ptp4l_proc = None
                try:
                    if psutil.pid_exists(ptp_process.pid):
                        parent = psutil.Process(ptp_process.pid)
                        for child in parent.children(recursive=True):
                            if "ptp4l" in child.name():
                                ptp4l_proc = child
                                break
                except (psutil.NoSuchProcess, ProcessLookupError, IndexError):
                    pass

                if ptp4l_proc:
                    self.loaded_clients[client_name].update({
                        "pid": ptp4l_proc.pid,
                        "status": "Running"
                    })
                    
                    launched_processes.append({
                        "client": client_name,
                        "pid": ptp4l_proc.pid,
                        "log": str(log_path),
                        "status": "Running"
                    })
                else:
                    self.loaded_clients[client_name]["status"] = "Failed"
                    
            except Exception as e:
                self.loaded_clients[client_name]["status"] = "Error"
                continue
        
        return launched_processes

    def stop_ptp(self) -> bool:
        result = subprocess.run(["pgrep", "-a", "ptp4l"], capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()

        if not lines:
            return True

        try:
            for line in lines:
                pid, *cmd = line.split()
                subprocess.run(["kill", "-9", pid], check=True)

            if self.log_dir.exists():
                for archivo in self.log_dir.iterdir():
                    if archivo.is_file():
                        archivo.unlink()

            self.loaded_clients = {}
            return True

        except Exception:
            return False

    def ping_server(self) -> List[Dict[str, str]]:
        if not self.loaded_clients:
            return []

        results = []
        for client_name, data in self.loaded_clients.items():
            namespace: str = data["namespace"]
            config_path: Path = self.ptp_profile_dir / data["config"]

            try:
                with open(config_path, "r") as f:
                    lines = f.readlines()
                server_ip = None
                for line in lines:
                    if "UDPv4" in line:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            server_ip = parts[1]
                            break

                if not server_ip:
                    results.append({"client": client_name, "status": "No Server IP in Config"})
                    continue

                output = subprocess.check_output(
                    ["sudo", "ip", "netns", "exec", namespace, "ping", "-c", "5", server_ip],
                    stderr=subprocess.STDOUT
                ).decode()

                results.append({
                    "client": client_name,
                    "status": "Success",
                    "output": output.strip().split('\n')[-1]
                })

            except Exception as e:
                results.append({"client": client_name, "status": f"Error: {str(e)}"})

            time.sleep(0.5)
        return results

    def show_logs(self, client_name: str) -> str:
        if client_name not in self.loaded_clients:
            return f"Error: Client '{client_name}' is not loaded."

        log_path: Path = self.log_dir / f"ptp-{client_name}.log"
        
        if not log_path.exists():
            return f"Error: Log file for {client_name} does not exist."

        try:
            with open(log_path, 'r') as f:
                lines = f.readlines()
                return "".join(lines[-100:])
        except Exception as e:
            return f"Error reading log file: {e}"