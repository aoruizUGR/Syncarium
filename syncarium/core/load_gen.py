import os
import time
import subprocess
import yaml
import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

import syncarium.utils as utils
import path_config.global_vars as global_vars

class LoadGen:
    """
    Manages load generator configurations and scripts within the Syncarium environment.
    This class handles the backend logic for TRex and STL load generation.
    """

    def __init__(self) -> None:
        # Define paths for configuration and scripts
        self.load_dir: Path = global_vars.LOAD_DIR
        self.utils_dir: Path = global_vars.UTILS_DIR
        self.dpdk_profile_dir: Path = global_vars.DPDK_PROFILE_DIR
        self.scripts_dir: Path = global_vars.SCRIPTS_DIR

        # Traffic generator metadata
        self.loadgen_name: Optional[str] = None
        self.loadgen_ver: Optional[str] = None
        self.loadgen_dir: Optional[Path] = None
        self.loadgen_server_dir: Optional[Path] = None
        self.loadgen_client_dir: Optional[Path] = None

        # STL script execution details
        self.stl_filename: Optional[str] = None
        self.stl_args: Optional[List[str]] = None
        self.stl_process: Optional[Any] = None
        self.stl_start_time: Optional[float] = None
        self.stl_duration: Optional[float] = None
        self.stl_state: Optional[str] = None
        self.stl_env: Optional[Dict] = None

    def load_dpdk_driver(self, file_cfg: Optional[str] = None) -> bool:
        """
        Loads the specified DPDK driver and binds network ports.
        Returns: bool: True if successful, False otherwise.
        """
        if file_cfg:
            filepath_cfg: Path = Path(file_cfg)
        else:
            files = [f.name for f in self.dpdk_profile_dir.iterdir() if f.suffix == ".yaml"]
            if not files:
                return False
            filepath_cfg = self.dpdk_profile_dir / files[0] 

        try:
            with open(filepath_cfg, 'r') as f:
                config: Dict = yaml.safe_load(f)
        except Exception:
            return False

        dpdk_driver = config.get("dpdk_driver")
        n_ports = config.get("n_ports")

        if not dpdk_driver or not isinstance(n_ports, int):
            return False

        ports = [config.get(f"pci_bus_port{i}") for i in range(n_ports)]
        
        # Load driver
        subprocess.run(["sudo", "modprobe", dpdk_driver], check=True)

        # Bind ports
        nic_bind_script = self.utils_dir / "dpdk-devbind.py"
        cmd = ["sudo", "python3", str(nic_bind_script), "-b", dpdk_driver] + ports
        subprocess.run(cmd, check=True, capture_output=True)
        return True

    def start_trex_server(self, sleep_seconds: int = 10, file_cfg: Optional[str] = None) -> bool:
        """Starts the TRex server process."""
        # Check if running
        result = subprocess.run(["pgrep", "-a", "_t-rex-64"], capture_output=True, text=True)
        if result.stdout.strip():
            self.stop_trex_server()

        if file_cfg is None:
            files = [f.name for f in self.loadgen_server_dir.iterdir() if f.name.startswith("trex_") and f.suffix == ".yaml"]
            if not files: return False
            filepath_cfg = self.loadgen_server_dir / files[0]
        else:
            filepath_cfg = self.loadgen_server_dir / file_cfg

        script_path = self.scripts_dir / "config_hugepages.sh"
        subprocess.run(["sudo", "chmod", "a+x", str(script_path)], check=True)
        subprocess.run(["sudo", str(script_path)], check=True)

        command = ["./t-rex-64", "-i", "--software", "--no-scapy-server", "--cfg", str(filepath_cfg.resolve())]
        
        process = subprocess.Popen(
            ["sudo"] + command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            cwd=self.loadgen_server_dir,
            preexec_fn=os.setpgrp
        )

        time.sleep(sleep_seconds)
        return True

    def stop_trex_server(self) -> bool:
        """Stops all TRex server processes."""
        result = subprocess.run(["pgrep", "-a", "_t-rex-64"], capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()
        if not lines:
            return True

        for line in lines:
            pid = line.split()[0]
            subprocess.run(["sudo", "kill", "-9", pid], check=True)
        return True

    def start_trex_tui(self) -> bool:
        """Launches the TRex TUI."""
        try:
            subprocess.run(
                ["./trex-console"],
                cwd=self.loadgen_server_dir,
                check=True,
                env=self.stl_env
            )
            return True
        except Exception:
            return False

    def start_stl_program(
        self,
        file_cfg: Optional[Path] = None,
        stl_duration: Optional[int] = None,
        stl_output: Optional[str] = None,
        logger=None,
        extra_indent: int = 0
    ) -> bool:
        """Launches the STL program and updates internal state."""
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

        self.stl_filename = stl.get("loadgen_stl_program")
        
        if stl_duration and stl_output:
            self.stl_duration = stl_duration
            self.stl_args = [str(self.stl_duration)] + [str(v) for v in stl.get("loadgen_stl_args", {}).values()] + [str(stl_output)]
        else:
            self.stl_duration = stl.get("loadgen_stl_args", {}).get("duration")
            self.stl_args = [str(v) for v in stl.get("loadgen_stl_args", {}).values()]

        stl_filepath = self.loadgen_client_dir / self.stl_filename
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
        """Stops the active STL process."""
        if self.stl_state != "Launched":
            return True

        try:
            if self.stl_process:
                self.stl_process.terminate()
            self.stl_state = "Forced Stop"
            return True
        except Exception:
            return False

    def select_load_gen(self, selected_name: str) -> bool:
        """Sets up the environment for a selected generator by name."""
        self.loadgen_dir = global_vars.TGEN_DIR
        
        if not self.loadgen_dir.exists():
            return False

        # Update internal paths based on selection
        self.loadgen_name = selected_name
        self.loadgen_server_dir = self.loadgen_dir / self.loadgen_name / "server"
        self.loadgen_client_dir = self.loadgen_dir / self.loadgen_name / "client"

        # Build PYTHONPATH for STL client scripts
        interactive_path = self.loadgen_server_dir / "automation/trex_control_plane/interactive"
        self.stl_env = os.environ.copy()
        self.stl_env["PYTHONPATH"] = f"{interactive_path}:{self.stl_env.get('PYTHONPATH', '')}"

        # Extract and store the version from the folder name (e.g., "trex_v3.04" → "3.04")
        version = self.loadgen_name.split("_v")[-1]
        if self.loadgen_ver != version:
            self.stop_trex_server()
            self.loadgen_ver = version
        
        return True