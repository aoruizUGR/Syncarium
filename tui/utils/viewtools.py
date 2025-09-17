#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# viewtools.py

**Project**: Syncarium - Intelligent Timing Platform Toolkit  
**Description**: User Interface utilities for TUI.  
**Author**: PhD Student Alberto Ortega Ruiz, PhD Student Víctor Vázquez, University of Granada  
**Created**: 2025-05-22  
**Version**: 1.0.0  
**License**: GPLv3
"""


# ─────────────────────────────────────────────────────────────────────────────
# Standard Library Imports
import os
import glob
import re
import time
import shutil
import psutil
import socket
import datetime
import logging
import subprocess
import multiprocessing
import yaml
import locale
from pathlib import Path
from typing import Optional, List, Any

# ─────────────────────────────────────────────────────────────────────────────
# Third-Party Imports
import pyfiglet
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, BarColumn, TimeRemainingColumn
from InquirerPy import inquirer, get_style

# ─────────────────────────────────────────────────────────────────────────────
# Local Application Imports
from syncarium.tui.utils import SysAuxiliar
import syncarium.options.global_vars as global_vars

# ─────────────────────────────────────────────────────────────
# 🖥️ View Tools Class
# ─────────────────────────────────────────────────────────────
class ViewTools:
    """
    Utility class for displaying styled console messages and managing UI-related configurations.

    ### Attributes
    - **console** (`Console`): Rich console instance for styled output.
    - **aux** (`SysAuxiliar`): Auxiliary system utility instance.
    - **config_dir** (`str`): Path to the configuration directory.
    - **scripts_dir** (`str`): Path to the shell scripts directory.
    - **output_dir** (`str`): Path to the output directory.
    - **version** (`str`): Optional version string for display purposes.
    """


# ─────────────────────────────────────────────────────────────────────────────
# 🚧 Function: constructor
# ─────────────────────────────────────────────────────────────────────────────
    def __init__(self, console: Optional[Console] = None, version: str = "") -> None:
        """
        Initializes the ViewTools instance with optional console and version configuration.

        ### Args
        - **console** (`Optional[Console]`): Rich console instance. If not provided, a default one is created.
        - **version** (`str`): Optional version string to display in the UI.
        """

        # Use provided console or create a default one
        self.console: Console = console or Console()

        # Initialize auxiliary system tools
        self.aux: SysAuxiliar = SysAuxiliar()

        # Define paths to configuration, scripts, and output directories
        self.config_dir: Path = global_vars.CONFIG_DIR
        self.scripts_dir: Path = global_vars.SCRIPTS_DIR
        self.output_dir: Path = global_vars.OUTPUT_DIR
        self.version = version 
        locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")


# ─────────────────────────────────────────────────────────────────────────────
# ⌨️ Function: console_message
# ─────────────────────────────────────────────────────────────────────────────
    def console_message(
        self,
        type: str,
        message: str,
        title_emoji: str = "🔷",
        indent: int = 0,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Displays a styled message in the console with optional indentation and logging.

        Applies visual formatting based on message type, including emoji and color style.
        Supports logging the plain-text version of the message if a logger is provided.

        ### Args
        - **type** (`str`): Type of message (e.g., `"success"`, `"error"`, `"info"`).
        - **message** (`str`): Content of the message to display.
        - **title_emoji** (`str`): Emoji used for title-type messages. Defaults to `"🔷"`.
        - **indent** (`int`): Indentation level for visual hierarchy. Defaults to `0`.
        - **logger** (`Optional[Logger]`): Logger instance to log the plain-text message. Defaults to `None`.
        """

        # Define styles and emojis for different message types
        styles = {
            "success": ("✅", "[green]"),
            "error": ("❌", "[red]"),
            "caution": ("⚠️", "[yellow]"),
            "info": ("ℹ️", "[italic cyan]"),
            "clean": ("🗑️", "[italic bright_black]"),
            "exit": ("👋", "[bright_blue]"),
            "main_title": (f"{title_emoji}", "[bold underline bright_white]"),
            "title": (f"{title_emoji}", "[bold blue]")
        }

        # Get emoji and style based on message type
        emoji, style = styles.get(type.lower(), ("❔", "[white]"))

        # Create visual indentation prefix
        prefix = "" if indent == 0 else "│   " * (indent - 1) + "├── "

        # Format each line with style and indentation
        lines = message.split("\n")
        formatted_lines = [
            f"{prefix}{emoji} {style}{line}{style.replace('[', '[/')}"
            for line in lines
        ]
        formatted_message = "\n".join(formatted_lines)

        if logger:
            # Log plain text version if logger is provided
            plain_lines = [f"{prefix}{emoji} {line}" for line in lines]
            plain_message = "\n".join(plain_lines)
            log_func = getattr(logger, type.lower(), logger.info)
            log_func(plain_message)
        else:
            # Print styled message to console
            self.console.print(formatted_message)

