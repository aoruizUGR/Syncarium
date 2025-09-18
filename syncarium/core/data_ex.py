#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# data_ex.py

**Project**: Syncarium – Intelligent Timing Platform Toolkit  
**Description**: Data Extractor for TUI  
**Author**: PhD Student Alberto Ortega Ruiz, PhD Student Víctor Vázquez, University of Granada  
**Created**: 2025-05-31  
**Version**: 1.0.0  
**License**: GPLv3
"""


# ─────────────────────────────────────────────────────────────────────────────
# Standard Library Imports
import csv
import threading
import multiprocessing
import queue
import yaml
import time
import datetime
import signal
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable

# ─────────────────────────────────────────────────────────────────────────────
# Third-Party Imports
from rich.prompt import Prompt, IntPrompt, Confirm

# ─────────────────────────────────────────────────────────────────────────────
# Local Application Imports
import syncarium.utils as utils
import syncarium.core.dsources as dsources
import syncarium.options.global_vars as global_vars


# ─────────────────────────────────────────────────────────────
# 📈 DataEx Class
# ─────────────────────────────────────────────────────────────
class DataEx:
    """
    Tool for extracting data from configured sources and managing output files.

    ### Attributes
    - **vt** (`utils.ViewTools`): Utility tools for view-related operations.
    - **output_dir** (`Path`): Directory where output files will be stored.
    - **loaded_datasources** (`List[dsources.DataSource]`): List of data sources that have been loaded.
    - **writer_process** (`multiprocessing.Process`): Background process responsible for writing output.
    - **output_filepath** (`Optional[Path]`): Path to the output file, if available.
    - **start_time** (`Optional[float]`): Timestamp marking the start of the extraction process.
    - **duration** (`Optional[int]`): Duration of the extraction process in seconds.
    """

    # ─────────────────────────────────────────────────────────────
    # 🚧 Constructor
    # ─────────────────────────────────────────────────────────────
    def __init__(self, vt: utils.ViewTools) -> None:
        """
        Initialize a new instance of `DataEx` with default paths and metadata.

        ### Args
        - **vt** (`utils.ViewTools`): Utility tools for view-related operations.
        """

        # Store the view tools instance
        self.vt: utils.ViewTools = vt

        # Define configuration and output directories using pathlib
        self.datasources_dir: Path = global_vars.DATASOURCES_DIR
        self.output_dir: Path = global_vars.OUTPUT_DIR

        # Initialize the list of loaded data sources
        self.loaded_datasources: List[dsources.DataSource] = []

        # Prepare the writer process (not started yet)
        self.writer_process: multiprocessing.Process = multiprocessing.Process()

        # Initialize metadata for output tracking
        self.output_filepath: Optional[Path] = None
        self.start_time: Optional[float] = None
        self.duration: Optional[int] = None


# ─────────────────────────────────────────────────────────────────────────────
# 📋 Function: main_menu
# ─────────────────────────────────────────────────────────────────────────────
    def main_menu(self) -> None:
        """
        Render and manage the interactive terminal-based main menu for data extraction.

        Continuously displays a menu using InquirerPy, allowing the user to:
        - Load data sources
        - Start or stop the extractor
        - View progress and extracted data
        - Refresh the view
        - Exit the tool

        The loop runs until the user selects **"❌ Exit"** or interrupts the process with **Ctrl+C**.

        ### Menu Options
        - 🛢️ Load Data Sources → `load_datasources`
        - 📈 Start Extractor → `start_extraction`
        - 🛑 Stop Extractor → `stop_extraction`
        - ⏳ Show Progress → `show_progress`
        - 📄 Show Extracted Data → `show_extracted_data`
        - 🔄 Refresh View → no action
        - ❌ Exit → terminates the menu loop

        ### Notes
        - Graceful termination is supported via **Ctrl+C**.
        """

        try:
            while True:
                # Show software title without delay
                self.vt.console_software_title(delay=0)

                # Display the main menu title
                self.vt.console_message("main_title", "Data Extractor Menu", "📈")

                # Show the most recent metric
                self.vt.table_last_metric()

                # Display loaded data sources
                self.vt.table_datasources(self.loaded_datasources)

                # Show extractor status and output information
                self.vt.table_data_extractor(
                    self.writer_process,
                    self.loaded_datasources,
                    self.output_filepath,
                    self.start_time,
                    self.duration
                )

                # Present interactive menu options
                choice: str = self.vt.console_select_menu(
                    choices=[
                        {"name": "🛢️ Load Data Sources", "value": "load_datasources"},
                        {"name": "📈 Start Extractor", "value": "start_extraction"},
                        {"name": "🛑 Stop Extractor", "value": "stop_extraction"},
                        {"name": "⏳ Show Progress", "value": "show_progress"},
                        {"name": "📄 Show Extracted Data", "value": "show_extracted_data"},
                        {"name": "🔄 Refresh view", "value": "refresh_view"},
                        {"name": "❌ Exit", "value": "exit"},
                    ],
                    indent=1
                )

                # Map menu options to corresponding methods
                submenu: dict[str, Callable[[], None]] = {
                    "load_datasources":     self.load_datasources,
                    "start_extraction":     self.start_extraction,
                    "stop_extraction":      self.stop_extraction,
                    "show_progress":        self.show_progress,
                    "show_extracted_data":  self.show_extracted_data,
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
# 📌 Function: load_datasources
# ─────────────────────────────────────────────────────────────────────────────
    def load_datasources(
        self, 
        file_cfg: Optional[Path] = None, 
        quiet: bool = False
    ) -> None:
        """
        Load and configure data sources from a YAML configuration file.

        Clears any previously loaded sources and parses the selected configuration file,
        instantiating the appropriate data source classes. If no file is provided, the user
        is prompted to select one interactively from the available files in the config directory.

        ### Args
        - **file_cfg** (`Optional[str]`): Path to the YAML configuration file. If `None`, prompts the user to select one.
        - **quiet** (`bool`): If `True`, suppresses console output messages.

        ### Notes
        - Prevents loading if the extractor process is currently running.
        - Supports graceful cancellation via **Ctrl+C**.
        - Automatically creates missing log files if required by a `FileLogDataSource`.
        - Displays success or error messages for each data source loaded.
        """


        if not quiet: self.vt.console_message("title", "Data Sources Configuration", "🛢️")

        # Prevent loading if extractor is running
        if self.writer_process.is_alive():
            self.vt.console_message("info", "Data extractor is running already.", indent=1)
            return

        # Clear previously loaded data sources
        if self.loaded_datasources:
            if not quiet: self.vt.console_message("clean", "Deleting previous data sources.", indent=1)
            self.loaded_datasources = []

        # Determine configuration file path
        if file_cfg:
            filepath_cfg: Path = file_cfg
        
        else:
            config_files = [f.name for f in Path(self.datasources_dir).glob("*.yaml")]

            if not config_files:
                self.vt.console_message("error", f"No data sources files found in '{self.datasources_dir}'.", indent=1)
                return

            try:
                choices = [
                    {"name": f"{i}. 📄 {name}", "value": name}
                    for i, name in enumerate(sorted(config_files), 1)
                ]

                selected = self.vt.console_select_menu(
                    choices=choices,
                    message="Available Data Sources Files:",
                    indent=1
                )

                filepath_cfg = Path(self.datasources_dir) / selected

            except KeyboardInterrupt:
                self.vt.console_message("caution", "Operation cancelled by user.")
                return
            
        # Load YAML configuration
        with open(filepath_cfg, 'r') as file:
            yaml_data = yaml.safe_load(file)
            data = yaml_data.get("dataex_datasources", {})

        # Parse each data source entry
        for source_name, source_info in data.items():
            try:
                data_class = source_info.pop('data_class')

                if data_class == 'FileLogDataSource':
                    if not quiet: self.vt.console_message("info", f"Loading FileLogDataSource config: {source_name}", indent=1)

                    log_path = global_vars.LOG_DIR / Path(source_info["filepath"])
                    if not log_path.is_file():
                        if not quiet: 
                            self.vt.console_message("error", f"Log file not found: {log_path}", indent=2)
                            self.vt.console_message("info", f"Creating log file: {log_path}", indent=2)
                        log_path.parent.mkdir(parents=True, exist_ok=True)
                        log_path.touch()

                    self.loaded_datasources.append({
                        "class": dsources.FileLogDataSource,
                        "name": source_name,
                        "args": {
                            "pattern": source_info["pattern"],
                            "filepath": str(log_path)
                        }
                    })
                    if not quiet: self.vt.console_message("success", f"Loaded FileLogDataSource config: {source_name}", indent=2)

                elif data_class == "PPSAnalyzerDataSource":
                    if not quiet: self.vt.console_message("info", f"Loading PPSAnalyzerDataSource config: {source_name}", indent=1)

                    self.loaded_datasources.append({
                        "class": dsources.PPSAnalyzerDataSource,
                        "name": source_name,
                        "args": {
                            "serial_port": source_info["serial_port"],
                            "pps_inputs": source_info["pps_inputs"],
                            "cable_delays": source_info["cable_delays"],
                        }
                    })
                    if not quiet: self.vt.console_message("success", f"Loaded PPSAnalyzerDataSource config: {source_name}", indent=2)

                else:
                    if not quiet: self.vt.console_message("error", f"Unknown Data Source: {data_class}", indent=1)

            except Exception as e:
                if not quiet: self.vt.console_message("error", f"Error loading {source_name} ({data_class}): {e}", indent=1)

        # Final confirmation
        if self.loaded_datasources:
            if not quiet: self.vt.console_message("success", f"Data Sources successfully loaded from {filepath_cfg}", indent=1)



# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: start_extraction
# ─────────────────────────────────────────────────────────────────────────────
    def start_extraction(
        self,
        suffix_out: Optional[str] = None,
        dir_out: Optional[str] = None,
        duration_out: Optional[int] = None,
        logger=None,
        extra_indent: int = 0
    ) -> None:
        """
        Start the data extraction process using the configured data sources.

        Launches a background writer process that collects metrics and stores them
        in a CSV file. A YAML summary file is also generated, containing metadata
        about the extraction session.

        ### Args
        - **suffix_out** (`Optional[str]`): Suffix for the output CSV file name. If `None`, the user is prompted.
        - **dir_out** (`Optional[str]`): Directory where output files will be saved. If `None`, defaults to the configured output directory.
        - **duration_out** (`Optional[int]`): Duration of the extraction in seconds. If `None`, the user is prompted.
        - **logger**: Optional logger instance for logging messages.
        - **extra_indent** (`int`): Additional indentation level for console messages.

        ### Notes
        - Prevents starting a new extraction if a writer process is already running.
        - Prompts the user interactively for missing parameters unless provided.
        - Automatically creates missing output directories and log files.
        - Saves extraction metadata to a YAML file alongside the CSV output.
        - Displays process details including PID, start time, duration, and assigned data sources.
        """

        # Prevent starting if a writer process is already running
        if self.writer_process.is_alive():
            self.vt.console_message(
                "caution",
                f"A writer process is already running with PID {self.writer_process.pid}.",
                indent=1,
                logger=logger
            )
            self.vt.console_message(
                "info",
                "To start a new extraction it is necessary to manually stop extraction from menu.",
                indent=1,
                logger=logger
            )
            return

        # Ensure data sources are loaded
        if not self.loaded_datasources:
            self.vt.console_message(
                "error",
                "No data sources registered. Cannot start extraction.",
                indent=1,
                logger=logger
            )
            return

        self.vt.console_message("title", "Starting extraction", "📈", logger=logger, indent=extra_indent)

        # Prompt user for suffix and duration if not provided
        if suffix_out is None:
            suffix: str = Prompt.ask("📁 Enter a suffix for the output CSV file", default="metrics")
            duration: int = IntPrompt.ask("⏱️ Enter duration in seconds", default=60)
        else:
            suffix = suffix_out
            duration = duration_out if duration_out is not None else 60

        # Update output directory if provided
        if dir_out is not None:
            self.output_dir = Path(dir_out)

        # Record start time and calculate planned end time
        self.start_time = time.time()
        start_time_hr = datetime.datetime.fromtimestamp(self.start_time).strftime("%d-%m-%Y %H:%M:%S")
        self.duration = duration
        planned_end_time = self.start_time + self.duration
        planned_end_time_hr = datetime.datetime.fromtimestamp(planned_end_time).strftime("%d-%m-%Y %H:%M:%S")

        # Create output file path with timestamp
        output_filepath = self.output_dir / f"{suffix}.csv"
        output_filepath.parent.mkdir(exist_ok=True, parents=True)
        self.output_filepath = str(output_filepath)

        # Prepare data source configurations for the writer process
        source_configs = [
            {
                "class": source["class"],
                "name": source["name"],
                "args": source["args"]
            }
            for source in self.loaded_datasources
        ]

        # Save extractor parameters to a YAML file
        extractor_output = {
            "datasources": {
                source["name"]: {
                    "args": source["args"]
                }
                for source in self.loaded_datasources
            },
            "duration": self.duration,
            "started_at": start_time_hr,
            "finished_at_planned": planned_end_time_hr
        }

        extractor_output_filepath = self.output_dir / f"{suffix}.yaml"
        with open(extractor_output_filepath, "w") as file:
            yaml.dump(extractor_output, file, sort_keys=False, default_flow_style=False, allow_unicode=True)

        # Launch the writer process
        self.writer_process = multiprocessing.Process(
            target=self.write_metrics,
            args=(output_filepath, extractor_output_filepath, duration, source_configs)
        )
        self.writer_process.start()

        # Display confirmation and process details
        self.vt.console_message("success", "DataEx launched successfully.", indent=1+extra_indent, logger=logger)
        self.vt.console_message("info", f"PID: {self.writer_process.pid} | Started at: {start_time_hr}", indent=2+extra_indent, logger=logger)
        self.vt.console_message("info", f"Duration: {self.duration} seconds", indent=2+extra_indent, logger=logger)
        self.vt.console_message("info", f"Data Sources assigned: {[s['name'] for s in source_configs]}", indent=2+extra_indent, logger=logger)

# ─────────────────────────────────────────────────────────────────────────────
# 🧪 Function: write_metrics
# ─────────────────────────────────────────────────────────────────────────────
    def write_metrics(
        self,
        output_filepath: Path,
        extractor_output_filepath: Path,
        duration: int,
        source_configs: List[Dict[str, Any]],
        logger=None,
        extra_indent: int = 0
    ) -> None:
        """
        Collect metrics from configured data sources and write them to a CSV file.

        Starts each data source in a separate thread and coordinates data collection
        through a shared queue. Metrics are timestamped and written to the output file.
        Upon completion, metadata is appended to a YAML summary file.

        ### Args
        - **output_filepath** (`Path`): Path to the output CSV file.
        - **extractor_output_filepath** (`Path`): Path to the YAML metadata file.
        - **duration** (`int`): Duration of the extraction process in seconds.
        - **source_configs** (`List[Dict[str, Any]]`): Configuration for each data source.
        - **logger**: Optional logger instance for logging messages.
        - **extra_indent** (`int`): Additional indentation level for console messages.

        ### Notes
        - Each data source runs in its own thread and pushes metrics to a shared queue.
        - The process ignores `SIGINT` to prevent interruption via keyboard.
        - Graceful termination is supported via `SIGTERM`.
        - Metadata including the stop time is appended to the YAML file after extraction ends.
        """
       
        # Ignore SIGINT to prevent interruption from keyboard
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        # Graceful termination handler
        def handle_signal(signum, frame):
            event.set()

        signal.signal(signal.SIGTERM, handle_signal)

        # Shared event and queue for thread coordination
        event = threading.Event()
        q: queue.Queue = queue.Queue(maxsize=1000)

        sources = []
        for config in source_configs:
            try:
                # Instantiate and start each data source thread
                source_class = config["class"]
                name = config["name"]
                args = config["args"]
                source = source_class(name, q, event, **args)
                source.start()
                sources.append(source)
            except Exception as e:
                self.vt.console_message(
                    "error",
                    f"[{name}] Error starting source: {e}",
                    indent=1 + extra_indent,
                    logger=logger
                )

        # Open CSV file and write header
        with output_filepath.open("w", newline="", buffering=1) as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "metric", "value"])

            try:
                # Collect data until duration expires or event is triggered
                t_end = time.time() + duration
                while time.time() < t_end and not event.is_set():
                    try:
                        timestamp, metric, value = q.get(timeout=1)
                        writer.writerow([timestamp, metric, value])
                    except queue.Empty:
                        continue  # No data available, continue waiting
            finally:
                # Signal all threads to stop
                event.set()
                for source in sources:
                    source.join()

                # Record stop time and append to YAML metadata
                self.stop_time = time.time()
                stop_time_hr = datetime.datetime.fromtimestamp(self.stop_time).strftime("%d-%m-%Y %H:%M:%S")

                extractor_output = {
                    "finished_at": stop_time_hr,
                }
                with extractor_output_filepath.open("a") as file:
                    yaml.dump(extractor_output, file, sort_keys=False, default_flow_style=False, allow_unicode=True)


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: stop_extraction
# ─────────────────────────────────────────────────────────────────────────────
    def stop_extraction(
        self,
        preconfirmation: Optional[bool] = False,
        logger=None,
        extra_indent: int = 0
    ) -> None:
        """
        Forcefully stops the active data extraction process and resets session metadata.

        If the writer process is running, this method optionally prompts the user for confirmation,
        terminates the process, and clears output-related session variables.

        ### Args:
        - **preconfirmation** (`Optional[bool]`): If `True`, skips the confirmation prompt. Defaults to `False`.
        - **logger**: Logger instance used for logging messages. Defaults to `None`.
        - **extra_indent** (`int`): Additional indentation level for console messages. Defaults to `0`.
        """


        # Display section title
        self.vt.console_message("title", "Stopping extraction", "🛑", logger=logger, indent=extra_indent)

        # Check if the writer process is running
        if not self.writer_process.is_alive():
            self.vt.console_message("info", "No DataEx running.", indent=1 + extra_indent, logger=logger)
            return

        # Ask user for confirmation before terminating the process
        if not preconfirmation:
            confirm: bool = Confirm.ask("⚠️ Are you sure you want to forcefully stop the extraction process?", default=True)
            if not confirm:
                self.vt.console_message("info", "Stop operation cancelled.", indent=1, logger=logger)
                return

        # Terminate the writer process if still alive
        if self.writer_process.is_alive():
            self.vt.console_message("clean", "Terminating writer process...", indent=1 + extra_indent, logger=logger)
            self.writer_process.terminate()
            self.writer_process.join()
            self.vt.console_message("success", "Writer process forcefully terminated.", indent=1 + extra_indent, logger=logger)
        else:
            self.vt.console_message("info", "Writer process is not running.", indent=1 + extra_indent, logger=logger)

        # Reset extraction session state
        self.output_filepath = None
        self.start_time = None
        self.duration = None


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: show_progress
# ─────────────────────────────────────────────────────────────────────────────
    def show_progress(self) -> None:
        """
        Displays a real-time progress indicator for the ongoing data extraction process.

        If the writer process is active, this method uses the view tools to render a progress bar
        based on the elapsed time since the extraction started.

        Console messages are shown if no extraction process is currently running.
        """

        # Display section title
        self.vt.console_message("title", "Showing progress", "⏳")

        # Check if extraction is active
        if not self.writer_process.is_alive():
            self.vt.console_message("caution", "No data extraction was started.", indent=1)
            return

        # Show real-time progress bar
        self.vt.real_time_progress(self.start_time, self.duration, "⏳ Extracting data...")


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: show_extracted_data
# ─────────────────────────────────────────────────────────────────────────────
    def show_extracted_data(self) -> None:
        """
        Streams the real-time log output of the data extraction process to the console.

        If the writer process is active, this method uses the view tools to display the contents
        of the output log file. Otherwise, it notifies the user that no process is running.
        """

        # Check if extraction is active
        if not self.writer_process.is_alive():
            self.vt.console_message("caution", "No data extraction was started.", indent=1)
            return

        # Stream the real-time log output
        log_path: Path = Path(self.output_filepath) if self.output_filepath else Path()
        self.vt.real_time_log(log_path)


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: exit
# ─────────────────────────────────────────────────────────────────────────────
    def exit(self) -> None:
        """
        Exits the TUI menu and performs cleanup operations.

        This method is intended to be called when the user chooses to exit the interface.
        It stops any active data extraction process and releases associated resources.
        """
  
        self.stop_extraction()