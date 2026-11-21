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
        self.config_dir = global_paths.NAMESPACES_PROFILE_DIR
        self.linuxptp_dir = global_paths.LINUXPTP_DIR
        self.ptp_clients_profile_dir = global_paths.PTP_CLIENTS_PROFILE_DIR
        self.linuxptp_profile_dir = global_paths.LINUXPTP_PROFILE_DIR
        self.log_dir = global_paths.LOG_DIR

        self.loaded_clients = {}

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _resolve_config_path(self, file_cfg: str, base_dir: Path) -> Path:
        path = Path(file_cfg)
        return path if path.is_absolute() else base_dir / path

    def _read_yaml(self, filepath: Path) -> Optional[Dict[str, Any]]:
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)

    def _list_namespaces(self) -> List[str]:
        result = subprocess.run(["ip", "netns", "list"], capture_output=True, text=True, check=True)
        return [line.split()[0] for line in result.stdout.strip().splitlines() if line]

    # ------------------------------------------------------------------
    # Namespaces
    # ------------------------------------------------------------------

    def load_namespaces(self, file_cfg: Optional[str] = None) -> tuple[bool, Optional[str]]:
        if not file_cfg:
            return False, "Configuration file path is missing."

        filepath_cfg = self._resolve_config_path(file_cfg, self.config_dir)
        if not filepath_cfg.exists():
            return False, f"Configuration file not found: {filepath_cfg}"

        try:
            config = self._read_yaml(filepath_cfg)
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

        filepath_cfg = self._resolve_config_path(file_cfg, self.config_dir)
        try:
            config = self._read_yaml(filepath_cfg)
        except Exception as e:
            return False, f"Error reading file: {str(e)}"

        for ns, cfg in (config.get("namespaces") or {}).items():
            ip_mask, gw, iface = cfg.get("IP/mask"), cfg.get("gateway"), cfg.get("interface")
            if not all([ns, ip_mask, iface]):
                continue

            try:
                self._run(f"ip netns add {ns}")
                self._run(f"ip link set {iface} netns {ns}")
                self._run(f"ip netns exec {ns} ip addr add {ip_mask} dev {iface}")
                self._run(f"ip netns exec {ns} ip link set dev {iface} up")
                if gw:
                    self._run(f"ip netns exec {ns} ip route add default via {gw} dev {iface}")
                self._run(f"ip netns exec {ns} sysctl -w net.ipv6.conf.{iface}.disable_ipv6=1")
            except subprocess.CalledProcessError as e:
                return False, f"Error creating/configuring namespace '{ns}': {str(e)}"

        return True, None

    @staticmethod
    def _run(cmd: str) -> None:
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def stop_namespaces(self) -> tuple[bool, Optional[str]]:
        try:
            for ns in self._list_namespaces():
                subprocess.run(["ip", "netns", "delete", ns], check=True)
            return True, None
        except subprocess.CalledProcessError as e:
            return False, str(e)

    # ------------------------------------------------------------------
    # PTP clients
    # ------------------------------------------------------------------

    def load_clients(self, file_cfg: Optional[str] = None) -> bool:
        if not file_cfg:
            return False

        filepath_cfg = self._resolve_config_path(file_cfg, self.ptp_clients_profile_dir)
        if not filepath_cfg.exists():
            return False

        try:
            yaml_data = self._read_yaml(filepath_cfg) or {}
            self.loaded_clients = yaml_data.get("ptp_clients", {})

            existing_namespaces = set(self._list_namespaces())
            for client_name, client_data in list(self.loaded_clients.items()):
                if client_data.get("namespace") not in existing_namespaces:
                    del self.loaded_clients[client_name]

            return len(self.loaded_clients) > 0
        except Exception:
            return False

    def start_ptp(self, stop_existing: bool = True) -> List[Dict[str, Any]]:
        if stop_existing:
            self.stop_ptp()

        if not self.loaded_clients:
            return []

        self.log_dir.mkdir(parents=True, exist_ok=True)
        launched_processes = []

        for client_name, data in self.loaded_clients.items():
            config_path = self.linuxptp_profile_dir / data["config"]
            namespace = data["namespace"]
            log_path = self.log_dir / f"ptp-{client_name}.log"
            log_path.write_text(f"[{datetime.now()}] Log reset for {client_name}\n")

            command = [
                "sudo", "ip", "netns", "exec", namespace,
                self.linuxptp_dir / "ptp4l", "-f", str(config_path), "-H", "-q", "-m"
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

                ptp4l_proc = self._find_ptp4l_child(ptp_process.pid)
                if not ptp4l_proc:
                    data["status"] = "Failed"
                    continue

                info = {"pid": ptp4l_proc.pid, "status": "Running"}
                data.update(info)
                launched_processes.append({"client": client_name, "log": str(log_path), **info})

            except Exception:
                data["status"] = "Error"

        return launched_processes

    @staticmethod
    def _find_ptp4l_child(parent_pid: int):
        try:
            if not psutil.pid_exists(parent_pid):
                return None
            for child in psutil.Process(parent_pid).children(recursive=True):
                if "ptp4l" in child.name():
                    return child
        except (psutil.NoSuchProcess, ProcessLookupError, IndexError):
            pass
        return None

    def stop_ptp(self) -> bool:
        result = subprocess.run(["pgrep", "-a", "ptp4l"], capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()

        if not lines:
            return True

        try:
            for line in lines:
                subprocess.run(["kill", "-9", line.split()[0]], check=True)

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
            namespace = data["namespace"]
            config_path = self.linuxptp_profile_dir / data["config"]

            try:
                server_ip = next(
                    (line.strip().split()[1] for line in config_path.read_text().splitlines()
                     if "UDPv4" in line and len(line.split()) >= 2),
                    None
                )
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

        log_path = self.log_dir / f"ptp-{client_name}.log"
        if not log_path.exists():
            return f"Error: Log file for {client_name} does not exist."

        try:
            return "".join(log_path.read_text().splitlines(keepends=True)[-100:])
        except Exception as e:
            return f"Error reading log file: {e}"
