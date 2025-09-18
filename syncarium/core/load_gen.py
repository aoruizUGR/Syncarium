#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# load_gen.py

**Project**: Syncarium – Intelligent Timing Platform Toolkit  
**Description**: Load Generator configurations for TUI  
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada  
**Created**: 2025-05-28  
**Version**: 1.1.0  
**License**: GPLv3
"""


# ─────────────────────────────────────────────────────────────────────────────
# Standard Library Imports
import os
import time
import subprocess
import yaml
import time
import datetime
from pathlib import Path
from typing import Optional, Callable, Dict

# ─────────────────────────────────────────────────────────────────────────────
# Third-Party Imports
from rich.prompt import Confirm

# ─────────────────────────────────────────────────────────────────────────────
# Local Application Imports
import syncarium.utils as utils
import syncarium.options.global_vars as global_vars

# ─────────────────────────────────────────────────────────────
#  🚦 LoadGen Class
# ─────────────────────────────────────────────────────────────
class LoadGen:
    """
    Manages load generator configurations and scripts within the Syncarium environment.

    ### Attributes
    - **vt** (`utils.ViewTools`): Utility tools for rendering views in the console.
    - **load_dir** (`Path`): Path to the directory containing load configuration files.
    - **dpdk_driver_dir** (`Path`): Path to the DPDK driver directory.
    - **scripts_dir** (`Path`): Path to the directory containing shell scripts.
    - **loadgen_name** (`Optional[str]`): Name of the selected load generator.
    - **loadgen_ver** (`Optional[str]`): Version of the selected load generator.
    - **loadgen_dir** (`Optional[Path]`): Path to the load generator's server working directory.
    - **loadgen_server_dir** (`Optional[Path]`): Path to the load generator's server working directory.
    - **loadgen_client_dir** (`Optional[Path]`): Path to the STL client directory.
    - **stl_filename** (`Optional[str]`): Name of the STL script file.
    - **stl_args** (`Optional[str]`): Arguments passed to the STL script.
    - **stl_process** (`Optional[object]`): Process object for the STL execution.
    - **stl_start_time** (`Optional[float]`): Timestamp when the STL process started.
    - **stl_duration** (`Optional[float]`): Duration of the STL process.
    - **stl_state** (`Optional[str]`): Current state of the STL process.
    - **stl_env** (`Optional[Dict]`): Environment variables for the STL process.
    """
    

# ─────────────────────────────────────────────────────────────────────────────
# 🚧 Function: constructor
# ─────────────────────────────────────────────────────────────────────────────
    def __init__(self, vt: utils.ViewTools) -> None:
        """
        Initializes a new instance of LoadGen.

        ### Args
        - **vt** (`utils.ViewTools`): Utility tools for rendering views in the console.
        """

        self.vt: utils.ViewTools = vt

        # Define paths for configuration and scripts
        self.load_dir: Path = global_vars.LOAD_DIR
        self.dpdk_dir: Path = global_vars.DPDK_DIR
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
        self.stl_args: Optional[str] = None
        self.stl_process: Optional[object] = None
        self.stl_start_time: Optional[float] = None
        self.stl_duration: Optional[float] = None
        self.stl_state: Optional[str] = None
        self.stl_env: Optional[Dict] = None


# ─────────────────────────────────────────────────────────────────────────────
# 🚀 Function: main_menu
# ─────────────────────────────────────────────────────────────────────────────
    def main_menu(self) -> None:
        """
        Displays and manages the interactive load generator management menu.

        Continuously renders a terminal-based menu using `ViewTools`, allowing the user to manage
        TRex-based load generation tasks such as loading drivers, starting/stopping servers,
        launching STL scripts, and switching load generators. The loop runs until the user selects
        **"❌ Exit"** or interrupts with **Ctrl+C**.

        ### Menu Options (for TRex)
        - 📦 Load DPDK Driver → `load_dpdk_driver`
        - 🖥️ Start TRex Server → `start_trex_server`
        - 🛑 Stop TRex Server → `stop_trex_server`
        - 🖼️ Start TRex TUI → `start_trex_tui`
        - 🚀 Start STL Program → `start_stl_program`
        - 🛑 Stop STL Program → `stop_stl_program`
        - 🚦 Select another Traffic Generator → `select_load_gen`
        - 🔄 Refresh view → does nothing
        - ❌ Exit → exits the menu

        ### Notes
        - Only TRex-based load generators are currently supported.
        - Graceful exit is handled via **Ctrl+C**.
        """

        try:
            # Ensure a load generator is selected
            if not self.loadgen_name:
                self.select_load_gen()

            while True:
                # Display software title and main menu header
                self.vt.console_software_title(delay=0)
                self.vt.console_message("main_title", "LoadGen  Menu", "🚦")

                # Handle TRex-specific menu
                if self.loadgen_name.startswith("trex_"):
                    self.vt.console_message("main_title", f"TRex v{self.loadgen_ver} Management Menu", "🦖")

                    # Show DPDK-bound devices
                    self.vt.table_dpdk_bound_devices(self.dpdk_dir)

                    # Show TRex server process info
                    self.vt.table_loadgen()

                    # Show current STL process status
                    self.vt.table_stl_program(
                        self.stl_process,
                        self.stl_filename,
                        self.stl_args,
                        self.stl_start_time,
                        self.stl_duration,
                        self.stl_state
                    )

                    # Display interactive menu
                    choice: str = self.vt.console_select_menu(
                        choices=[
                            {"name": "📦 Load DPDK Driver", "value": "load_dpdk_driver"},
                            {"name": "🖥️ Start TRex Server", "value": "start_trex_server"},
                            {"name": "🛑 Stop TRex Server", "value": "stop_trex_server"},
                            {"name": "🖼️ Start TRex TUI", "value": "start_trex_tui"},
                            {"name": "🚀 Start STL Program", "value": "start_stl_program"},
                            {"name": "🛑 Stop STL Program", "value": "stop_stl_program"},
                            {"name": "🚦 Select another Traffic Generator", "value": "select_load_gen"},
                            {"name": "🔄 Refresh view", "value": "refresh_view"},
                            {"name": "❌ Exit", "value": "exit"},
                        ],
                        indent=1
                    )

                    # Map menu choices to methods
                    submenu: Dict[str, Callable[[], None]] = {
                        "load_dpdk_driver":   self.load_dpdk_driver,
                        "start_trex_server":  self.start_trex_server,
                        "stop_trex_server":   self.stop_trex_server,
                        "start_trex_tui":     self.start_trex_tui,
                        "start_stl_program":  self.start_stl_program,
                        "stop_stl_program":   self.stop_stl_program,
                        "select_load_gen":    self.select_load_gen,
                    }

                    # Handle user selection
                    if choice == "exit":
                        break
                    elif choice != "refresh_view":
                        submenu.get(choice, lambda: None)()
                        input("\n🔙 Press ⏎ to return to the menu...")

                else:
                    # Unsupported load generator
                    self.vt.console_message("exit", "Others Traffic Generators not supported yet.", indent=1)
                    return

        except KeyboardInterrupt:
            # Graceful exit on Ctrl+C
            self.vt.console_message("exit", "Exiting...")


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: load_dpdk_driver
# ─────────────────────────────────────────────────────────────────────────────
    def load_dpdk_driver(self, file_cfg: Optional[str] = None) -> None:
        """
        Loads the specified DPDK driver and binds network ports using TRex's NIC binding script.

        If no configuration file is provided, the user is prompted to select one from the available YAML files.
        The selected file must contain the driver name, number of ports, and PCI addresses for each port.
        The function uses `modprobe` to load the driver and executes `dpdk_nic_bind.py` to bind the ports.

        ### Args
        - **file_cfg** (`Optional[str]`): Name of the YAML configuration file to use. If `None`, prompts the user to select one.

        ### YAML Configuration Requirements
        - `dpdk_driver`: Name of the DPDK driver (e.g., `igb_uio`, `vfio-pci`)
        - `n_ports`: Number of ports to bind
        - `pci_bus_port{i}`: PCI address for each port, where `i` is the port index
        """
        
        # Display section title
        self.vt.console_message("title", "DPDK Driver Setup for TRex", "📦")

        if file_cfg:
            # Use provided configuration file
            filepath_cfg: Path = file_cfg
        else:
            # List available YAML configuration files
            files: list[str] = [
                f.name for f in self.dpdk_profile_dir.iterdir()
                if f.is_file() and f.suffix == ".yaml"
            ]

            # Exit if no configuration files are found
            if not files:
                self.vt.console_message("error", f"No configuration files found in '{self.dpdk_profile_dir}'", indent=1)
                return

            try:
                # Prompt user to select a configuration file
                choices = [
                    {"name": f"{i}. 📄 {name}", "value": name}
                    for i, name in enumerate(sorted(files), 1)
                ]
                selected: str = self.vt.console_select_menu(
                    choices=choices,
                    message="Available Configuration Files:",
                    indent=1
                )
                filepath_cfg: Path = self.dpdk_profile_dir / selected
            except KeyboardInterrupt:
                # Handle user cancellation
                self.vt.console_message("caution", "Operation cancelled by user.")
                return

        # Read and parse YAML configuration
        try:
            with open(filepath_cfg, 'r') as f:
                config: Dict = yaml.safe_load(f)
        except Exception as e:
            self.vt.console_message("error", f"Error reading YAML file: {e}", indent=1)
            return
        # Extract required fields
        dpdk_driver: Optional[str] = config.get("dpdk_driver")
        n_ports: Optional[int] = config.get("n_ports")

        # Validate configuration
        if not dpdk_driver or not isinstance(n_ports, int):
            self.vt.console_message("error", "YAML must contain valid 'dpdk_driver' and 'n_ports'.", indent=1)
            return

        # Collect PCI port addresses
        ports: list[str] = []
        for i in range(n_ports):
            port_key = f"pci_bus_port{i}"
            port = config.get(port_key)
            if not port:
                self.vt.console_message("error", f"Missing PCI address for '{port_key}'.", indent=2)
                return
            ports.append(port)

        # Load the DPDK driver using modprobe
        cmd = ["sudo", "modprobe", dpdk_driver]
        self.vt.console_message("info", f"Running: {' '.join(cmd)}", indent=1)
        subprocess.run(cmd)

        # Bind the ports using TRex's dpdk_nic_bind.py script
        nic_bind_script: Path = self.dpdk_dir / "dpdk-devbind.py"
        cmd = ["sudo", "python3", str(nic_bind_script), "-b", dpdk_driver] + ports
        self.vt.console_message("info", f"Running: {' '.join(cmd)}", indent=1)

        try:
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.vt.console_message(
                "success",
                f"DPDK driver '{dpdk_driver}' successfully loaded on {n_ports} port(s).",
                indent=2
            )
        except subprocess.CalledProcessError as e:
            self.vt.console_message("error", f"Error executing TRex script: {e}", indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: start_trex_server
# ─────────────────────────────────────────────────────────────────────────────
    def start_trex_server(self, sleep_seconds: int = 10, file_cfg: Optional[str] = None) -> None:
        """
        Starts the TRex server using the specified configuration file.

        If a TRex server is already running, prompts the user to stop it before launching a new one.
        Prepares the system environment (e.g., hugepages), selects a configuration file (if not provided),
        and launches the TRex server in software mode.

        ### Args
        - **sleep_seconds** (`int`): Seconds to wait after launching the server to allow initialization. Defaults to `10`.
        - **file_cfg** (`Optional[str]`): Name of the TRex YAML configuration file. If `None`, prompts the user to select one.

        ### Notes
        - Uses `config_hugepages.sh` to prepare hugepages before launching.
        - Launches TRex with `--software` and `--no-scapy-server` flags.
        """
        
        # Display section title
        self.vt.console_message("title", "Starting TRex Server", "🖥️")

        # Check if a TRex server is already running
        result = subprocess.run(["pgrep", "-a", "_t-rex-64"], capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()
        if lines:
            self.vt.console_message("info", "There is a TRex Server already running.", indent=1)
            confirm: bool = Confirm.ask("⚠️ Are you sure you want to stop the actual TRex Server?", default=True)
            if confirm:
                self.stop_trex_server()
            else:
                self.vt.console_message("success", "Not starting new TRex Server process.", indent=1)
                return

        # Select configuration file
        if file_cfg is None:
            files: list[str] = [
                f.name for f in self.loadgen_server_dir.iterdir()
                if f.is_file() and f.name.startswith("trex_") and f.suffix == ".yaml"
            ]

            if not files:
                self.vt.console_message("error", "No available config files found in the directory.", indent=1)
                return

            try:
                choices = [
                    {"name": f"{i}. 📄 {name}", "value": name}
                    for i, name in enumerate(sorted(files), 1)
                ]
                selected: str = self.vt.console_select_menu(
                    choices=choices,
                    message="Available Configuration Files:",
                    indent=2
                )
                filepath_cfg: Path = self.loadgen_server_dir / selected
            except KeyboardInterrupt:
                self.vt.console_message("caution", "Operation cancelled by user.")
                return
        else:
            filepath_cfg: Path = self.loadgen_server_dir / file_cfg

        absolute_filepath_cfg: Path = filepath_cfg.resolve()

        try:
            # Prepare system environment (e.g., hugepages)
            script_path: Path = self.scripts_dir / "config_hugepages.sh"
            subprocess.run(["sudo", "chmod", "a+x", script_path], check=True)
            subprocess.run(["sudo", script_path], check=True)

            # Build the TRex launch command
            command: list[str] = [
                "./t-rex-64", "-i", "--software", "--no-scapy-server", "--cfg", str(absolute_filepath_cfg)
            ]

            # Launch the TRex server process
            process = subprocess.Popen(
                ["sudo"] + command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                cwd=self.loadgen_server_dir,
                preexec_fn=os.setpgrp  # Detach from parent process group
            )

            # Wait for the server to initialize
            time.sleep(sleep_seconds)

            # Display process metadata
            start_time: str = datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Y")
            cmd_str: str = " ".join(command[3:])  # Skip 'sudo' and './t-rex-64'

            self.vt.console_message("success", "TRex Server launched successfully.", indent=1)
            self.vt.console_message("info", f"PID: {process.pid} | Started at: {start_time}", indent=2)
            self.vt.console_message("info", f"Command: {cmd_str}", indent=2)

        except Exception as e:
            # Handle any error during launch
            self.vt.console_message("error", f"Error launching TRex Server: {e}", indent=1)


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: stop_trex_server
# ─────────────────────────────────────────────────────────────────────────────
    def stop_trex_server(self) -> None:
        """
        Stops any running TRex server processes.

        Checks for active TRex server instances using `pgrep`, prompts the user for confirmation,
        and terminates each detected process using `kill -9`. Displays relevant messages for success,
        cancellation, or errors during termination.
        """


        # Display section title
        self.vt.console_message("title", "Stopping TRex Server", "🛑")

        # Check for running TRex server processes
        result = subprocess.run(["pgrep", "-a", "_t-rex-64"], capture_output=True, text=True)
        lines: list[str] = result.stdout.strip().splitlines()

        # If no processes found, notify and exit
        if not lines:
            self.vt.console_message("info", "No active TRex Server process found.", indent=1)
            return

        # Ask user for confirmation before terminating the process
        confirm: bool = Confirm.ask("⚠️ Are you sure you want to stop the TRex Server process?", default=False)
        if not confirm:
            self.vt.console_message("info", "Stop operation cancelled.", indent=1)
            return
        try:
            # Iterate over each running process and terminate it
            for line in lines:
                pid, *cmd = line.split()
                self.vt.console_message("clean", f"Killing TRex Server process with PID {pid} → {' '.join(cmd)}", indent=1)
                subprocess.run(["sudo", "kill", "-9", pid], check=True)

            self.vt.console_message("success", "TRex Server process has been terminated.", indent=1)

        except subprocess.CalledProcessError as e:
            # Handle errors during process termination
            self.vt.console_message("error", f"Error stopping TRex Server process: {e}", indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: start_trex_tui
# ─────────────────────────────────────────────────────────────────────────────
    def start_trex_tui(self) -> None:
        """
        Launches the TRex Text User Interface (TUI) console.

        Verifies that a TRex server process is running before attempting to launch the TUI.
        Executes the `trex-console` command within the TRex server directory using the configured environment.

        ### Notes
        - If no TRex server is running, the TUI will not be launched.
        - Uses the environment defined in `stl_env` to execute the console.
        """

        # Print header to indicate the TUI launch process
        self.vt.console_message("title", "Launch TUI Server", "🖼️")

        # Check if there is a running TRex server process
        result = subprocess.run(["pgrep", "-a", "_t-rex-64"], capture_output=True, text=True)
        lines: list[str] = result.stdout.strip().splitlines()
        if not lines:
            self.vt.console_message("info", "No active TRex Server process found.", indent=1)
            return

        try:
            # Define the command to launch the TRex TUI
            command: list[str] = ["./trex-console"]

            # Clear the console and reprint the header for a clean interface
            self.vt.console_message("title", "Launch TUI Server", "🖼️")

            # Run the command in the TRex server directory with the appropriate environment
            subprocess.run(
                command,
                cwd=self.loadgen_server_dir,
                check=True,
                env=self.stl_env
            )

        except subprocess.CalledProcessError as e:
            # Handle errors if the subprocess fails
            self.vt.console_message("error", f"TRex TUI exited with error: {e}", indent=1)

        except Exception as e:
            # Handle any other unexpected exceptions
            self.vt.console_message("error", f"Error launching TRex TUI: {e}", indent=1)


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: start_stl_program
# ─────────────────────────────────────────────────────────────────────────────
    def start_stl_program(
        self,
        file_cfg: Optional[Path] = None,
        labt_duration: Optional[int] = None,
        labt_output: Optional[str] = None,
        logger=None,
        extra_indent: int = 0
    ) -> None:
        """
        Launches an STL load generation program based on a YAML configuration file.

        This method ensures no other STL process is currently running, selects or loads
        a configuration file, parses the STL script and its arguments, and starts the
        process with the appropriate environment variables.

        ### Args:
        - **file_cfg** (`Optional[str]`): Name of the YAML configuration file. If `None`, the user is prompted to select one.
        - **labt_duration** (`Optional[int]`): Optional override for the duration of the STL program.
        - **labt_output** (`Optional[str]`): Optional output path or identifier for the STL program.
        - **logger**: Logger instance used for logging messages. Defaults to `None`.
        - **extra_indent** (`int`): Additional indentation level for console messages. Defaults to `0`.
        """

        self.vt.console_message("title", "Start STL Program", "🚀", indent=extra_indent, logger=logger)

        # Check if an STL process is already running
        if self.stl_process and self.stl_process.poll() is None:
            self.vt.console_message("caution", f"A STL program is already running with PID {self.stl_process.pid}.", indent=1)
            self.vt.console_message("info", "To start a STL program it is necessary to manually stop actual load from menu.", indent=1)
            return

        # Select configuration file
        if file_cfg:
            filepath_cfg: Path = file_cfg
        
        else:            
            files: list[str] = [
                str(f.relative_to(self.load_dir))
                for f in self.load_dir.rglob("*.yaml")
                if f.is_file()
            ]


            if not files:
                self.vt.console_message("error", "No available STL programs found in the directory.", indent=1)
                return

            try:
                choices = [
                    {"name": f"{i}. 📄 {name}", "value": name}
                    for i, name in enumerate(sorted(files), 1)
                ]
                selected: str = self.vt.console_select_menu(
                    choices=choices,
                    message="Available STL Configuration Files:",
                    indent=1
                )
                filepath_cfg: Path = self.load_dir / selected
            except KeyboardInterrupt:
                self.vt.console_message("caution", "Operation cancelled by user.")
                return


        # Read configuration file
        self.vt.console_message("info", "Reading configuration file...", indent=1 + extra_indent, logger=logger)
        with open(filepath_cfg, 'r') as f:
            stl: Dict = yaml.safe_load(f)

        self.stl_filename: Optional[str] = stl.get("loadgen_stl_program")

        # Build STL arguments
        if labt_duration and labt_output:
            self.stl_duration = labt_duration
            self.stl_args = [str(self.stl_duration)] + [
                str(value) for value in stl.get("loadgen_stl_args", {}).values()
            ] + [str(labt_output)]
        else:
            self.stl_duration = stl.get("loadgen_stl_args", {}).get("duration")
            self.stl_args = [
                str(value) for value in stl.get("loadgen_stl_args", {}).values()
            ]

        if self.stl_duration is None:
            self.vt.console_message("error", f"STL Duration not found in {filepath_cfg}.", indent=1 + extra_indent, logger=logger)
            return

        # Check if STL script exists
        stl_filepath: Path = self.loadgen_client_dir / self.stl_filename
        if not stl_filepath.exists():
            self.vt.console_message("error", f"STL program not found in {stl_filepath}.", indent=1 + extra_indent, logger=logger)
            return


        # Launch STL program
        self.stl_start_time = time.time()
        start_time_hr: str = datetime.datetime.fromtimestamp(self.stl_start_time).strftime("%Y-%m-%d %H:%M:%S")

        cmd: list[str] = ["python", str(stl_filepath)] + self.stl_args
        self.vt.console_message("info", f"running {cmd}", indent=1 + extra_indent, logger=logger)

        self.stl_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            env=self.stl_env,
            start_new_session=True
        )

        # Display process metadata
        self.vt.console_message("info", f"PID: {self.stl_process.pid} | Started at: {start_time_hr}", indent=2 + extra_indent, logger=logger)
        self.vt.console_message("info", f"Duration: {self.stl_duration} seconds", indent=2 + extra_indent, logger=logger)
        self.vt.console_message("info", f"Args used: {self.stl_args}", indent=2 + extra_indent, logger=logger)
        self.stl_state = "Launched"
           

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: stop_stl_program
# ─────────────────────────────────────────────────────────────────────────────
    def stop_stl_program(
        self,
        logger=None,
        preconfirmation: Optional[bool] = False,
        extra_indent: int = 0
    ) -> None:
        """
        Stops the currently running STL load generation program.

        Verifies if an STL process is active, optionally prompts the user for confirmation,
        terminates the process, and updates the internal state accordingly.

        ### Args:
        - **logger**: Logger instance used for logging messages. Defaults to `None`.
        - **preconfirmation** (`Optional[bool]`): If `True`, skips the confirmation prompt. Defaults to_indent** (`int`): Additional indentation level for console messages. Defaults to `0`.
        """
        
        self.vt.console_message("title", "Stopping STL program", "🛑", indent=extra_indent, logger=logger)

        # Check if an STL process is running
        if self.stl_state != "Launched":
            self.vt.console_message("info", "No STL Program running.", indent=1 + extra_indent, logger=logger)
            return

        # Ask user for confirmation before terminating the process
        if not preconfirmation:
            confirm: bool = Confirm.ask("⚠️ Are you sure you want to forcefully stop the STL program?", default=True)
            if not confirm:
                self.vt.console_message("info", "Stop operation cancelled.", indent=1 + extra_indent, logger=logger)
                return

        try:
            # Terminate the STL process
            self.vt.console_message("clean", f"Killing STL process with PID {self.stl_process.pid}", indent=1 + extra_indent, logger=logger)
            self.stl_process.terminate()
            #os.killpg(self.stl_process.pid, signal.SIGTERM)

            self.vt.console_message("success", "STL process has been terminated.", indent=2 + extra_indent, logger=logger)

        except subprocess.CalledProcessError as e:
            # Handle errors during process termination
            self.vt.console_message("error", f"Error stopping STL process: {e}", indent=2 + extra_indent, logger=logger)

        # Update internal state
        self.stl_state = "Forced Stop"


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: select_load_gen
# ─────────────────────────────────────────────────────────────────────────────
    def select_load_gen(self) -> Optional[bool]:
        """
        Prompts the user to select a load generator and sets up its environment.

        Lists available load generator folders, allows the user to choose one,
        and configures internal paths and environment variables accordingly.
        If the selected generator version differs from the current one, stops any running TRex server.

        ### Returns:
        - `Optional[bool]`: `True` if a load generator was successfully selected, `False` otherwise.
        """
        
        # Define the base directory where load generator folders are located
        self.loadgen_dir: Path = global_vars.TGEN_DIR

        # List all folder names in the loadgen_dir directory
        load_generators: list[str] = [
            f.name for f in self.loadgen_dir.iterdir()
            if f.is_dir()
        ]

        # If no load generators are found, notify the user and exit
        if not load_generators:
            self.vt.console_message("error", f"No Traffic Generators found in '{self.loadgen_dir}'.", indent=1)
            return False

        try:
            # Prompt the user to select a load generator
            choices: list[Dict[str, str]] = [
                {"name": f"🚦 {name}", "value": name}
                for name in load_generators
            ]
            selected: str = self.vt.console_select_menu(
                choices=choices,
                message="Available Traffic Generator Software:",
                indent=1
            )

            # Store the selected load generator and its path
            self.loadgen_name = selected
            self.loadgen_server_dir = self.loadgen_dir / self.loadgen_name / "server"
            self.loadgen_client_dir = self.loadgen_dir / self.loadgen_name / "client"

            # Build PYTHONPATH for STL client scripts
            interactive_path: Path = self.loadgen_server_dir / "automation/trex_control_plane/interactive"
            self.stl_env = os.environ.copy()
            self.stl_env["PYTHONPATH"] = f"{interactive_path}:{self.stl_env.get('PYTHONPATH', '')}"

            # Extract and store the version from the folder name (e.g., "trex_v3.04" → "3.04")
            version: str = self.loadgen_name.split("_v")[-1]
            if self.loadgen_ver != version:
                self.stop_trex_server()
                self.loadgen_ver = version

            # Confirm successful selection
            self.vt.console_message("success", f"Traffic Generator '{self.loadgen_name}' successfully loaded.", indent=1)

        except KeyboardInterrupt:
            # Handle user interruption gracefully
            self.vt.console_message("caution", "Operation cancelled by user.")
            return False