# ─────────────────────────────────────────────────────────────────────────────
# ⌨️ Function: console_software_title
# ─────────────────────────────────────────────────────────────────────────────
    def console_software_title(
        self,
        text: str = "Syncarium",
        delay: float = 0.01,
        font: str = "big"
    ) -> None:
        """
        Displays a stylized ASCII art title centered in the terminal, with optional version string.

        Clears the console, renders the title using `pyfiglet`, and centers it horizontally.
        If a version string is set, it is displayed below the title in a dim italic style.

        ### Args
        - **text** (`str`): Text to convert into ASCII art. Defaults to `"Syncarium"`.
        - **delay** (`float`): Delay between printing each line. Defaults to `0.01`.
        - **font** (`str`): Font used for ASCII art. Must be a valid `pyfiglet` font. Defaults to `"big"`.
        """

        # Clear console
        self.console.clear()
        # Create ASCII art
        ascii_art = pyfiglet.figlet_format(text, font=font)
        # Get terminal width
        terminal_width = shutil.get_terminal_size().columns
        for line in ascii_art.splitlines():
            padding = max((terminal_width - len(line)) // 2, 0)
            self.console.print(" " * padding + line, style="bold cyan")
            time.sleep(delay)

        # Mostrar la versión justo debajo, centrada y en estilo más pequeño
        if self.version:
            version_text = f"v{self.version}"
            padding = max((terminal_width - len(version_text)) // 2, 0)
            self.console.print(" " * padding + version_text, style="dim italic")

# ─────────────────────────────────────────────────────────────────────────────
# ⌨️ Function: console_software_subtitle
# ─────────────────────────────────────────────────────────────────────────────
    def console_software_subtitle(self) -> None:
        """
        Displays a centered subtitle panel with a description of the software's features.

        Uses the `rich` library to render a styled panel describing the purpose and
        functionalities of Syncarium. The panel is centered both horizontally and vertically.
        """
        
        # Create the content aligned to the left
        content = Align.left(
            """🛠️ [bold cyan]Intelligent automation for temporal synchronization platforms[/bold cyan]

        [dim]Software designed to simplify the setup, deployment, and monitoring of timing experimentation platforms.[/dim]
        """
        )

        # Create the panel with left-aligned content
        subtitle = Panel.fit(
            content,
            border_style="grey37"
        )

        # Print the panel centered in the terminal
        self.console.print(Align.center(subtitle, vertical="middle"))

# ─────────────────────────────────────────────────────────────────────────────
# ⌨️ Function: console_select_menu
# ─────────────────────────────────────────────────────────────────────────────
    def console_select_menu(
        self,
        choices: list,
        message: str = "Select an option:",
        indent: int = 0
    ) -> Any:
        """
        Displays a styled selection menu in the console with visual indentation for choices.

        Uses `inquirer` to render an interactive menu. Supports indentation for hierarchical
        display of options and accepts both strings and dictionaries with `name` and `value`.

        ### Args
        - **choices** (`list`): List of options to display. Can be strings or dicts with `name` and `value`.
        - **message** (`str`): Prompt message shown above the menu. Defaults to `"Select an option:"`.
        - **indent** (`int`): Indentation level for visual hierarchy. Defaults to `0`.

        ### Returns
        - `Any`: The selected value from the menu.
        """

        inquirer_custom_style = get_style({
            "question": "fg:#00ffff italic",
            "questionmark": "fg:#ff00ff ",
            "answer": "fg:#4169e1 ",
            "pointer": "fg:#00ffff ",
            "highlighted": "#008b8b ",
            "selected": "#008b8b ",
            "instruction": "fg:#cccccc ",
            "text": "fg:#ffffff ",
            "disabled": "fg:#666666 italic ",
        })

        # Visual indentation prefix for choices
        def get_indent_prefix(level):
            if level == 0:
                return ""
            return "│   " * (level - 1) + "├── "

        prefix = get_indent_prefix(indent)

        # Leave the message clean
        indented_message = message

        # Apply visual indentation only to choices
        indented_choices = []
        for choice in choices:
            if isinstance(choice, dict):
                indented_choices.append({
                    "name": f"{prefix}{choice['name']}",
                    "value": choice["value"]
                })
            else:
                indented_choices.append(f"{prefix}{choice}")

        question = inquirer.select(
            message=indented_message,
            choices=indented_choices,
            style=inquirer_custom_style,
            default=None,
            pointer="👉",
            cycle=True,
            instruction="(Usa ↑ ↓ para navegar y ⏎ para seleccionar)",
            qmark="📋"
        )

        return question.execute()


# ─────────────────────────────────────────────────────────────────────────────
# 🔄 Function: refresh_view
# ─────────────────────────────────────────────────────────────────────────────
    def refresh_view(self) -> None:
        """
        Displays a visual refresh indicator in the console.

        Prints a styled message and decorative rules to indicate that the view is being refreshed.
        Includes a short delay to simulate a loading effect.
        """

        # Create a centered, styled text message
        big_text = Text("REFRESHING...", style="bold magenta", justify="center")

        # Print a styled rule and the message to the console
        self.console.rule("[bold cyan]⏳ Refreshing view[/bold cyan]")
        self.console.print(big_text, style="bold magenta", justify="center")
        self.console.rule()

        # Simulate a short delay
        time.sleep(0.5)


# ─────────────────────────────────────────────────────────────────────────────
# 🔄 Function: real_time_log
# ─────────────────────────────────────────────────────────────────────────────
    def real_time_log(self, log_path: str) -> None:
        """
        Displays the contents of a log file in real time using the `tail -F` command.

        Checks if the specified log file exists. If it does, streams its content to the console.
        The user can interrupt the stream with Ctrl+C. If the file is missing, an error is shown.

        ### Args
        - **log_path** (`str`): Path to the log file to monitor.
        """

        if os.path.exists(log_path):
            # Notify the user that real-time log viewing has started
            self.console.print(Panel.fit(
                f"📄 [bold bright_white]Showing {log_path} in real-time[/bold bright_white]. Press Ctrl+C to exit.",
                style="sky_blue3"
            ))
            try:
                subprocess.run(["tail", "-F", log_path])
            except KeyboardInterrupt:
                self.console_message("caution", "Operation cancelled by user.")
        else:
            self.console_message("error", f"Log file {log_path} not found")

# ─────────────────────────────────────────────────────────────────────────────
# 🔄 Function: real_time_progress
# ─────────────────────────────────────────────────────────────────────────────
    def real_time_progress(
        self,
        start_time: float,
        duration: int,
        message: str,
        repetition_info: Optional[int]
    ) -> None:
        """
        Displays a real-time progress bar for the duration of a running process.

        Uses Rich's progress bar to visually represent elapsed time. Updates until the
        specified duration is reached or the user interrupts the display.

        ### Args
        - **start_time** (`float`): Timestamp when the process started (in seconds since epoch).
        - **duration** (`int`): Total duration of the process in seconds.
        - **message** (`str`): Message to display alongside the progress bar.
        - **repetition_info** (`Optional[int]`): Optional repetition count to append to the message.
        """

        if not start_time or not duration:
            self.console_message("error", "Process has not started yet.")
            return

        total_seconds = duration
        elapsed = lambda: time.time() - start_time

        try:
            with Progress(
                "[progress.description]{task.description}",
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.0f}%",
                TimeRemainingColumn(),
                console=self.console,
                transient=True
            ) as progress:
                message = message + (f" ({repetition_info})" if repetition_info else "")
                task = progress.add_task(message, total=total_seconds)
                self.console_message("info", "Press Ctrl+C to exit.")

                # Update progress bar until time is up or user interrupts
                while not progress.finished:
                    progress.update(task, completed=elapsed())
                    if elapsed() >= total_seconds:
                        break
                    time.sleep(0.5)

            self.console_message("success", "Progress completed.")
        except KeyboardInterrupt:
            self.console_message("caution", "Progress display cancelled by user.")


# ─────────────────────────────────────────────────────────────────────────────
# 🧮 Function: table_network_namespaces
# ─────────────────────────────────────────────────────────────────────────────
    def table_network_namespaces(self) -> None:
        """
        Displays a table of network namespaces and their associated interfaces.

        Uses system commands to retrieve information about existing network namespaces,
        including their interfaces, IP addresses, MAC addresses, and default gateways.
        The data is presented in a styled table using the `rich` library. If no namespaces
        are found, a warning panel is displayed.
        """

        try:
            # Get the list of network namespaces
            result = subprocess.run(["sudo","ip", "netns", "list"], capture_output=True, text=True, check=True)
            namespaces = result.stdout.strip().split('\n')

            # Create the table layout
            table = Table(
                title="🌐 Network Namespaces",
                show_header=True,
                header_style="bold cyan",
                title_justify="left"
            )
            table.add_column("Namespace", justify="center", overflow="fold")
            table.add_column("Interface", justify="center", overflow="fold")
            table.add_column("IP Address", justify="center", overflow="fold")
            table.add_column("MAC Address", justify="center", overflow="fold")
            table.add_column("Gateway", justify="center", overflow="fold")

            if namespaces and namespaces[0]:
                for ns_line in namespaces:
                    ns = ns_line.split()[0]
                    try:
                        # Get interfaces in the namespace
                        interfaces_result = subprocess.run(
                            ["sudo", "ip", "netns", "exec", ns, "ip", "-o", "link", "show"],
                            capture_output=True, text=True, check=True
                        )
                        interfaces = interfaces_result.stdout.strip().split('\n')
                        if not interfaces:
                            continue

                        # Get IP addresses
                        try:
                            ip_result = subprocess.run(
                                ["sudo", "ip", "netns", "exec", ns, "ip", "-o", "-4", "addr", "show"],
                                capture_output=True, text=True, check=True
                            )
                            ips = ip_result.stdout.strip().split('\n')
                        except subprocess.CalledProcessError:
                            ips = []

                        # Get default gateways
                        try:
                            gw_result = subprocess.run(
                                ["sudo", "ip", "netns", "exec", ns, "ip", "route", "show", "default"],
                                capture_output=True, text=True, check=True
                            )
                            gws = gw_result.stdout.strip().split('\n')
                        except subprocess.CalledProcessError:
                            gws = []

                        for line in interfaces:
                            parts = line.split()
                            if len(parts) >= 2:
                                iface = parts[1].strip(':')
                                if iface == "lo":
                                    continue
                                # Get MAC address
                                try:
                                    mac_result = subprocess.run(
                                        ["sudo", "ip", "netns", "exec", ns, "ip", "link", "show", iface],
                                        capture_output=True, text=True, check=True
                                    )
                                    mac_line = next((l for l in mac_result.stdout.splitlines() if "link/ether" in l), None)
                                    mac = mac_line.split()[1] if mac_line else "N/A"
                                except subprocess.CalledProcessError:
                                    mac = "N/A"

                                # Match IP and gateway to interface
                                ip = next((ip_line.split()[3] for ip_line in ips if iface in ip_line), "N/A")
                                gw = next((gw_line.split()[2] for gw_line in gws if "via" in gw_line), "N/A")

                                # Add row to the table
                                table.add_row(ns, iface, ip, mac, gw)

                    except subprocess.CalledProcessError as e:
                        # Handle errors per namespace
                        self.console_message("error",f"Error processing namespace '{ns}': {e}")
                        continue

                # Display the final table
                self.console.print(table)

            else:
                # No namespaces found
                self.console.print(Panel.fit(
                    "[bold yellow]No network namespaces found.[/bold yellow]",
                    title="🌐 Network Namespaces",
                    border_style="red"
                ))

        except subprocess.CalledProcessError as e:
            # Handle general error
            self.console_message("error",f"Error retrieving namespaces: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# 🧮 Function: table_synccore_processes
# ─────────────────────────────────────────────────────────────────────────────   
    def table_synccore_processes(self) -> None:
        """
        Displays a table of currently running PTP (Precision Time Protocol) processes.

        Uses `pgrep` and `ps` to identify running `ptp4l` processes and extract details
        such as PID, start time, command line, and stdout redirection path. If no processes
        are found, a warning panel is shown.
        """

        # Run pgrep to find all running ptp4l processes with full command line
        result = subprocess.run(["sudo","pgrep", "-a", "ptp4l"], capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()

        # If no processes are found, show a warning panel
        if not lines:
            self.console.print(Panel.fit(
                "[bold yellow]No PTP processes have been started or are currently running.[/bold yellow]",
                title="⏱️ PTP Processes Status",
                border_style="red"
            ))
            return

        # Create a rich table to display process information
        table = Table(
            title="⏱️ PTP Processes Status",
            show_header=True,
            header_style="bold cyan",
            title_justify="left",
        )
        table.add_column("PID", justify="center", overflow="fold")
        table.add_column("Start Time", justify="center", overflow="fold")
        table.add_column("Command", justify="left", overflow="fold")
        table.add_column("Stdout Redirection", justify="left", overflow="fold")

        # Populate the table with process details
        for line in lines:
            pid, *cmd = line.split()
            cmd_str = " ".join(cmd)

            # Get process start time
            start_time = datetime.datetime.strptime(
                subprocess.run(
                    ["sudo", "ps", "-p", pid, "-o", "lstart="], capture_output=True, text=True
                ).stdout.strip().replace("  ", " "), "%a %b %d %H:%M:%S %Y"
            ).strftime("%d-%m-%Y %H:%M:%S")



            # Get stdout redirection path (if any)
            stdout_path = subprocess.run(
                ["sudo", "readlink", f"/proc/{pid}/fd/1"],
                capture_output=True,
                text=True
            ).stdout.strip() or "N/A"

            table.add_row(pid, start_time, cmd_str, stdout_path)

        # Print the table to the console
        self.console.print(table)

# ─────────────────────────────────────────────────────────────────────────────
# 🧮 Function: table_dpdk_bound_devices
# ─────────────────────────────────────────────────────────────────────────────
    def table_dpdk_bound_devices(self, dpdk_path: str) -> List[str]:
        """
        Lists network devices currently bound to DPDK-compatible drivers.

        Executes the `dpdk_nic_bind.py -s` script to retrieve information about
        network interfaces using DPDK drivers. Parses the output to extract device
        details and displays them in a formatted Rich table.

        ### Args
        - **dpdk_path** (`str`): Path to the directory containing the `dpdk_devbind.py` script.

        ### Returns
        - `List[str]`: List of strings representing DPDK-bound devices, or an empty list if none are found.
        """

        try:
            # Run the dpdk_nic_bind.py script with the -s flag to list devices
            result = subprocess.run(
                ["sudo", "./dpdk-devbind.py", "-s"],
                capture_output=True,
                text=True,
                check=True,
                cwd=dpdk_path  # Set working directory to where the script is located
            )
            output = result.stdout

            dpdk_section = []
            capture = False

            # Parse the output to isolate the section listing DPDK-bound devices
            for line in output.splitlines():
                if "Network devices using DPDK-compatible driver" in line:
                    capture = True
                    continue
                if capture:
                    if line.strip() == "" or line.startswith("==="):
                        continue
                    if line.startswith("Network devices using kernel driver"):
                        break
                    dpdk_section.append(line.strip())

            dpdk_devices = []
            pattern = re.compile(
                r"(?P<pci>\S+)\s+'(?P<name>[^']+)'.*?drv=(?P<driver>\S+)\s+unused=(?P<unused>\S+)"
            )

            for line in dpdk_section:
                match = pattern.search(line)
                if match:
                    dpdk_devices.append(match)


            # If no devices found, show a warning panel
            if not dpdk_devices:
                self.console.print(Panel.fit(
                    "[bold yellow]No devices found using a DPDK-compatible driver.[/bold yellow]",
                    title="🔌 DPDK Devices",
                    border_style="red"
                ))
                return []

            # Create a Rich table to display the device information
            table = Table(
                title="🔌 DPDK Devices",
                show_header=True,
                header_style="bold cyan",
                title_justify="left"
            )
            table.add_column("PCI Address", justify="center", overflow="fold")
            table.add_column("Device Name", justify="center", overflow="fold")
            table.add_column("Driver Used", justify="center", overflow="fold")
            table.add_column("Unused Drivers", justify="center", overflow="fold")

            # Extract fields from each line and add them to the table
            for match in dpdk_devices:
                pci = match.group("pci")
                name = match.group("name")
                driver = match.group("driver")
                unused = match.group("unused")
                table.add_row(pci, name, driver, unused)

            # Print the table to the console
            self.console.print(table)
            return dpdk_devices
        except subprocess.CalledProcessError as e:
            # Print an error message if the script execution fails
            self.console_message("error",f"Error running dpdk_nic_bind.py: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# 🧮 Function: table_tgen
# ─────────────────────────────────────────────────────────────────────────────   
    def table_loadgen(self) -> None:
        """
        Displays a table of currently running TRex traffic generator server processes.

        Uses `pgrep` and `ps` to identify running `_t-rex-64` processes and extract
        details such as PID, start time, and command line. If no processes are found,
        a warning panel is displayed.
        """

        # Run pgrep to find all running _t-rex-64 processes with full command line
        result = subprocess.run(["sudo","pgrep", "-a", "_t-rex-64"], capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()

        # If no processes are found, show a warning panel
        if not lines:
            self.console.print(Panel.fit(
                "[bold yellow]TRex Server is not currently running.[/bold yellow]",
                title="🖥️ TRex Server Status",
                border_style="red"
            ))
            return

        # Create a rich table to display process information
        table = Table(
            title="🖥️ TRex Server Status",
            show_header=True,
            header_style="bold cyan",
            title_justify="left"
        )
        table.add_column("PID", justify="center", overflow="fold")
        table.add_column("Start Time", justify="center", overflow="fold")
        table.add_column("Command", justify="left", overflow="fold")

        # Populate the table with process details
        for line in lines:
            pid, *cmd = line.split()
            cmd_str = " ".join(cmd)

            # Get process start time
            start_time = datetime.datetime.strptime(
                subprocess.run(
                    ["sudo", "ps", "-p", pid, "-o", "lstart="], capture_output=True, text=True
                ).stdout.strip().replace("  ", " "), "%a %b %d %H:%M:%S %Y"
            ).strftime("%d-%m-%Y %H:%M:%S")

            table.add_row(pid, start_time, cmd_str)

        # Print the table to the console
        self.console.print(table)

# ─────────────────────────────────────────────────────────────────────────────
# 🧮 Function: table_stl_program
# ─────────────────────────────────────────────────────────────────────────────
    def table_stl_program(
        self,
        stl_process,
        filename: str,
        args: List[str],
        start_time: float,
        duration: int,
        state: str
    ) -> None:
        """
        Displays a table summarizing the status of an STL process.

        Shows process metadata including PID, state, filename, arguments, duration,
        and start time. If no process is running, a warning panel is displayed.

        ### Args
        - **stl_process**: STL process object. Must have a `pid` attribute.
        - **filename** (`str`): Name of the STL file being processed.
        - **args** (`List[str]`): List of arguments passed to the STL process.
        - **start_time** (`float`): Timestamp indicating when the process started.
        - **duration** (`int`): Duration of the process in seconds.
        - **state** (`str`): Current state of the STL process.
        """

        if not stl_process:
            # Show a warning if the process is not running
            self.console.print(Panel.fit(
                "[bold yellow]No STL process alive.[/bold yellow]",
                title="🚀 STL Process Status",
                border_style="red"
            ))
            return

        # Create and configure the table
        table = Table(
            title="🚀 STL Process Status",
            show_header=True,
            header_style="bold cyan",
            title_justify="left"
        )
        table.add_column("PID", justify="center", overflow="fold")
        table.add_column("State", justify="center", overflow="fold")
        table.add_column("Filename", justify="center", overflow="fold")
        table.add_column("Args", justify="center", overflow="fold")
        table.add_column("Duration", justify="center", overflow="fold")
        table.add_column("Start Time", justify="center", overflow="fold")
        
        # Format values for display
        pid = str(stl_process.pid)
        state = state
        output = filename or "N/A"
        start = datetime.datetime.fromtimestamp(start_time).strftime("%d-%m-%Y %H:%M:%S") if start_time else "N/A"
        duration_str = f"{duration} sec" if duration else "N/A"
        args_str = ",".join([str(arg) for arg in args])

        # Add a row with the current extraction status
        table.add_row(pid, state, output, args_str, duration_str, start)

        # Print the table to the console
        self.console.print(table)


# ─────────────────────────────────────────────────────────────────────────────
# 🧮 Function: table_datasources
# ─────────────────────────────────────────────────────────────────────────────
    def table_datasources(self, sources: List[dict]) -> None:
        """
        Displays a formatted table of loaded data sources in the console.

        Uses Rich to render a table showing the name, type, and parameters of each
        loaded data source. If no sources are provided, a warning panel is shown.

        ### Args
        - **sources** (`List[dict]`): List of dictionaries representing data source configurations.
        """

        if not sources:
            # Show a warning panel if no sources are loaded
            self.console.print(Panel.fit(
                "[bold yellow]No sources have been loaded.[/bold yellow]",
                title="🛢️ Data Sources Loaded",
                border_style="red"
            ))
            return
        # Create and configure the table
        table = Table(
            title="🛢️ Data Sources Loaded",
            show_header=True,
            header_style="bold cyan",
            title_justify="left",
        )
        table.add_column("Name", justify="center", overflow="fold")
        table.add_column("Source Type", justify="center", overflow="fold")
        table.add_column("Parameters", justify="center", overflow="fold")

        # Populate the table with source data
        for source in sources:
            name = source.get("name", "Unknown")
            source_type = source.get("class", type(None)).__name__
            args = source.get("args", {})

            try:
                parameters = ", ".join(f"{k}={v}" for k, v in args.items())
            except Exception as e:
                parameters = f"[Error: {e}]"

            table.add_row(name, source_type, parameters)

        # Print the table to the console
        self.console.print(table)

# ─────────────────────────────────────────────────────────────────────────────
# 🧮 Function: table_last_metric
# ─────────────────────────────────────────────────────────────────────────────
    def table_last_metric(self) -> None:
        """
        Displays a table with metadata from the 5 most recent extraction YAML files.

        Scans the output directory for YAML files containing extraction metadata,
        parses them, and shows a summary table with duration, timestamps, and completion status.
        If more than 5 extractions are found, only the most recent 5 are shown and a warning is displayed.
        """

        # Search recursively for YAML files matching the extraction pattern
        pattern = os.path.join(self.output_dir, "**", "*.yaml")
        files = glob.glob(pattern, recursive=True)

        if not files:
            self.console.print(Panel.fit(
                "[bold yellow]No past extractions found.[/bold yellow]",
                title="📜 Last Data Extracted",
                border_style="red"
            ))
            return

        # Parse metadata and collect start timestamps
        extractions = []
        for file_path in files:
            with open(file_path, 'r') as f:
                metadata = yaml.safe_load(f)
                try:
                    start_ts = datetime.datetime.strptime(metadata["started_at"], "%d-%m-%Y %H:%M:%S")
                    extractions.append((start_ts, file_path, metadata))
                except Exception:
                    continue  # Skip files with invalid or missing timestamps

        # Sort by start timestamp (descending) and select the 5 most recent
        extractions.sort(reverse=True, key=lambda x: x[0])
        recent_extractions = extractions[:5]

        # Create and configure the table
        table = Table(
            title="📜 Last 5 Data Extractions",
            show_header=True,
            header_style="bold cyan",
            title_justify="left"
        )
        table.add_column("HashID", justify="center", overflow="fold")
        table.add_column("Data Sources", justify="center", overflow="fold")
        table.add_column("Duration", justify="center", overflow="fold")
        table.add_column("Start Time", justify="center", overflow="fold")
        table.add_column("Stop Time", justify="center", overflow="fold")
        table.add_column("Completed Successfully", justify="center", overflow="fold")

        # Populate the table with recent extraction data
        for start_ts, file_path, metadata in recent_extractions:
            hash_id = os.path.splitext(os.path.basename(file_path))[0].split("_")[-1]
            datasources = ", ".join(list(metadata["datasources"].keys()))
            duration = str(datetime.timedelta(seconds=metadata["duration"]))
            start_ts_str = start_ts.strftime("%d-%m-%Y %H:%M:%S")

            if "finished_at" in metadata:
                stop_ts = datetime.datetime.strptime(metadata["finished_at"], "%d-%m-%Y %H:%M:%S")
                planned_finish = datetime.datetime.strptime(metadata["finished_at_planned"], "%d-%m-%Y %H:%M:%S")
                completed = stop_ts in (planned_finish, planned_finish + datetime.timedelta(seconds=1))
                stop_ts_str = stop_ts.strftime("%d-%m-%Y %H:%M:%S")
            else:
                stop_ts_str = "Not finished yet"
                completed = "Not finished yet"

            table.add_row(hash_id, datasources, duration, start_ts_str, stop_ts_str, str(completed))

        # Print the table to the console
        self.console.print(table)

        # Show a message if there are more than 5 extractions
        if len(extractions) > 5:
            self.console.print(
                f"[bold yellow]Showing only the 5 most recent extractions out of {len(extractions)} total.[/bold yellow]"
            )


# ─────────────────────────────────────────────────────────────────────────────
# 🧮 Function: table_data_extractor
# ─────────────────────────────────────────────────────────────────────────────
    def table_data_extractor(
        self,
        writer_process: multiprocessing.Process,
        data_sources: List[dict],
        output_file: str,
        start_time: float,
        duration: int
    ) -> None:
        """
        Displays a table summarizing the current status of the data extraction process.

        Checks if the writer process is alive and, if so, prints a table showing its PID,
        output file, start time, duration, and the names of the data sources involved.

        ### Args
        - **writer_process** (`multiprocessing.Process`): Process handling data writing.
        - **data_sources** (`List[dict]`): List of data source configurations.
        - **output_file** (`str`): Path to the output file.
        - **start_time** (`float`): Timestamp when the extraction started.
        - **duration** (`int`): Duration of the extraction in seconds.
        """
    
        if not writer_process.is_alive():
            # Show a warning if the process is not running
            self.console.print(Panel.fit(
                "[bold yellow]No extraction process alive.[/bold yellow]",
                title="📈 Data Extractor Status",
                border_style="red"
            ))
            return

        # Create and configure the table
        table = Table(
            title="📈 Data Extractor Status",
            show_header=True,
            header_style="bold cyan",
            title_justify="left"
        )
        table.add_column("Output HashID", justify="center", overflow="fold")
        table.add_column("PID", justify="center", overflow="fold")
        table.add_column("Start Time", justify="center", overflow="fold")
        table.add_column("Duration", justify="center", overflow="fold")
        table.add_column("Sources", justify="center", overflow="fold")

        # Format values for display
        pid = str(writer_process.pid)
        hash_id = os.path.splitext(os.path.basename(output_file))[0].split("_")[-1]
        start = datetime.datetime.fromtimestamp(start_time).strftime("%d-%m-%Y %H:%M:%S") if start_time else "N/A"
        duration = str(datetime.timedelta(seconds=duration)) if duration else "N/A"
        sources = ", ".join(s["name"] for s in data_sources) if data_sources else "—"

        # Add a row with the current extraction status
        table.add_row(hash_id, pid, start, duration, sources)

        # Print the table to the console
        self.console.print(table)

# ─────────────────────────────────────────────────────────────────────────────
# 🧮 Function: table_experiment
# ─────────────────────────────────────────────────────────────────────────────
    def table_experiment(
        self,
        exp_fn: str,
        exp_state: str,
        exp_id: str,
        exp_duration: int,
        exp_start_ts: float,
        exp_ptp_clients: str,
        exp_ptp_ts: int,
        exp_stl_fn: str,
        exp_stl_ts: int,
        exp_dext_datasources: str,
        exp_dext_ts: int
    ) -> None:
        """
        Displays a table summarizing the current experiment's status and associated files.

        Shows metadata including experiment ID, name, state, duration, start time,
        and associated PTP, STL, and DEXT components with their respective start times.

        ### Args
        - **exp_fn** (`str`): Name of the experiment.
        - **exp_state** (`str`): Current state of the experiment (e.g., `"Running"`, `"Completed"`).
        - **exp_id** (`str`): Unique identifier (HashID) of the experiment.
        - **exp_duration** (`int`): Total duration of the experiment in seconds.
        - **exp_start_ts** (`float`): Timestamp when the experiment started.
        - **exp_ptp_clients** (`str`): Comma-separated list of PTP client names.
        - **exp_ptp_ts** (`int`): Start time (in seconds) of the PTP process.
        - **exp_stl_fn** (`str`): Filename of the STL file.
        - **exp_stl_ts** (`int`): Start time (in seconds) of the STL process.
        - **exp_dext_datasources** (`str`): Comma-separated list of DEXT data sources.
        - **exp_dext_ts** (`int`): Start time (in seconds) of the DEXT process.
        """

        if not exp_id:
            # Show a warning if no experiment is loaded or running
            self.console.print(Panel.fit(
                "[bold yellow]No experiment loaded or running.[/bold yellow]",
                title="🧪 Laboratory Status",
                border_style="red"
            ))
            return

        # Create and configure the table
        table = Table(
            title="🧪 Laboratory Status",
            show_header=True,
            header_style="bold cyan",
            title_justify="left"
        )
        table.add_column("HashID", justify="center", overflow="fold")
        table.add_column("State", justify="center", overflow="fold")
        table.add_column("Name", justify="center", overflow="fold")
        table.add_column("Duration", justify="center", overflow="fold")
        table.add_column("Start Time", justify="center", overflow="fold")
        table.add_column("PTP Clients (Start)", justify="center", overflow="fold")
        table.add_column("STL File (Start)", justify="center", overflow="fold")
        table.add_column("DEXT Datasources (Start)", justify="center", overflow="fold")

        # Format Duration
        exp_duration_str = str(datetime.timedelta(seconds=exp_duration))

        # Format Start Timestamp
        if exp_start_ts:
            exp_start_ts_str = datetime.datetime.fromtimestamp(exp_start_ts).strftime("%d-%m-%Y %H:%M:%S")
        else:
            exp_start_ts_str = "Not started yet"

        # Format STL
        if exp_stl_ts == -1:
            exp_stl_fn_str = f"{exp_stl_fn} (NOT)"
        else:
            exp_stl_fn_str = f"{exp_stl_fn} ({str(datetime.timedelta(seconds=exp_stl_ts))})"
        
        # Format PTP
        if exp_ptp_ts == -1:
            exp_ptp_fn_str = ", ".join(exp_ptp_clients) + " (NOT)"
        else:
            exp_ptp_fn_str = ",".join(exp_ptp_clients) + f" ({str(datetime.timedelta(seconds=exp_ptp_ts))})"

        # Format DEXT
        exp_dext_fn_str = ",".join(exp_dext_datasources) + f" ({str(datetime.timedelta(seconds=exp_dext_ts))})"


        # Add a row with the current experiment status
        table.add_row(
            exp_id,
            exp_state,
            exp_fn,
            exp_duration_str,
            exp_start_ts_str,
            exp_ptp_fn_str,
            exp_stl_fn_str,
            exp_dext_fn_str
        )

        # Print the table to the console
        self.console.print(table)

# ─────────────────────────────────────────────────────────────────────────────
# 🪟 Function: panel_platform_info
# ─────────────────────────────────────────────────────────────────────────────
    def panel_platform_info(self) -> None:
        """
        Displays detailed system information in a styled panel.

        Gathers and formats host system details including hostname, CPU model,
        core counts, RAM, temperature, active network interfaces, available shell
        drivers, and configuration files. The information is rendered using Rich
        in a visually styled panel.
        """

        # Gather system information
        now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        hostname = socket.gethostname()
        cpu_model = self.aux.get_cpu_model()
        ram_total_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
        physical_cores = psutil.cpu_count(logical=False)
        logical_cores = psutil.cpu_count(logical=True)
        cpu_temperature = next((s['temperature'] for s in self.aux.get_temperatures() if s['label'] == 'Package id 0'), None)

        # Get active network interfaces and their PCI IDs
        interfaces = [iface for iface in psutil.net_if_addrs().keys() if not iface.startswith("lo")]
        interfaces_info = [(self.aux.get_pci_device(iface), iface) for iface in interfaces]
        interfaces_info.sort()
        formatted_interfaces = [f"{iface} (PCI: {pci})" for pci, iface in interfaces_info]
        interfaces_grid = self.aux.format_columns_with_bullets(formatted_interfaces)

        info_text = (
            f"💻 [bold]Host:[/bold] {hostname}\n"
            f"🧩 [bold]CPU:[/bold] {cpu_model}\n"
            f"🔢 [bold]Physical cores:[/bold] {physical_cores} | [bold]Logical cores:[/bold] {logical_cores}\n"
            f"🧠 [bold]Total RAM:[/bold] {ram_total_gb} GB\n"
            f"🌡️ [bold]CPU Temperature:[/bold] {cpu_temperature} ºC\n"
            f"📅 [bold]Date & Time:[/bold] {now}\n"
            f"🌐 [bold]Active interfaces:[/bold]\n{interfaces_grid}\n"
        )

        self.console.print(
            Align.center(
                Panel.fit(info_text, title="🧠 System Information", border_style="cyan"),
                vertical="middle"
            )
        )