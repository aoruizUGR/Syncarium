#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# plat_init.py

**Project**: Syncarium - Intelligent Timing Platform Toolkit  
**Description**: Platform Initialization for TUI  
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada  
**Created**: 2025-05-22  
**Version**: 1.2.0  
**License**: GPLv3
"""


# ─────────────────────────────────────────────────────────────────────────────
# Standard Library Imports
import subprocess
import yaml
from pathlib import Path
from typing import Callable, Optional, List, Dict

# ─────────────────────────────────────────────────────────────────────────────
# Third-Party Imports
from rich.prompt import Confirm

# ─────────────────────────────────────────────────────────────────────────────
# Local Application Imports
import syncarium.utils as utils
import syncarium.options.global_vars as global_vars

# ─────────────────────────────────────────────────────────────
# ⚙️ Platform Initialization Class
# ─────────────────────────────────────────────────────────────

class PlatInit:
    """
    Sets up the platform setup environment for 

    ### Attributes
    - **vt** (`utils.ViewTools`): Utility tools for rendering views in the console.
    - **config_dir** (`Path`): Path to the directory containing platform setup files.
    - **scripts_dir** (`Path`): Path to the directory containing shell scripts.
    - **loaded_namespaces** (`List[str]`): List of namespaces that have been loaded.
    """

# ─────────────────────────────────────────────────────────────
# 🚧 Function: constructor
# ─────────────────────────────────────────────────────────────
    def __init__(self, vt: utils.ViewTools) -> None:
        """
        Initializes a new instance of `PlatInit`.

        ### Parameters
        - **vt** (`utils.ViewTools`): Instance of utility tools for rendering views in the console.
        """

        # Store the view tools instance
        self.vt: utils.ViewTools = vt

        # Define the path to the configuration directory
        self.config_dir: Path = global_vars.NAMESPACES_DIR

        # Define the path to the scripts directory
        self.scripts_dir: Path = global_vars.SCRIPTS_DIR

        # Initialize the list of loaded namespaces
        self.loaded_namespaces: List[str] = []

# ─────────────────────────────────────────────────────────────
# 📋 Function: main_menu
# ─────────────────────────────────────────────────────────────
    def main_menu(self) -> None:
        """
        Displays and manages the interactive main menu for platform setup tasks.

        Continuously renders a terminal-based menu using InquirerPy, allowing the user to:
        - Load device drivers
        - Manage Linux namespaces
        - Configure PPS I/O

        The menu loop runs until the user selects **"Exit"** or interrupts the process with **Ctrl+C**.

        ### Menu Options:
        - 📦 Load Device Driver → `load_device_driver`
        - 🌐 Start Linux Namespaces → `start_namespaces`
        - 🛑 Stop Linux Namespaces → `stop_namespaces`
        - 📍 Configure PPS I/O → `config_pps_io`
        - 🔄 Refresh View → refreshes the display (no action)
        - ❌ Exit → exits the menu loop

        ### Notes:
        - Graceful termination is supported via **Ctrl+C**.
        """

        try:
            while True:
                # Display the software title instantly
                self.vt.console_software_title(delay=0)

                # Show the main menu header
                self.vt.console_message("main_title", "Platform Initialization Menu", "⚙️")

                # Render a table of active network namespaces
                self.vt.table_network_namespaces()

                # Prompt user with interactive menu
                choice: str = self.vt.console_select_menu(
                    choices=[
                        {"name": "📦 Load Device Driver", "value": "load_device_driver"},
                        {"name": "🌐 Start Linux Namespaces", "value": "start_namespaces"},
                        {"name": "🛑 Stop Linux Namespaces", "value": "stop_namespaces"},
                        {"name": "📍 Configure PPS I/O", "value": "config_pps_io"},
                        {"name": "🔄 Refresh view", "value": "refresh_view"},
                        {"name": "❌ Exit", "value": "exit"},
                    ],
                    indent=1
                )

                # Map menu options to corresponding methods
                submenu: Dict[str, Callable[[], None]] = {
                    "load_device_driver": self.load_device_driver,
                    "start_namespaces": self.start_namespaces,
                    "stop_namespaces": self.stop_namespaces,
                    "config_pps_io": self.config_pps_io,
                }

                # Exit loop if user chooses to exit
                if choice == "exit":
                    break

                # Refresh view does nothing; other options invoke their methods
                elif choice != "refresh_view":
                    action = submenu.get(choice)
                    if action:
                        action()
                        input("\n🔙 Press ⏎ to return to the menu...")

        except KeyboardInterrupt:
            # Handle Ctrl+C interruption gracefully
            self.vt.console_message("exit", "Exiting...")


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: load_device_driver
# ─────────────────────────────────────────────────────────────────────────────
    def load_device_driver(self) -> None:
        """
        Loads a device driver from the available shell scripts in the scripts directory.

        Searches for scripts matching the pattern `devdriver_*.sh` within `scripts_dir`.
        If any are found, presents them in an interactive menu using InquirerPy for selection.
        The selected script is made executable and then executed.

        Displays appropriate messages for:
        - Missing scripts
        - User cancellation
        - Execution success or failure

        ### Raises:
        - **subprocess.CalledProcessError**: If the script execution fails.
        """

        # Show section title
        self.vt.console_message("title", "Loading Drivers", "📦")

        # Find all matching driver scripts
        drivers: list[str] = [
            f.stem[len("devdriver_"):]
            for f in Path(self.scripts_dir).glob("devdriver_*.sh")
        ]

        # If no drivers found, notify and exit
        if not drivers:
            self.vt.console_message("error", "No available drivers found in the directory.", indent=1)
            return

        try:
            # Build menu choices from driver names
            choices: List[Dict[str, str]] = [
                {"name": f"{i}. 📄 {name}", "value": name}
                for i, name in enumerate(sorted(drivers), 1)
            ]

            # Prompt user to select a driver
            selected: str = self.vt.console_select_menu(
                choices=choices,
                message="Available Drivers Installations:",
                indent=1
            )

            # Construct full path to the selected script
            script_path: Path = Path(self.scripts_dir) / f"devdriver_{selected}.sh"

        except KeyboardInterrupt:
            # Handle cancellation gracefully
            self.vt.console_message("caution", "Operation cancelled by user.")
            return

        # Make the script executable
        subprocess.run(["chmod", "a+x", script_path], check=True)

        # Run the script
        self.vt.console_message("info", f"Running: {script_path}", indent=1)
        try:
            subprocess.run([script_path], check=True)
            self.vt.console_message("success", f"Driver '{selected}' loaded successfully.", indent=2)
        except subprocess.CalledProcessError as e:
            # Handle execution errors
            self.vt.console_message("error", f"Error executing the script: {e}.", indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: load_namespaces
# ─────────────────────────────────────────────────────────────────────────────
    def load_namespaces(self, file_cfg: Optional[Path] = None) -> bool:
        """
        Loads a network namespace configuration from a YAML file.

        If `file_cfg` is provided, it is used directly. Otherwise, the method searches
        for YAML files in `config_dir` matching the pattern `*.yaml`, and prompts the user
        to select one interactively. The selected file is parsed and its contents are stored
        in `loaded_namespaces`.

        The configuration must contain a top-level key `"namespaces"` with a dictionary
        of namespace definitions. If no valid configuration is found, the operation is
        aborted gracefully.

        ### Parameters:
        - **file_cfg** (`Optional[str]`): Optional filename of the YAML configuration to load.

        ### Returns:
        - **bool**: `True` if the configuration was successfully loaded and validated; `False` otherwise.
        """

        # Show section title
        self.vt.console_message("title", "Loading Linux Namespaces", "🌐")

        if file_cfg:
            # Use provided filename directly
            filepath_cfg: Path = file_cfg
        
        else:
            # Search for YAML configuration files
            files: list[str] = [
                str(f.relative_to(self.config_dir))
                for f in self.config_dir.rglob("*.yaml")
                if f.is_file()
            ]

            # Notify if no files are found
            if not files:
                self.vt.console_message(
                    "error",
                    message=f"No configuration files found in '{self.config_dir}'.",
                    indent=1
                )
                return False

            try:
                # Build menu choices from file names
                choices: list[Dict[str, str]] = [
                    {"name": f"{i}. 📄 {name}", "value": name}
                    for i, name in enumerate(sorted(files), 1)
                ]

                # Prompt user to select a file
                selected: str = self.vt.console_select_menu(
                    choices=choices,
                    message="Available Configuration Files:",
                    indent=1
                )

                # Construct full path to selected file
                filepath_cfg: Path = self.config_dir / selected

            except KeyboardInterrupt:
                # Handle cancellation gracefully
                self.vt.console_message("caution", "Operation cancelled by user.")
                return False

        try:
            # Read and parse the YAML configuration
            self.vt.console_message("info", "Reading configuration file...", indent=1)
            with open(filepath_cfg, 'r') as f:
                config: Dict = yaml.safe_load(f)

            # Extract namespaces from config
            self.loaded_namespaces = config.get("namespaces", {})

            # Validate that namespaces exist
            if not self.loaded_namespaces:
                self.vt.console_message("error", "Configuration file does not contain namespaces.", indent=2)
                return False

            self.vt.console_message("success", "Configuration file loaded successfully.", indent=2)
            return True

        except Exception as e:
            # Handle file or parsing errors
            self.vt.console_message("error", f"Error reading YAML file: {e}", indent=2)
            return False


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: start_namespaces
# ─────────────────────────────────────────────────────────────────────────────
    def start_namespaces(self, file_cfg: Optional[str] = None) -> None:
        """
        Starts Linux network namespaces based on a selected YAML configuration file.

        This method performs the following steps:
        - Checks if any namespaces are already running and optionally stops them.
        - Loads a namespace configuration from a YAML file.
        - Iterates through the configuration and applies each namespace setup using system commands.

        Each namespace must define:
        - A name
        - An interface
        - An IP/mask

        Optionally, a gateway can be defined. IPv6 is disabled on each configured interface.

        If any required fields are missing, the corresponding namespace setup is skipped.

        ### Parameters:
        - **file_cfg** (`Optional[str]`): Optional filename of the YAML configuration to load.  
        If not provided, the user will be prompted to select one.
        """

        # Check if any namespaces are already running
        result = subprocess.run(["ip", "netns", "list"], capture_output=True, text=True)
        namespaces = result.stdout.strip().split('\n')

        if namespaces and namespaces[0]:
            self.vt.console_message("caution", "There are Linux Namespaces already running.")
            confirm = Confirm.ask("⚠️ Are you sure you want to stop the actual Linux namespaces?", default=True)
            if confirm:
                self.stop_namespaces(ask_confirm=False)
            else:
                self.vt.console_message("success", "Not starting new Linux Namespaces.", indent=1)
                return

        # Load namespace configuration from YAML
        if not self.load_namespaces(file_cfg):
            self.vt.console_message("error", "Aborting operation due to failed configuration loading.", indent=1)
            return
        
        self.config_pps_io()

        self.vt.console_message("title", "Start Linux Namespaces", "🌐")

        # Iterate through each namespace entry
        for key, config in self.loaded_namespaces.items():
            ns = key
            ip_mask = config.get("IP/mask")
            gw = config.get("gateway")
            iface = config.get("interface")

            # Skip if any required field is missing
            if not all([ns, ip_mask, iface]):
                self.vt.console_message("error", f"Missing data for namespace '{key}'. Check the YAML file.", indent=1)
                continue

            self.vt.console_message("info", f"Configuring namespace '{ns}'...", indent=1)
            try:
                # Create the network namespace
                subprocess.run(f"ip netns add {ns}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Move the physical interface into the namespace
                subprocess.run(f"ip link set {iface} netns {ns}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Assign IP address to the interface inside the namespace
                subprocess.run(f"ip netns exec {ns} ip addr add {ip_mask} dev {iface}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Bring the interface up inside the namespace
                subprocess.run(f"ip netns exec {ns} ip link set dev {iface} up", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Set the default gateway inside the namespace
                if gw:
                    subprocess.run(f"ip netns exec {ns} ip route add default via {gw} dev {iface}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Disable IPv6 on the interface
                subprocess.run(f"ip netns exec {ns} sysctl -w net.ipv6.conf.{iface}.disable_ipv6=1", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.vt.console_message("success", f"Namespace '{ns}' configured successfully.", indent=2)
            
            except subprocess.CalledProcessError as e:
                self.vt.console_message("error", f"Error creating namespace '{ns}': {e}", indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: stop_namespaces
# ─────────────────────────────────────────────────────────────────────────────
    def stop_namespaces(self, ask_confirm: bool = True) -> None:
        """
        Stops all currently running Linux network namespaces.

        This method performs the following steps:
        - Lists active namespaces using `ip netns list`.
        - Optionally prompts the user for confirmation before deletion.
        - Iterates through each namespace and deletes it using system commands.
        - Displays progress, success, and error messages accordingly.

        ### Parameters:
        - **ask_confirm** (`bool`): Whether to prompt the user for confirmation before stopping namespaces.  
        Defaults to `True`.
        """
        
        # Show section title
        self.vt.console_message("title", "Stopping Linux Namespaces", "🛑")

        try:
            # List all existing namespaces
            result = subprocess.run(["ip", "netns", "list"], capture_output=True, text=True)
            namespaces: List[str] = [
                line.split()[0] for line in result.stdout.strip().splitlines() if line
            ]

            # If no namespaces found, notify and exit
            if not namespaces:
                self.vt.console_message("info", "No namespaces to delete.", indent=1)
                return

            # Ask for confirmation before deletion
            if ask_confirm:
                confirm: bool = Confirm.ask("⚠️ Are you sure you want to delete namespaces?", default=True)
                if not confirm:
                    self.vt.console_message("info", "Stop operation cancelled.", indent=1)
                    return

            # Delete each namespace
            for ns in namespaces:
                self.vt.console_message("clean", f"Stopping: {ns}", indent=1)
                subprocess.run(["ip", "netns", "delete", ns], check=True)

            # Confirm completion
            self.vt.console_message("success", "All namespaces have been deleted.", indent=1)

        except subprocess.CalledProcessError as e:
            # Handle deletion errors
            self.vt.console_message("error", f"Error stopping namespaces: {e}", indent=2)

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: config_pps_io
# ─────────────────────────────────────────────────────────────────────────────
    def config_pps_io(self) -> None:
        """
        Configures PPS (Pulse Per Second) I/O for ALL loaded namespaces.

        Instead of asking the user to choose one namespace, this version iterates
        over each namespace loaded in self.loaded_namespaces and applies the PPS
        configuration according to its hardware type.

        Supported hardware:
        - OCP-TAP TimeStick  (no configuration needed)
        - Intel 710          (uses config_pps_Intel710.sh)
        - Intel 810          (uses config_pps_Intel810.sh)
        """

        self.vt.console_message("title", "Configure PPS I/O on ALL namespaces", "📍")

        if not self.loaded_namespaces:
            self.vt.console_message(
                "caution",
                "No namespaces loaded. Start namespaces before configuring PPS I/O.",
                indent=1
            )
            return

        try:
            # Iterate over each namespace
            for ns_key, ns_cfg in self.loaded_namespaces.items():

                self.vt.console_message("info", f"Processing namespace: {ns_key}", indent=1)
                hw_type: Optional[str] = ns_cfg.get("hardware")

                # ──────────────────────────────
                # OCP-TAP TimeStick
                # ──────────────────────────────
                if hw_type == "OCP-TAP_TimeStick":
                    self.vt.console_message(
                        "info",
                        "OCP-TAP TimeStick detected → PPS OUT mode enabled by default. No script execution needed.",
                        indent=2,
                    )
                    continue
                # ──────────────────────────────
                # Intel 710
                # ──────────────────────────────
                elif hw_type == "Intel710":
                    pps_mode: Optional[str] = ns_cfg.get("pps_mode")
                    pps_interface: Optional[str] = ns_cfg.get("interface")

                    if not (pps_mode and pps_interface):
                        self.vt.console_message(
                            "error",
                            f"Missing PPS parameters in namespace {ns_key}. Skipping.",
                            indent=2
                        )
                        continue                    
                    
                    self.vt.console_message(
                        "info",
                        f"{hw_type} detected → Configuring PPS (SMA1 {pps_mode}) on {pps_interface}.",
                        indent=2,
                    )

                    script_path: Path = Path(self.scripts_dir) / f"config_pps_{hw_type}.sh"

                    # Ensure script is executable
                    subprocess.run(["chmod", "a+x", script_path], check=True)

                    cmd: list[str] = [str(script_path), ns_key, pps_interface, pps_mode]

                    self.vt.console_message("info", f"Running: {' '.join(cmd)}", indent=2)

                    try:
                        subprocess.run(cmd, check=True)
                        self.vt.console_message("success", f"PPS configured successfully for {ns_key}.", indent=3)

                    except subprocess.CalledProcessError as e:
                        self.vt.console_message(
                            "error",
                            f"Error running PPS script for {ns_key}: {e}",
                            indent=3
                        )
                # ──────────────────────────────
                # Intel 810
                # ──────────────────────────────
                elif hw_type == "Intel810":

                    pps_sma: Optional[str] = ns_cfg.get("pps_sma")
                    pps_mode: Optional[str] = ns_cfg.get("pps_mode")
                    pps_interface: Optional[str] = ns_cfg.get("pps_interface")

                    if not (pps_sma and pps_mode and pps_interface):
                        self.vt.console_message(
                            "error",
                            f"Missing PPS parameters in namespace {ns_key}. Skipping.",
                            indent=2
                        )
                        continue

                    self.vt.console_message(
                        "info",
                        f"{hw_type} detected → Configuring PPS ({pps_sma} {pps_mode}) on {pps_interface}.",
                        indent=2,
                    )

                    script_path: Path = Path(self.scripts_dir) / f"config_pps_{hw_type}.sh"

                    # Ensure script is executable
                    subprocess.run(["chmod", "a+x", script_path], check=True)

                    cmd: list[str] = [str(script_path), pps_interface, str(pps_sma), pps_mode]

                    self.vt.console_message("info", f"Running: {' '.join(cmd)}", indent=2)

                    try:
                        subprocess.run(cmd, check=True)
                        self.vt.console_message("success", f"PPS configured successfully for {ns_key}.", indent=3)

                    except subprocess.CalledProcessError as e:
                        self.vt.console_message(
                            "error",
                            f"Error running PPS script for {ns_key}: {e}",
                            indent=3
                        )

                else:
                    self.vt.console_message(
                        "caution",
                        f"Unknown hardware type '{hw_type}' in namespace {ns_key}. Skipping.",
                        indent=2
                    )

        except KeyboardInterrupt:
            self.vt.console_message("caution", "Operation cancelled by user.")