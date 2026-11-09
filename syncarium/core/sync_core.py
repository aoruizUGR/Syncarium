#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_core.py

**Project**: Syncarium Platform
**Description**: Core logic for managing PTP (Precision Time Protocol) clients, 
                 process lifecycle, and network namespace verification.
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada
**License**: GPLv3
"""

import os
import time
import subprocess
import yaml
import psutil
from pathlib import Path
from datetime import datetime
from threading import Lock
from typing import Optional, Dict, Any, List

import syncarium.options.global_vars as global_vars

class SyncCore:
    """
    Manages the synchronization logic, including loading PTP clients from 
    configurations, starting/stopping PTP processes in namespaces, 
    and performing connectivity checks.
    """

    def __init__(self) -> None:
        """
        Initializes the SyncCore instance with paths and thread-safe locks.
        """
        self.ptp_profile_dir: Path = global_vars.PTP_PROFILE_DIR
        self.log_dir: Path = global_vars.LOG_DIR

        self.print_lock: Lock = Lock()

        self.loaded_clients: Dict[str, Dict[str, str]] = {}

    def load_clients(
        self,
        file_cfg: Optional[str] = None
    ) -> bool:
        """
        Loads PTP client configurations from a YAML file and validates 
        their existence in current network namespaces.

        Args:
            file_cfg (Optional[str]): Path to the YAML configuration file.

        Returns:
            bool: True if clients were successfully loaded and validated, False otherwise.
        """
        if not file_cfg:
            return False

        filepath_cfg = Path(file_cfg)
        if not filepath_cfg.is_absolute():
            filepath_cfg = self.ptp_profile_dir / file_cfg

        if not filepath_cfg.exists():
            return False

        try:
            with open(filepath_cfg, 'r') as f:
                yaml_data: Dict = yaml.safe_load(f)
                self.loaded_clients = yaml_data.get("ptp_clients", {})

            ns_result = subprocess.run(["ip", "netns", "list"], stdout=subprocess.PIPE, text=True)
            existing_namespaces: set[str] = {
                line.split()[0] for line in ns_result.stdout.strip().splitlines()
            }

            to_delete = []
            for client_name, client_data in list(self.loaded_clients.items()):
                ns = client_data.get("namespace")
                if ns not in existing_namespaces:
                    to_delete.append(client_name)

            for client_name in to_delete:
                del self.loaded_clients[client_name]

            return len(self.loaded_clients) > 0

        except Exception:
            return False
        
    def start_ptp(
        self,
        stop_existing: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Starts PTP processes for all loaded clients within their respective namespaces.

        Args:
            stop_existing (bool): If True, stops any running ptp4l processes before starting new ones.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the status, PID, 
                                   and log path for each launched client.
        """
        if stop_existing:
            result = subprocess.run(["pgrep", "-a", "ptp4l"], capture_output=True, text=True)
            lines = result.stdout.strip().splitlines()
            if lines:
                self.stop_ptp(preconfirmation=True)

        if not self.loaded_clients:
            return []

        launched_processes = []
        for client_name, data in self.loaded_clients.items():
            config_path: Path = self.ptp_profile_dir / data["config"]
            namespace: str = data["namespace"]
            log_path: Path = self.log_dir / f"ptp-{client_name}.log"

            if not config_path.exists():
                continue

            self.log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_path, 'w') as f:
                f.write(f"[{datetime.now()}] Log reset for {client_name}\n")

            ptp4l_bin = "/home/aoruiz/linuxptp-3.1.1/ptp4l" 
            command: list[str] = [
                "ip", "netns", "exec", namespace,
                ptp4l_bin, "-f", str(config_path), "-H", "-q", "-m"
            ]

            try:
                with open(log_path, 'a') as log_file:
                    ptp_process = subprocess.Popen(
                        ["sudo", "-n"] + command,
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
                print(f"Error launching PTP on {client_name}: {e}")
                continue
        
        return launched_processes
    
    def stop_ptp(
        self,
        preconfirmation: bool = False
    ) -> bool:
        """
        Stops all active PTP processes and clears the log directory.

        Args:
            preconfirmation (bool): If True, used to handle internal state before killing.

        Returns:
            bool: True if the processes were stopped successfully, False otherwise.
        """
        result = subprocess.run(["pgrep", "-a", "ptp4l"], capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()

        if not lines:
            return True

        try:
            for line in lines:
                pid, *cmd = line.split()
                subprocess.run(["sudo", "kill", "-9", pid], check=True)

            if self.log_dir.exists():
                for archivo in self.log_dir.iterdir():
                    if archivo.is_file():
                        archivo.unlink()

            self.loaded_clients = {}
            return True

        except Exception:
            return False

    def ping_server(self) -> List[Dict[str, str]]:
        """
        Pings the server defined in the configuration for each loaded client.

        Returns:
            List[Dict[str, str]]: A list of results containing client names, 
                                   success status, and ping output.
        """
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
        """
        Retrieves the last 100 lines of the log file for a specific client.

        Args:
            client_name (str): Name of the client whose logs should be retrieved.

        Returns:
            str: The last 100 lines of the log file or an error message.
        """
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