#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plat_init.py

**Project**: Syncarium Platform
**Description**: Handles platform initialization, including device drivers and network namespace management.
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada
**License**: GPLv3
"""

import subprocess
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
import syncarium.options.global_vars as global_vars

class PlatInit:
    """
    Handles the platform initialization tasks such as loading drivers and managing 
    network namespaces.
    """

    def __init__(self) -> None:
        """
        Initializes the PlatInit instance with default directories from global variables.
        """
        self.config_dir: Path = global_vars.NAMESPACES_DIR
        self.scripts_dir: Path = global_vars.SCRIPTS_DIR

    def load_device_driver(self, driver_name: str) -> bool:
        """
        Executes the shell script corresponding to a specific device driver.

        Args:
            driver_name (str): The name of the driver to load.

        Returns:
            bool: True if the script was executed successfully, False otherwise.
        """
        script_path: Path = self.scripts_dir / f"devdriver_{driver_name}.sh"

        if not script_path.exists():
            return False

        try:
            subprocess.run(["chmod", "a+x", str(script_path)], check=True)
            subprocess.run([str(script_path)], check=True)
            return True

        except subprocess.CalledProcessError:
            return False

    def load_namespaces(self, file_cfg: Optional[str] = None) -> bool:
        """
        Validates if a configuration file contains the required namespace definitions.

        Args:
            file_cfg (Optional[str]): Path to the YAML configuration file.

        Returns:
            bool: True if the file exists and contains the "namespaces" key, False otherwise.
        """
        if not file_cfg:
            return False

        filepath_cfg: Path = Path(file_cfg)
        if not filepath_cfg.is_absolute():
            filepath_cfg = self.config_dir / file_cfg

        if not filepath_cfg.exists():
            return False

        try:
            with open(filepath_cfg, 'r') as f:
                config: Dict = yaml.safe_load(f)
            
            return config.get("namespaces") is not None
        except Exception:
            return False

    def start_namespaces(self, file_cfg: Optional[str] = None) -> bool:
        """
        Creates and configures network namespaces based on the provided configuration file.

        Args:
            file_cfg (Optional[str]): Path to the YAML configuration file.

        Returns:
            bool: True if the process finished without fatal errors, False otherwise.
        """
        if not self.load_namespaces(file_cfg):
            return False
        
        filepath_cfg: Path = Path(file_cfg)
        if not filepath_cfg.is_absolute():
            filepath_cfg = self.config_dir / file_cfg

        with open(filepath_cfg, 'r') as f:
            config: Dict = yaml.safe_load(f)
        
        namespaces_cfg = config.get("namespaces", {})
        
        self.config_pps_io(namespaces_cfg)

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
            except subprocess.CalledProcessError:
                continue
        
        return True

    def stop_namespaces(self) -> bool:
        """
        Deletes all existing network namespaces from the system.

        Returns:
            bool: True if all namespaces were successfully deleted, False otherwise.
        """
        try:
            result = subprocess.run(["ip", "netns", "list"], capture_output=True, text=True)
            namespaces: List[str] = [
                line.split()[0] for line in result.stdout.strip().splitlines() if line
            ]

            for ns in namespaces:
                subprocess.run(["ip", "netns", "delete", ns], check=True)

            return True

        except subprocess.CalledProcessError:
            return False

    def config_pps_io(self, namespaces_cfg: Dict[str, Any]) -> bool:
        """
        Configures PPS (Pulse Per Second) I/O for specific hardware types in the namespaces.

        Args:
            namespaces_cfg (Dict[str, Any]): Dictionary containing namespace configurations.

        Returns:
            bool: True if the configuration was successful, False otherwise.
        """
        if not namespaces_cfg:
            return False

        try:
            for ns_key, ns_cfg in namespaces_cfg.items():
                hw_type: Optional[str] = ns_cfg.get("hardware")
                if hw_type == "OCP-TAP_TimeStick":
                    continue
                elif hw_type == "Intel710":
                    pps_mode = ns_cfg.get("pps_mode")
                    pps_interface = ns_cfg.get("interface")
                    if not (pps_mode and pps_interface): continue                    
                    script_path = self.scripts_dir / f"config_pps_{hw_type}.sh"
                    subprocess.run(["chmod", "a+x", str(script_path)], check=True)
                    subprocess.run([str(script_path), ns_key, pps_interface, pps_mode], check=True)
                elif hw_type == "Intel810":
                    pps_sma = ns_cfg.get("pps_sma")
                    pps_mode = ns_cfg.get("pps_mode")
                    pps_interface = ns_cfg.get("pps_interface")
                    if not (pps_sma and pps_mode and pps_interface): continue
                    script_path = self.scripts_dir / f"config_pps_{hw_type}.sh"
                    subprocess.run(["chmod", "a+x", str(script_path)], check=True)
                    subprocess.run([str(script_path), pps_interface, str(pps_sma), pps_mode], check=True)
            return True
        except subprocess.CalledProcessError:
            return False