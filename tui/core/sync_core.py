#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# sync_core.py

**Project**: Syncarium - Intelligent Timing Platform Toolkit  
**Description**: Synchronization Core for TUI  
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada  
**Created**: 2025-05-22  
**Version**: 1.0.0  
**License**: GPLv3
"""


# ─────────────────────────────────────────────────────────────────────────────
# Standard Library Imports
import os
import time
import subprocess
import yaml
import re
import psutil
from pathlib import Path
from datetime import datetime
from threading import Lock
from typing import Callable, Optional, Dict, Any

# ─────────────────────────────────────────────────────────────────────────────
# Third-Party Imports
from rich.prompt import Confirm

# ─────────────────────────────────────────────────────────────────────────────
# Local Application Imports
import syncarium.tui.utils as utils
from syncarium.options import global_vars

# ─────────────────────────────────────────────────────────────
# 🕒 SyncCore Class
# ─────────────────────────────────────────────────────────────
class SyncCore:
    """
    Handles Precision Time Protocol (PTP) configuration and management tasks
    within the Syncarium environment.

    ### Attributes:
    - **vt** (`utils.ViewTools`): Utility class for rendering formatted views in the console.
    - **ptp_profile_dir** (`Path`): Path to the directory containing ptp4l-specific configuration files.
    - **log_dir** (`Path`): Path to the directory where log files are stored.
    - **print_lock** (`Lock`): Thread lock used to synchronize console output across threads.
    - **loaded_clients** (`Dict[str, Dict[str, str]]`): Dictionary containing loaded PTP client configurations.
    """


# ─────────────────────────────────────────────────────────────────────────────
# 🚧 Function: constructor
# ─────────────────────────────────────────────────────────────────────────────
    def __init__(self, vt: utils.ViewTools) -> None:
        """
        Initializes the SyncCore instance with required configuration paths and utilities.

        ### Args:
        - **vt** (`utils.ViewTools`): Instance of the view rendering utility used for console output.
        """

        # Store view tools instance
        self.vt: utils.ViewTools = vt

        # Define configuration and logging directories
        self.ptp_profile_dir: Path = global_vars.PTP_PROFILE_DIR
        self.log_dir: Path = global_vars.LOG_DIR

        # Lock for thread-safe console output
        self.print_lock: Lock = Lock()

        # Dictionary to store loaded PTP client configurations
        self.loaded_clients: Dict[str, Dict[str, str]] = {}


# ─────────────────────────────────────────────────────────────────────────────
# 📋 Function: main_menu
# ─────────────────────────────────────────────────────────────────────────────
    def main_menu(self) -> None:
        """
        Displays and manages the interactive terminal-based menu for PTP operations.

        Continuously renders a menu using InquirerPy, allowing the user to perform various
        PTP-related actions such as starting/stopping services, viewing logs, pinging the server,
        and refreshing the interface. The loop continues until the user selects **"❌ Exit"**
        or interrupts the process using **Ctrl+C**.

        ### Menu Options:
        - ⏱️ Start PTP → `start_ptp`
        - 🛑 Stop PTP → `stop_ptp`
        - 📄 Show PTP Logs → `print_ptp_log`
        - 📡 Ping PTP Server → `ping_server`
        - 🔄 Refresh View → refreshes the interface without performing any action
        - ❌ Exit → exits the menu loop

        ### Notes:
        - Graceful exit is supported via **Ctrl+C** interruption.
        """

        try:
            while True:
                # Display the software title
                self.vt.console_software_title(delay=0)

                # Show the main menu header
                self.vt.console_message("main_title", "Synchronization Core Menu", "⏱️")

                # Render a table of active PTP processes
                self.vt.table_synccore_processes()

                # Prompt user with interactive menu
                choice: str = self.vt.console_select_menu(
                    choices=[
                        {"name": "⏱️ Start PTP", "value": "start_ptp"},
                        {"name": "🛑 Stop PTP", "value": "stop_ptp"},
                        {"name": "📄 Show PTP Logs", "value": "print_ptp_log"},
                        {"name": "📡 Ping PTP Server", "value": "ping_server"},
                        {"name": "🔄 Refresh view", "value": "refresh_view"},
                        {"name": "❌ Exit", "value": "exit"},
                    ],
                    indent=1
                )

                # Map menu options to corresponding methods
                submenu: Dict[str, Callable[[], None]] = {
                    "start_ptp":        self.start_ptp,
                    "stop_ptp":         self.stop_ptp,
                    "print_ptp_log":    self.print_ptp_log,
                    "ping_server":      self.ping_server,
                }

                # Handle user selection
                if choice == "exit":
                    break
                elif choice != "refresh_view":
                    action = submenu.get(choice)
                    if action:
                        action()
                        input("\n🔙 Press ⏎ to return to the menu...")

        except KeyboardInterrupt:
            # Gracefully handle Ctrl+C interruption
            self.vt.console_message("exit", "Exiting...")


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: load_clients
# ─────────────────────────────────────────────────────────────────────────────
    def load_clients(
        self,
        file_cfg: Optional[Path] = None,
        logger: Optional[Any] = None,
        extra_indent: int = 0,
        quiet: bool = True
    ) -> bool:
        """
        Loads and validates PTP client configurations from a YAML file.

        If no file is specified, the user is prompted to select one interactively from the available
        YAML files in the configuration directory. Each client's network namespace is validated
        against the system. Clients with missing namespaces are skipped and reported.

        The YAML file must contain a `ptp_clients` section with client definitions.

        ### Args:
        - **file_cfg** (`Optional[str]`): Name of the YAML configuration file to load. If `None`, prompts the user interactively.
        - **logger** (`Optional[Any]`): Logger instance used for logging messages. Defaults to `None`.
        - **extra_indent** (`int`): Additional indentation level for console messages. Defaults to `0`.
        - **quiet** (`bool`): If `True`, suppresses console output. Defaults to `True`.

        ### Returns:
        - `bool`: `True` if clients were successfully loaded and validated; `False` otherwise.
        """

        # Show section title
        if not quiet: self.vt.console_message("title", "Loading PTP Clients", logger=logger, indent=extra_indent)

        # If no file is provided, prompt user to select one
        if file_cfg:
            filepath_cfg: Path = file_cfg

        else:             
            files: list[str] = [
                str(f.relative_to(self.ptp_profile_dir))
                for f in self.ptp_profile_dir.rglob("*.yaml")
                if f.is_file()
            ]
            
            if not files:
                self.vt.console_message(
                    "error",
                    f"No YAML configuration files found in '{self.ptp_profile_dir}'",
                    indent=1 + extra_indent,
                    logger=logger
                )
                return False

            try:
                choices: list[Dict[str, str]] = [
                    {"name": f"{i}. 📄 {name}", "value": name}
                    for i, name in enumerate(sorted(files), 1)
                ]
                selected: str = self.vt.console_select_menu(
                    choices=choices,
                    message="Available Configuration Files:",
                    indent=1 + extra_indent
                )
                filepath_cfg: Path = self.ptp_profile_dir / selected

            except KeyboardInterrupt:
                self.vt.console_message("caution", "Operation cancelled by user.", logger=logger)
                return False
        
        try:
            # Load YAML data
            with open(filepath_cfg, 'r') as f:
                yaml_data: Dict = yaml.safe_load(f)
                self.loaded_clients: Dict[str, Dict[str, str]] = yaml_data.get("ptp_clients", {})

            # Get currently existing namespaces
            ns_result = subprocess.run(["ip", "netns", "list"], stdout=subprocess.PIPE, text=True)
            existing_namespaces: set[str] = {
                line.split()[0] for line in ns_result.stdout.strip().splitlines()
            }

            skipped: list[tuple[str, str]] = []

            # Validate each client namespace
            for client_name, client_data in list(self.loaded_clients.items()):
                ns: Optional[str] = client_data.get("namespace")
                if ns not in existing_namespaces:
                    skipped.append((client_name, ns))
                    del self.loaded_clients[client_name]

            # Report missing namespaces
            if skipped:
                missing = "\n".join(f"⛔ {iface} → Namespace '{ns}' not found" for iface, ns in skipped)
                raise RuntimeError(f"❌ One or more namespaces are missing:\n{missing}")

            # Confirm successful loading
            if not quiet: self.vt.console_message(
                "success",
                f"Clients successfully loaded from {filepath_cfg}.",
                indent=1 + extra_indent,
                logger=logger
            )

            # Display loaded clients
            if self.loaded_clients:
                if not quiet: self.vt.console_message("success", "Loaded PTP Clients:", indent=1 + extra_indent, logger=logger)
                for client_name, data in self.loaded_clients.items():
                    if not quiet: self.vt.console_message(
                        "info",
                        f"{client_name} → Namespace: {data['namespace']} / Interface: {data['interface']} / Config: {data['config']}",
                        indent=2 + extra_indent,
                        logger=logger
                    )

            return True

        except Exception as e:
            # Handle YAML or validation errors
            if not quiet: self.vt.console_message(
                "error",
                f"Error loading YAML file: {e}",
                indent=1 + extra_indent,
                logger=logger
            )
            return False

# ─────────────────────────────────────────────────────────────
# 📌 Function: start_ptp
# ─────────────────────────────────────────────────────────────
    def start_ptp(
        self,
        logger: Optional[Any] = None,
        extra_indent: int = 0,
        stop: bool = True
    ) -> None:
        """
        Launches `ptp4l` processes for all configured clients.

        If enabled, checks for existing `ptp4l` processes and prompts the user to stop them before starting new ones.
        If no clients are currently loaded, attempts to load them from configuration files.

        For each valid client, starts a `ptp4l` process within its corresponding network namespace using `sudo`,
        with output redirected to a dedicated log file. Displays process information including PID, log path, and command.

        ### Args
        - **logger** (`Optional[Any]`): Logger instance for logging messages. Defaults to `None`.
        - **extra_indent** (`int`): Indentation level for console messages. Defaults to `0`.
        - **stop** (`bool`): Whether to stop existing `ptp4l` processes before launching new ones. Defaults to `True`.
        """

        # Stop and clean actual clients if enabled
        if stop:

            # Check for existing ptp4l processes
            result = subprocess.run(["pgrep", "-a", "ptp4l"], capture_output=True, text=True)
            lines: list[str] = result.stdout.strip().splitlines()

            if lines:
                self.vt.console_message("caution", "There are PTP clients already running.", indent=1 + extra_indent)
                confirm: bool = Confirm.ask("⚠️ Are you sure you want to stop the actual PTP processes?", default=True)
                if confirm:
                    self.stop_ptp(preconfirmation=True, logger=logger, extra_indent=extra_indent)
                else:
                    self.vt.console_message("success", "Not starting new PTP processes.", indent=2 + extra_indent)
                    return

        # Load client configurations if not already loaded
        if not self.loaded_clients:
            if not self.load_clients(logger=logger, extra_indent=extra_indent):
                self.vt.console_message("error", "Aborting operation due to failed client loading.", indent=1 + extra_indent, logger=logger)
                return

        self.vt.console_message("title", "Starting PTP processes", title_emoji="⏱️", logger=logger, indent=extra_indent)

        for client_name, data in self.loaded_clients.items():
            config_path: Path = self.ptp_profile_dir / data["config"]
            namespace: str = data["namespace"]
            log_path: Path = self.log_dir / f"ptp-{client_name}.log"

            # Validate config file existence
            if not config_path.exists():
                with self.print_lock:
                    self.vt.console_message("error", f"Configuration file not found: {config_path}.", indent=1 + extra_indent, logger=logger)
                continue

            # Ensure log directory exists and reset log file
            self.log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_path, 'w') as f:
                f.write(f"[{datetime.now()}] Log reset for {client_name}\n")

            # Build ptp4l command
            command: list[str] = [
                "ip", "netns", "exec", namespace,
                "ptp4l", "-f", str(config_path), "-s", "-q", "-m", "0"
            ]

            try:
                # Launch ptp4l process with sudo and redirect output to log
                with open(log_path, 'a') as log_file:
                    ptp_process = subprocess.Popen(
                        ["sudo"] + command,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        stdin=subprocess.DEVNULL,
                        close_fds=True,
                        preexec_fn=os.setpgrp
                    )

                time.sleep(0.5)

                # Locate the actual ptp4l child process
                ptp4l_proc = None
                try:
                    parent = psutil.Process(ptp_process.pid)
                    for child in parent.children(recursive=True):
                        if "ptp4l" in child.name():
                            ptp4l_proc = child
                            break
                except psutil.NoSuchProcess:
                    pass

                if ptp4l_proc is None:
                    with self.print_lock:
                        self.vt.console_message("caution", f"PTP4L process not found in {namespace}.", indent=1 + extra_indent, logger=logger)
                    continue

                # Format and display process information
                start_time: str = datetime.now().strftime("%D-%H:%M:%S")
                cmd_str: str = " ".join(command[3:])

                with self.print_lock:
                    self.vt.console_message("success", "PTP launched successfully.", indent=1 + extra_indent, logger=logger)
                    self.vt.console_message("info", f"Client: {client_name} | PID: {ptp4l_proc.pid} | Started at: {start_time}", indent=2 + extra_indent, logger=logger)
                    self.vt.console_message("info", f"Log: {log_path}", indent=2 + extra_indent, logger=logger)
                    self.vt.console_message("info", f"Command: {cmd_str}", indent=2 + extra_indent, logger=logger)

            except Exception as e:
                with self.print_lock:
                    self.vt.console_message("error", f"Error launching PTP on {client_name}: {e}", indent=2 + extra_indent, logger=logger)


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: stop_ptp
# ─────────────────────────────────────────────────────────────────────────────
    def stop_ptp(
        self,
        preconfirmation: Optional[bool] = False,
        logger: Optional[Any] = None,
        extra_indent: int = 0,
        quiet: bool = True
    ) -> None:
        """
        Terminates all active `ptp4l` processes and removes associated log files.

        Detects running `ptp4l` processes and optionally prompts the user for confirmation before terminating them.
        After stopping the processes, it deletes all related log files and clears the loaded client configurations.

        ### Args
        - **preconfirmation** (`Optional[bool]`): If `True`, skips the confirmation prompt. Defaults to `False`.
        - **logger** (`Optional[Any]`): Logger instance for logging messages. Defaults to `None`.
        - **extra_indent** (`int`): Indentation level for console messages. Defaults to `0`.
        - **quiet** (`bool`): If `True`, suppresses non-critical console output. Defaults to `True`.
        """

        # Show section title
        if not quiet: self.vt.console_message("title", "Stopping ptp processes", "🛑", logger=logger, indent=extra_indent)

        # Check for running ptp4l processes
        result = subprocess.run(["pgrep", "-a", "ptp4l"], capture_output=True, text=True)
        lines: list[str] = result.stdout.strip().splitlines()

        if not lines:
            if not quiet: self.vt.console_message("info", "No active ptp4l processes found.", indent=1 + extra_indent, logger=logger)
            return

        # Ask for confirmation unless preconfirmed
        if not preconfirmation:
            confirm: bool = Confirm.ask("⚠️ Are you sure you want to stop the PTP processes?", default=True)
            if not confirm:
                self.vt.console_message("info", "Stop operation cancelled.", indent=1 + extra_indent, logger=logger)
                return

        try:
            # Kill each ptp4l process
            if not quiet: self.vt.console_message("info", "Killing all ptp4l processes:", indent=1 + extra_indent, logger=logger)
            for line in lines:
                pid, *cmd = line.split()
                if not quiet: self.vt.console_message("clean", f"Killing PTP4l process with PID {pid} → {' '.join(cmd)}", indent=2 + extra_indent, logger=logger)
                subprocess.run(["sudo", "kill", "-9", pid], check=True)

            if not quiet: self.vt.console_message("success", "All ptp4l processes have been terminated.", indent=1 + extra_indent, logger=logger)

        except subprocess.CalledProcessError as e:
            self.vt.console_message("error", f"Error stopping ptp4l processes: {e}", indent=2 + extra_indent, logger=logger)

        try:
            # Check and clean log directory
            if not self.log_dir.exists():
                self.vt.console_message("info", f"Log directory does not exist: {self.log_dir}", indent=1 + extra_indent, logger=logger)
                return

            logfiles: list[str] = [f.name for f in self.log_dir.iterdir() if f.is_file()]

            if not logfiles:
                self.vt.console_message("info", f"No log files found in: {self.log_dir}", indent=1 + extra_indent, logger=logger)
                return

            if not quiet: self.vt.console_message("info", "Removing all ptp4l log files:", indent=1 + extra_indent, logger=logger)

            # Delete each log file
            for archivo in logfiles:
                logpath: Path = self.log_dir / archivo
                if logpath.is_file():
                    try:
                        logpath.unlink()
                        if not quiet: self.vt.console_message("clean", f"Deleted log file: {logpath}", indent=2 + extra_indent, logger=logger)
                    except Exception as e:
                        self.vt.console_message("error", f"Failed to delete log file {logpath}: {e}", indent=2 + extra_indent, logger=logger)

            self.vt.console_message("success", "All log files have been processed.", indent=1 + extra_indent, logger=logger)

        except Exception as e:
            self.vt.console_message("error", f"Unexpected error while deleting log files: {e}", indent=1 + extra_indent, logger=logger)

        # Clear loaded client configurations
        self.loaded_clients = {}


# ─────────────────────────────────────────────────────────────
# 📌 Function: print_ptp_log
# ─────────────────────────────────────────────────────────────
    def print_ptp_log(self) -> None:
        """
        Displays and follows the real-time log of a selected PTP client.

        Lists all available PTP log files corresponding to the namespaces defined in the `ptp_clients` dictionary.
        Prompts the user to select one and uses `tail -F` to stream the log output in real time.
        """

        # Show section title
        self.vt.console_message("title", "Printing ptp logs", "📄")

        # Check if ptp4l is running
        result = subprocess.run(["pgrep", "-a", "ptp4l"], capture_output=True, text=True)
        lines: list[str] = result.stdout.strip().splitlines()
        if not lines:
            self.vt.console_message("caution", "No PTP processes have been started or are currently running.", indent=1)
            return

        # Search for log files matching the pattern ptp-<name>.log
        pattern = re.compile(r"^ptp-(.+)\.log$")
        available_logs: list[str] = []

        for filename in self.log_dir.iterdir():
            if filename.is_file():
                match = pattern.match(filename.name)
                if match:
                    available_logs.append(match.group(1))

        if not available_logs:
            self.vt.console_message("caution", "No log files found for the defined namespaces.", indent=1)
            return

        try:
            # Build menu choices from log file names
            choices: list[Dict[str, str]] = [
                {"name": f"{i}. 📄 {name}", "value": name}
                for i, name in enumerate(sorted(available_logs), 1)
            ]

            # Prompt user to select a log
            selected: str = self.vt.console_select_menu(
                choices=choices,
                message="Available PTP Logs:",
                indent=1
            )

            # Build full path to the selected log file
            log_path: Path = self.log_dir / f"ptp-{selected}.log"

        except KeyboardInterrupt:
            # Handle cancellation
            self.vt.console_message("caution", "Operation cancelled by user.")
            return

        # Display the log in real time
        self.vt.real_time_log(log_path)


# ─────────────────────────────────────────────────────────────
# 📌 Function: ping_server
# ─────────────────────────────────────────────────────────────
    def ping_server(self) -> None:
        """
        Performs a ping test to the PTP server from each configured namespace.

        For each client, extracts the server's IP address from its `.config` file by locating the line containing `'UDPv4'`.
        Then, executes a ping command from the corresponding network namespace to verify connectivity.
        Displays the result of each ping attempt in the console.
        """

        # Check if ptp4l is currently running
        result = subprocess.run(["pgrep", "-a", "ptp4l"], capture_output=True, text=True)
        lines: list[str] = result.stdout.strip().splitlines()
        if lines:
            self.vt.console_message("caution", "PTP processes have been started or are currently running.", indent=1)
            return

        # Load client configurations
        if not self.load_clients():
            self.vt.console_message("caution", "Aborting ping test due to failed client loading.", indent=1)
            return

        self.vt.console_message("title", "Pinging PTP Server from each Namespace", "📡")

        # Iterate over each client to perform ping
        for iface, data in self.loaded_clients.items():
            namespace: str = data["namespace"]
            config_path: Path = Path(self.ptp_profile_dir) / data["config"]

            # Extract server IP from config file
            try:
                with open(config_path, "r") as f:
                    lines = f.readlines()

                server_ip: str | None = None
                for line in lines:
                    if "UDPv4" in line:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            server_ip = parts[1]
                            break

                if not server_ip:
                    self.vt.console_message("error", f"No 'UDPv4' entry found in config for {iface} ({namespace})", indent=1)
                    continue

            except Exception as e:
                self.vt.console_message("error", f"Error reading config file for {iface} ({namespace}): {e}", indent=1)
                continue

            # Notify user and execute ping
            self.vt.console_message("info", f"Pinging from {namespace} to {server_ip}...", indent=1)
            try:
                output: str = subprocess.check_output(
                    ["sudo", "ip", "netns", "exec", namespace, "ping", "-c", "5", server_ip],
                    stderr=subprocess.STDOUT
                ).decode()

                self.vt.console_message("info", f"{output}", indent=2)

            except subprocess.CalledProcessError as e:
                self.vt.console_message("error", f"Ping failed from {namespace}:\n{e.output.decode()}", indent=2)

            # Brief pause before next ping
            time.sleep(0.5)
