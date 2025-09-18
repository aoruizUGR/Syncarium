#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# exp_orchestra.py

**Project**: Syncarium – Intelligent Timing Platform Toolkit  
**Description**: Syncarium ExpOrchestra  
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada  
**Created**: 2025-06-27  
**Version**: 1.0.0  
**License**: GPLv3
"""


# ─────────────────────────────────────────────────────────────────────────────
# Standard Library Imports

import yaml
import time
import datetime
import threading
import logging
import hashlib
from pathlib import Path
from typing import List, Tuple, Callable, Optional, Any
from logging.handlers import RotatingFileHandler

# ─────────────────────────────────────────────────────────────────────────────
# Third-Party Imports
import requests

# ─────────────────────────────────────────────────────────────────────────────
# Local Application Imports
import syncarium.utils as utils
from syncarium.core import SyncCore, LoadGen, DataEx
import syncarium.options.global_vars as global_vars
import syncarium.options.telegram_vars as telegram_vars


# ─────────────────────────────────────────────────────────────
# ⚗️ ExpOrchestra Class
# ─────────────────────────────────────────────────────────────
class ExpOrchestra:
    """
    A tool for managing and executing laboratory experiments involving PTP synchronization,
    traffic generation, and data extraction.

    ### Attributes:
    - **vt** (`utils.ViewTools`): Utility tools for view-related operations.
    - **synccore** (`SyncCore`): Precision Time Protocol manager.
    - **loadgen** (`LoadGen`): Traffic generator manager.
    - **dataex** (`DataEx`): Data extractor tool instance.
    - **exp_dir** (`Path`): Path to the directory containing experiment definitions.
    - **output_dir** (`Path`): Path to the directory for storing experiment outputs.
    - **state** (`Any`): Current state of the experiment.
    - **fn** (`Optional[str]`): Name of the loaded experiment file.
    - **duration** (`Optional[int]`): Total duration of the experiment.
    - **stl_start** (`Optional[float]`): Start timestamp of the STL process.
    - **stl_duration** (`Optional[int]`): Duration of the STL process.
    - **dataex_start** (`Optional[float]`): Start timestamp of the data extractor.
    - **dataex_duration** (`Optional[int]`): Duration of the data extractor.
    - **synccore_start** (`Optional[float]`): Start timestamp of the PTP process.
    - **synccore_stop_at_end** (`Optional[bool]`): Whether to stop PTP at the end of the experiment.
    - **hash_id** (`Optional[str]`): Unique identifier for the experiment.
    - **start_ts** (`Optional[float]`): Timestamp when the experiment starts.
    - **exp_output_dir** (`Optional[Path]`): Path to the specific output directory for the experiment.
    - **logger** (`Any`): Logger instance for logging experiment events.
    - **output_log** (`Optional[Path]`): Path to the output log file.
    - **output_yaml** (`Optional[Path]`): Path to the output YAML file.
    - **stl_fn** (`Optional[str]`): Name of the STL script file.
    - **dataex_datasources** (`Any`): Data sources used by the extractor.
    - **synccore_clients** (`Any`): PTP clients involved in the experiment.
    - **telegram_bot_token** (`str`): Telegram bot token used for sending notifications.
    - **telegram_chat_id** (`str`): Telegram chat ID used for sending notifications.
    - **thread** (`Optional[threading.Thread]`): Thread handling the experiment execution.
    - **batch_thread** (`Optional[threading.Thread]`): Thread handling batch execution.
    - **stop_event** (`threading.Event`): Event used to signal experiment interruption.
    - **total_repetitions** (`Optional[int]`): Total number of repetitions in batch mode.
    - **actual_repetition** (`Optional[int]`): Current repetition number in batch mode.
    - **delay_between** (`Optional[int]`): Delay in seconds between repetitions.
    """

# ─────────────────────────────────────────────────────────────────────────────
# 🚧 Function: constructor
# ─────────────────────────────────────────────────────────────────────────────
    def __init__(
        self,
        synccore: SyncCore,
        loadgen: LoadGen,
        dataex: DataEx,
        vt: utils.ViewTools
    ) -> None:
        """
        Initializes the ExpOrchestra with the required components for experiment execution.

        Sets up references to the PTP manager, traffic generator, data extractor, and view tools.
        Also initializes internal state variables, directory paths, logging configuration,
        and timing metadata for managing experiment lifecycle.

        ### Args:
        - **synccore** (`SyncCore`): Instance responsible for managing PTP synchronization.
        - **loadgen** (`LoadGen`): Instance responsible for traffic generation.
        - **dataex** (`DataEx`): Instance responsible for extracting experiment data.
        - **vt** (`utils.ViewTools`): Utility tools for rendering views in the console.
        """


        # Store tool instances
        self.vt: utils.ViewTools = vt
        self.synccore: SyncCore = synccore
        self.loadgen: LoadGen = loadgen
        self.dataex: DataEx = dataex

        # Experiment metadata
        self.fn: Optional[str] = None
        self.hash_id: Optional[str] = None
        self.start_ts: Optional[float] = None
        self.duration: Optional[int] = None
        self.state: Any = None
        self.thread: threading.Thread | None = None
        self.batch_thread: threading.Thread | None = None
        self.stop_event: threading.Event = threading.Event()

        # Directory paths
        self.exp_dir: Path = global_vars.EXPERIMENTS_DIR
        self.output_dir: Path = global_vars.OUTPUT_DIR
        self.exp_output_dir: Optional[Path] = None

        # Logging
        self.logger: Any = None
        self.output_log: Optional[Path] = None
        self.output_yaml: Optional[Path] = None

        # Experiment components
        self.stl_fn: Optional[str] = None
        self.dataex_datasources: Any = None
        self.synccore_clients: Any = None

        # Timing information
        self.stl_start: Optional[float] = None
        self.stl_duration: Optional[int] = None
        self.dataex_start: Optional[float] = None
        self.dataex_duration: Optional[int] = None
        self.synccore_start: Optional[float] = None
        self.synccore_stop_at_end: Optional[bool] = None

        # Batch information
        self.total_repetitions: Optional[int] = None
        self.actual_repetition: Optional[int] = None
        self.delay_between: Optional[int] = None

        # Telegram notification setup
        self.telegram_bot_token: str = telegram_vars.TELEGRAM_BOT_TOKEN
        self.telegram_chat_id: str = telegram_vars.TELEGRAM_CHAT_ID


# ─────────────────────────────────────────────────────────────────────────────
# 📋 Function: main_menu
# ─────────────────────────────────────────────────────────────────────────────
    def main_menu(self) -> None:
        """
        Displays and manages the interactive ExpOrchestra menu.

        Continuously renders a terminal-based menu using `ViewTools`, allowing the user to manage
        the experiment lifecycle, including PTP synchronization, STL traffic generation, and data extraction.

        The loop runs until the user selects **"❌ Exit"** or interrupts with **Ctrl+C**.

        ### Menu Options:
        - ⚗️ Load Experiment → `load_experiment`
        - ⚗️ Launch Experiment → `launch_experiment_bg`
        - 🏭 Launch Experiment Batch → `launch_experiment_batch`
        - 🛑⚗️ Stop Experiment → `stop_experiment`
        - 🛑🏭 Stop Experiment Batch → `stop_experiment_batch`
        - ⏳ Show Progress → `show_progress`
        - 📄 Show Experiment Status → `show_experiment`
        - 📄 Show Extracted Data → `show_extracted_data`
        - 🔄 Refresh View → Refreshes the current view without taking action
        - ❌ Exit → Exits the menu
        """
       
        try:
            # Ensure traffic generator is selected before proceeding
            if not self.loadgen.loadgen_name:
                self.loadgen.select_load_gen()

            while True:
                # Display software title and main menu header
                self.vt.console_software_title(delay=0)
                self.vt.console_message("main_title", "ExpOrchestra Menu", "⚗️")

                # Show current PTP processes
                self.vt.table_synccore_processes()

                # Show current STL process status
                self.vt.table_stl_program(
                    self.loadgen.stl_process,
                    self.loadgen.stl_filename,
                    self.loadgen.stl_args,
                    self.loadgen.stl_start_time,
                    self.loadgen.stl_duration,
                    self.loadgen.stl_state
                )

                # Show current data extractor status
                self.vt.table_data_extractor(
                    self.dataex.writer_process,
                    self.dataex.loaded_datasources,
                    self.dataex.output_filepath,
                    self.dataex.start_time,
                    self.dataex.duration
                )

                # Show last collected metric
                self.vt.table_last_metric()

                # Show current experiment status
                self.vt.table_experiment(
                    self.fn,
                    self.state,
                    self.hash_id,
                    self.duration,
                    self.start_ts,
                    self.synccore_clients,
                    self.synccore_start,
                    self.stl_fn,
                    self.stl_start,
                    self.dataex_datasources,
                    self.dataex_start
                )

                # Display interactive menu and get user choice
                choice: str = self.vt.console_select_menu(
                    choices=[
                        {"name": "⚗️ Load Experiment", "value": "load_experiment"},
                        {"name": "⚗️ Launch Experiment", "value": "launch_experiment"},
                        {"name": "🏭 Launch Experiment Batch", "value": "launch_experiment_batch"},
                        {"name": "🛑⚗️ Stop Experiment", "value": "stop_experiment"},
                        {"name": "🛑🏭 Stop Experiment Batch", "value": "stop_experiment_batch"},
                        {"name": "⏳ Show Progress", "value": "show_progress"},
                        {"name": "📄 Show Experiment Status", "value": "show_experiment"},
                        {"name": "📄 Show Extracted Data", "value": "show_extracted_data"},
                        {"name": "🔄 Refresh view", "value": "refresh_view"},
                        {"name": "❌ Exit", "value": "exit"},
                    ],
                    indent=1
                )

                # Map menu options to corresponding methods
                submenu: dict[str, Callable[[], None]] = {
                    "load_experiment":              self.load_experiment,
                    "launch_experiment":            self.launch_experiment_bg,
                    "launch_experiment_batch":      self.launch_experiment_batch,
                    "stop_experiment":              self.stop_experiment,
                    "stop_experiment_batch":        self.stop_experiment_batch,
                    "show_progress":                self.show_progress,
                    "show_experiment":              self.show_experiment,
                    "show_extracted_data":          self.show_extracted_data,
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
# 📌 Function: load_experiment
# ─────────────────────────────────────────────────────────────────────────────
    def load_experiment(self, file_cfg: Optional[Path] = None, quiet: bool = False) -> None:
        """
        Loads an experiment configuration from a YAML file and initializes its components.

        If no file is provided, prompts the user to select one from the available YAML files
        in the configuration directory. Parses the file to extract metadata, timing parameters,
        and component configurations for traffic generation, data extraction, and PTP synchronization.

        ### Args:
        - **file_cfg** (`Optional[str]`): Name of the YAML configuration file. If `None`, the user is prompted to select one.
        - **quiet** (`bool`): If `True`, suppresses console output. Defaults to `False`.
        """

        # Display section title
        if not quiet: self.vt.console_message("title", "Loading Experiment", "⚗️")

        # Clear previously loaded experiment data
        self.clean_experiment()

        if file_cfg:
            # Use provided filename directly
            filepath_cfg: Path = Path(self.exp_dir) / file_cfg
            
        else:
            # List YAML files in the experiment directory
            files: list[str] = [
                str(f.relative_to(self.exp_dir))
                for f in self.exp_dir.rglob("*.yaml")
                if f.is_file()
            ]

            # Notify if no experiment files are found
            if not files:
                self.vt.console_message("error", f"No data sources files found in '{self.exp_dir}'.", indent=1)
                return

            try:
                # Build selection menu for available experiment files
                choices = [
                    {"name": f"{i}. 📄 {name}", "value": name}
                    for i, name in enumerate(sorted(files), 1)
                ]

                selected: str = self.vt.console_select_menu(
                    choices=choices,
                    message="Available Experiments:",
                    indent=1
                )

                # Get full path of the selected file
                filepath_cfg: Path = self.exp_dir / selected

            except KeyboardInterrupt:
                # Handle user cancellation
                self.vt.console_message("caution", "Operation cancelled by user.")
                return

        try:
            # Load YAML content from the selected file
            with filepath_cfg.open('r') as file:
                data: dict = yaml.safe_load(file)

                # Load experiment metadata
                self.fn = filepath_cfg.stem
                self.fn_relative_path = filepath_cfg.relative_to(self.exp_dir)
                self.fn_absolute_path = Path(filepath_cfg).resolve()
                self.hash_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:4]
                self.start_ts = None
                self.duration = int(data.get("total_duration"))
                self.state = "Loaded"

                # Prepare output directories
                relative_folder = filepath_cfg.parent.relative_to(self.exp_dir)
                self.exp_output_dir = self.output_dir / relative_folder / self.fn
                self.exp_output_dir.mkdir(parents=True, exist_ok=True)

                # Prepare output file paths
                self.output_log = self.exp_output_dir / f"{self.fn}_{self.hash_id}.log"
                self.output_yaml = (self.exp_output_dir / f"{self.fn}_{self.hash_id}.yaml").resolve()

                # Load configuration values
                self.stl_fn = data.get("loadgen_stl_program")
                self.dataex_datasources = list(data.get("dataex_datasources", {}).keys())
                self.synccore_clients = list(data.get("synccore_clients", {}).keys())

                # Load start times and durations
                self.stl_start = int(data.get("loadgen_stl_start"))
                self.stl_duration = self.duration - 60
                self.dataex_start = int(data.get("dataex_start"))
                self.dataex_duration = self.duration - self.dataex_start
                self.synccore_start = int(data.get("synccore_start"))
                self.synccore_stop_at_end = bool(data.get("synccore_stop_at_end"))

                # If PTP enabled, kill actual clients and load new PTP clients
                if self.synccore_start != -1:
                    self.synccore.stop_ptp(preconfirmation=True, quiet=True)
                    self.synccore.load_clients(file_cfg=self.fn_absolute_path, logger=self.logger, extra_indent=1, quiet=True)

                # Load datasources
                self.dataex.load_datasources(file_cfg=self.fn_absolute_path, quiet = True)

                # Display experiment summary
                if not quiet: 
                    self.vt.console_message("success", "Experiment loaded successfully.", indent=1)
                    self.vt.console_message("info", f"Experiment Name: {self.fn}", indent=2)
                    self.vt.console_message("info", f"dataex Datasources: {self.dataex_datasources} | Starting at: {str(datetime.timedelta(seconds=self.dataex_start))}", indent=2)
                    if self.synccore_start != -1:
                        self.vt.console_message("info", f"PTP Clients: {self.synccore_clients} | Starting at: {str(datetime.timedelta(seconds=self.synccore_start))}", indent=2)
                    if self.stl_start != -1:
                        self.vt.console_message("info", f"STL Program: {self.stl_fn} | Starting at: {str(datetime.timedelta(seconds=self.stl_start))}", indent=2)
                    self.vt.console_message("info", f"Total duration: {int(self.duration / 60)} min | Data duration: {int(self.dataex_duration / 60)} min", indent=2)

        except Exception as e:
            # Handle errors during file reading or parsing
            self.vt.console_message("error", f"Error reading YAML file: {e}", indent=1)
            self.clean_experiment()

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: interrupted_sleep
# ─────────────────────────────────────────────────────────────────────────────
    def interrupted_sleep(self, seconds: float, stop_event: threading.Event) -> None:
        """
        Sleeps in small intervals to allow interruption via a stop event.

        This method is useful for long-running operations that need to be interruptible,
        such as experiment delays or scheduled actions.

        ### Args:
        - **seconds** (`float`): Total duration to sleep.
        - **stop_event** (`threading.Event`): Event used to interrupt the sleep early.
        """

        interval: float = 0.5
        elapsed: float = 0.0
        while elapsed < seconds:
            if stop_event.is_set():
                break
            time.sleep(min(interval, seconds - elapsed))
            elapsed += interval

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: launch_experiment_bg
# ─────────────────────────────────────────────────────────────────────────────
    def launch_experiment_bg(self, quiet: bool = False) -> None:
        """
        Starts the experiment in a background thread and sets up logging.

        Initializes a timestamped logger with a rotating file handler, then launches
        the experiment asynchronously using a daemon thread. Any exceptions during
        execution are logged automatically.


        """
        if self.state != "Loaded":
            self.vt.console_message("error", "Experiment not loaded")
            return

        # Notify user that experiment is starting
        if not quiet: self.vt.console_message("title", "Starting Experiment", "⚗️")

        # Create and configure logger
        timestamp: str = time.strftime('%d-%m-%Y_%H:%M:%S')
        self.logger = logging.getLogger(f"experiment_logger_{timestamp}")
        self.logger.setLevel(logging.DEBUG)

        # Add rotating file handler if not already present
        if not self.logger.handlers:
            handler = RotatingFileHandler(self.output_log, maxBytes=5_000_000, backupCount=3)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        def thread_target() -> None:
            """
            Target function for the background thread.
            Executes the experiment and logs any exceptions.
            """
            try:
                self.launch_experiment()
            except Exception:
                self.logger.exception("Experiment failed with an exception")

        # Launch the experiment in a background thread
        self.stop_event.clear()
        self.thread = threading.Thread(target=thread_target, daemon=True)
        self.thread.start()

        # Notify user that logging has started
        if not quiet: self.vt.console_message("success", f"Experiment logging saving in {self.output_log}")

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: launch_experiment_bg
# ─────────────────────────────────────────────────────────────────────────────
    def launch_experiment(self, quiet: bool = False) -> None:
        """
        Starts the experiment asynchronously in a background thread and sets up logging.

        Initializes a timestamped logger with a rotating file handler to capture experiment logs.
        Then launches the experiment in a daemon thread, allowing it to run in the background.
        Any exceptions raised during execution are automatically logged.

        ### Args:
        - **quiet** (`bool`): If `True`, suppresses console output. Defaults to `False`.
        """

        # Display experiment start message
        self.vt.console_message("title", "Starting Experiment", "⚗️", logger=self.logger)

        # Ensure an experiment is loaded before proceeding
        if self.state != "Loaded":
            self.vt.console_message("error", "No experiment loaded. Please load an experiment first.", indent=1, logger=self.logger)
            return

        # Notify via Telegram
        self.notify_telegram_bot(message=f"⚗️ Starting Experiment {self.fn} with ID {self.hash_id}")

        # Update internal state and record start time
        self.state = "Running"
        start_time: float = time.time()
        self.start_ts = start_time

        # Define tasks with their scheduled start times
        tasks: List[Tuple[int, Callable[[], None], str]] = [
            (
                self.dataex_start,
                lambda: self.dataex.start_extraction(
                    suffix_out=f"{self.fn}_{self.hash_id}",
                    dir_out=self.exp_output_dir,
                    duration_out=self.dataex_duration,
                    logger=self.logger,
                    extra_indent=1
                ),
                "dataex"
            )
        ]

        # Include PTP task if configured
        if self.synccore_start != -1:
            tasks.append((
                self.synccore_start,
                lambda: self.synccore.start_ptp(
                    logger=self.logger,
                    extra_indent=1,
                    stop = False
                ),
                "PTP"
            ))

        # Include STL task if configured
        if self.stl_start != -1:
            tasks.append((
                self.stl_start,
                lambda: self.loadgen.start_stl_program(
                    self.fn_absolute_path,
                    self.stl_duration,
                    self.output_yaml,
                    logger=self.logger,
                    extra_indent=1
                ),
                "STL"
            ))

        # Sort tasks by their scheduled start time
        tasks.sort(key=lambda x: x[0])

        # Execute tasks sequentially with appropriate delays
        for delay, func, name in tasks:
            now: float = time.time()
            wait_time: float = delay - (now - start_time)
            if wait_time > 0:
                self.vt.console_message("info", f"Waiting {int(wait_time)}s to start {name}...", indent=1, logger=self.logger)
                self.interrupted_sleep(wait_time, self.stop_event)
            
            if self.stop_event.is_set():
                self.vt.console_message("caution", f"Experiment interrupted before launching {name}.", logger=self.logger)
                break

            self.vt.console_message("info", f"Launching {name}...", indent=1, logger=self.logger)
            try:
                func()
            except Exception as e:
                self.vt.console_message("error", f"Error launching {name}: {e}", indent=1, logger=self.logger)

        if not self.stop_event.is_set():
            # Notify user of experiment duration
            self.vt.console_message("info", f"Experiment will run for {int(self.dataex_duration)} seconds.", indent=1, logger=self.logger)

        # Wait for the experiment to complete
        remaining: float = self.duration - (time.time() - start_time)
        if remaining > 0:
            self.interrupted_sleep(remaining, self.stop_event)
        
        # Finalize experiment
        if self.stop_event.is_set():
            self.interrupted_sleep(10, self.stop_event)
            self.vt.console_message("caution", "Experiment stopped.", logger=self.logger)
            self.state = "Stopped"
            # Notify Telegram
            self.notify_telegram_bot(message=f"⚠️ Stopped Experiment {self.fn} with ID {self.hash_id}")

        else: 
            self.vt.console_message("success", "Experiment completed.", logger=self.logger)
            self.vt.console_message("info", "Waiting 10 seconds for finish.", logger=self.logger)
            self.state = "Finished"
            # Stop PTP if configured to do so
            if self.synccore_stop_at_end is True:
                self.synccore.stop_ptp(preconfirmation=True,logger=self.logger)
            # Notify Telegram
            self.notify_telegram_bot(message=f"✅ Finished Experiment {self.fn} with ID {self.hash_id}")
        
        # Actualize batch info
        if self.total_repetitions:
            # Notify via Telegram
            self.notify_telegram_bot(message=f"🏭 Repetition number {self.actual_repetition}/{self.total_repetitions} of the experiment {self.fn} completed.")
            self.actual_repetition = self.actual_repetition + 1
        
            if self.actual_repetition == self.total_repetitions + 1:
                self.notify_telegram_bot(message=f"🏭 Batch of the experiment {self.fn} completed.")
                self.actual_repetition = None
                self.total_repetitions = None


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: launch_experiment_batch
# ─────────────────────────────────────────────────────────────────────────────
    def launch_experiment_batch(self) -> None:
        """
        Prompts the user to select an experiment and launches it multiple times in the background.

        For each repetition, the experiment is reloaded to regenerate a unique ID and output paths.
        A delay is applied between each execution. The batch runs asynchronously in a daemon thread
        and can be interrupted via `stop_event`.

        The user is prompted to configure:
        - Number of repetitions
        - Delay between repetitions (in seconds)
        """

        # Ask user for number of repetitions and delay
        self.vt.console_message("title", "Batch Configuration", "⚙️")

        files: list[str] = [
            str(f.relative_to(self.exp_dir))
            for f in self.exp_dir.rglob("*.yaml")
            if f.is_file()
        ]
        if not files:
            self.vt.console_message("error", f"No experiment files found in '{self.exp_dir}'.", indent=1)
            return
        try:
            choices = [{"name": f"{i}. 📄 {name}", "value": name} for i, name in enumerate(sorted(files), 1)]
            selected: str = self.vt.console_select_menu(
                choices=choices,
                message="Available Experiments:",
                indent=1
            )
            filepath_cfg: Path = selected
        except KeyboardInterrupt:
            self.vt.console_message("caution", "Operation cancelled by user.")
            return
        
        self.total_repetitions: int = int(self.vt.console.input("Enter number of repetitions:"))
        self.delay_between: int = int(self.vt.console.input("Enter delay between experiments (in seconds):"))
        self.actual_repetition = 1

        self.vt.console_message("success", f"Batch of {self.total_repetitions} repetitions for experiment {selected} launched.")
        
        # Notify via Telegram
        self.notify_telegram_bot(message=f"🏭 Starting a batch of the experiment {selected}, {self.total_repetitions} repetitions and {self.delay_between} seconds between experiments.")
        
        def batch_runner(stop_event: threading.Event) -> None:
            for i in range(self.total_repetitions):
                if stop_event.is_set():
                    break

                self.clean_experiment(quiet=True)
                if stop_event.is_set():
                    break

                self.load_experiment(filepath_cfg, quiet=True)
                if stop_event.is_set():
                    break

                self.launch_experiment_bg(quiet=True)
                if stop_event.is_set():
                    break

                if i < self.total_repetitions - 1:
                    for _ in range(int(self.duration + self.delay_between)):
                        if stop_event.is_set():
                            break
                        time.sleep(1)

        self.batch_thread = threading.Thread(target=lambda: batch_runner(self.stop_event), daemon=True)
        self.batch_thread.start()

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: stop_experiment
# ─────────────────────────────────────────────────────────────────────────────
    def stop_experiment(self, extra_indent: int = 0) -> None:
        """
        Stops all components of a running experiment and updates its state.

        Attempts to stop PTP synchronization, data extraction, and STL traffic generation
        if they were configured. Any errors encountered during shutdown are reported.
        The experiment state is updated to `"Stopped"` once all components are terminated.

        ### Args:
        - **extra_indent** (`int`): Indentation level for console messages. Defaults to `0`.
        """

        # Display section title
        self.vt.console_message("title", "Stopping/Cleaning Experiment", "🛑", indent=extra_indent, logger=self.logger)
        self.vt.console_message("title", "Stopping/Cleaning Experiment", "🛑", indent=extra_indent)


        # Check if an experiment is currently running
        if self.state != "Running":
            self.vt.console_message("warning", "No experiment is currently running.", indent=1)
            return

        errors: List[str] = []
        self.stop_event.set()

        # Attempt to stop PTP component if it was configured
        if self.synccore_start != -1:
            try:
                self.synccore.stop_ptp(preconfirmation=True, logger=self.logger, extra_indent=1)
            except Exception as e:
                errors.append(f"PTP: {e}")

        # Attempt to stop dataex component
        try:
            self.dataex.stop_extraction(preconfirmation=True, logger=self.logger, extra_indent=1)
        except Exception as e:
            errors.append(f"dataex: {e}")

        # Attempt to stop STL component if it was configured
        if self.stl_start != -1:
            try:
                self.loadgen.stop_stl_program(logger=self.logger, extra_indent=1, preconfirmation=True)
            except Exception as e:
                errors.append(f"STL: {e}")

        # Report any errors encountered during shutdown
        if errors:
            for err in errors:
                self.vt.console_message("error", f"Error stopping component: {err}", indent=1, logger=self.logger)
                self.vt.console_message("error", f"Error stopping component: {err}", indent=1)
                return
            
        # Update experiment state
        self.thread.join(timeout=5)
        self.state = "Stopped"
        self.vt.console_message("success", "All experiment components stopped successfully.", logger=self.logger)
        self.vt.console_message("success", "All experiment components stopped successfully.", indent=extra_indent)

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: stop_experiment_batch
# ─────────────────────────────────────────────────────────────────────────────
    def stop_experiment_batch(self, extra_indent: int = 0) -> None:
        """
        Stops all running experiments in the current batch.

        Signals the stop event to interrupt any ongoing or scheduled experiment launches.
        Also calls `stop_experiment()` to clean up the currently running experiment, and
        waits for the batch thread to finish execution.

        A Telegram notification is sent to indicate the batch was stopped.

        ### Args:
        - **extra_indent** (`int`): Indentation level for console messages. Defaults to `0`.
        """

        # Signal to stop all threads
        self.stop_event.set()

        # Stop the currently running experiment
        self.stop_experiment(extra_indent=extra_indent)

        self.vt.console_message("title", "Stopping Experiment Batch", "🛑", indent=extra_indent)
        
        # Stop entire batch
        self.batch_thread.join()

        self.vt.console_message("success", "Batch stop signal sent.", indent=extra_indent)

        # Notify via Telegram
        self.notify_telegram_bot(message=f"🏭 Batch of the experiment {self.fn} stopped at {self.actual_repetition}/{self.total_repetitions}.")


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: show_progress
# ─────────────────────────────────────────────────────────────────────────────
    def show_progress(self) -> None:
        """
        Displays real-time progress of the experiment.

        Console messages are used to notify the user if no experiment is running.
        """
        # Display section title
        self.vt.console_message("title", "Showing progress", "⏳")

        # Check if an experiment has been started
        if not self.fn:
            self.vt.console_message("caution", "No data extraction was started.", indent=1)
            return

        # Show real-time progress bar
        if self.state == "Running":
            self.vt.real_time_progress(self.start_ts, self.duration, "⏳ Experiment running...", repetition_info= f"{self.actual_repetition}/{self.total_repetitions}")


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: show_experiment
# ─────────────────────────────────────────────────────────────────────────────
    def show_experiment(self) -> None:
        """
        Displays the real-time log output of the experiment.

        If no experiment is currently running, a warning message is shown.
        Otherwise, the log file is streamed live in the console.
        """

        # Check if experiment is running
        if self.state != "Running":
            self.vt.console_message("caution", "No experiment was started.", indent=1)
            return

        # Stream the real-time log output
        log_path: Path = self.output_log
        self.vt.real_time_log(log_path)


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: show_extracted_data
# ─────────────────────────────────────────────────────────────────────────────
    def show_extracted_data(self) -> None:
        """
        Displays the real-time log output of the data extraction process.

        If no data extraction process is active, a warning message is shown.
        Otherwise, the log file is streamed live in the console.
        """

        # Check if data extraction process is alive
        if not self.dataex.writer_process.is_alive():
            self.vt.console_message("caution", "No data extraction was started.", indent=1)
            return

        # Stream the real-time log output
        log_path: Path = self.dataex.output_filepath
        self.vt.real_time_log(log_path)


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: clean_experiment
# ─────────────────────────────────────────────────────────────────────────────
    def clean_experiment(self, quiet: bool = False) -> None:
        """
        Resets all internal variables and clears the previously loaded experiment.

        This method resets experiment metadata, output paths, logging configuration,
        and component-specific parameters to prepare the tool for a new experiment.

        ### Args:
        - **quiet** (`bool`): If `True`, suppresses console output. Defaults to `False`.
        """

        if self.fn:
            if not quiet: self.vt.console_message("clean", "Deleting previous experiment...")

            # Reset experiment metadata and state
            self.fn = None
            self.state = None
            self.hash_id = None
            self.start_ts = None
            self.duration = None

            # Reset logging and output paths
            self.logger = None
            self.exp_output_dir = None
            self.output_log = None
            self.output_yaml = None

            # Reset component configuration
            self.stl_fn = None
            self.stl_start = None
            self.stl_duration = None
            self.dataex_datasources = None
            self.dataex_start = None
            self.dataex_duration = None
            self.synccore_clients = None
            self.synccore_start = None
            self.synccore_stop_at_end = None
            
            # Notify user
            if not quiet: self.vt.console_message("success", "Laboratory cleaned.", indent=1)


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: notify_telegram_bot
# ─────────────────────────────────────────────────────────────────────────────
    def notify_telegram_bot(self, message: str) -> None:
        """
        Sends a message to the configured Telegram bot.

        Constructs and sends a POST request to the Telegram Bot API using the stored
        bot token and chat ID. If the request fails, an error message is shown in the console.

        ### Args:
        - **message** (`str`): Text message to send via Telegram.
        """

        if self.telegram_bot_token:
            url: str = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data: dict[str, str] = {
                "chat_id": self.telegram_chat_id,
                "text": message
            }

            response = requests.post(url, data=data)

            # Handle failed request
            if response.status_code != 200:
                self.vt.console_message("error", f"Error sending message: {response.text}")

