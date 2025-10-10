#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# exp_orchestra.py

**Project**: Syncarium - Intelligent Timing Platform Toolkit  
**Description**: Syncarium ExpOrchestra  
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada  
**Created**: 2025-06-27  
**Version**: 1.1.0  
**License**: GPLv3
"""


# ─────────────────────────────────────────────────────────────────────────────
# Standard Library Imports
import time
import datetime
import threading
import logging
from pathlib import Path
from typing import List, Tuple, Callable, Optional, Any, Deque
from logging.handlers import RotatingFileHandler
from collections import deque

# ─────────────────────────────────────────────────────────────────────────────
# Third-Party Imports
# (None used directly in this file)

# ─────────────────────────────────────────────────────────────────────────────
# Local Application Imports
import syncarium.utils as utils
import syncarium.options.global_vars as global_vars
from syncarium.core import SyncCore, LoadGen, DataEx, Experiment

# ─────────────────────────────────────────────────────────────
# 🏭 ExpOrchestra Class
# ─────────────────────────────────────────────────────────────
class ExpOrchestra:


# ─────────────────────────────────────────────────────────────────────────────
# 🚧 Function: constructor
# ─────────────────────────────────────────────────────────────────────────────
    def __init__(
        self,
        synccore: SyncCore,
        loadgen: LoadGen,
        dataex: DataEx,
        vt: utils.ViewTools,
        telegram_bot: utils.TelegramBot
    ) -> None:
        """
        Initializes the ExpOrchestra with the required components for experiment execution.

        Sets up references to the PTP manager, traffic generator, data extractor, and view tools.
        Also initializes internal current_state variables, directory paths, logging configuration,
        and timing metadata for managing experiment lifecycle.

        ### Args:
        - **synccore** (`SyncCore`): Instance responsible for managing PTP synchronization.
        - **loadgen** (`LoadGen`): Instance responsible for traffic generation.
        - **dataex** (`DataEx`): Instance responsible for extracting experiment data.
        - **vt** (`utils.ViewTools`): Utility tools for rendering views in the console.
        """

        # Store tool instances
        self.vt: utils.ViewTools = vt
        self.telegram_bot: utils.TelegramBot = telegram_bot
        self.synccore: SyncCore = synccore
        self.loadgen: LoadGen = loadgen
        self.dataex: DataEx = dataex

        # Queue instance
        self.queue: Deque[Experiment] = deque()

        # Current experiment metadata
        self.current_experiment: Experiment = None

        # Thread-related constrains
        self.thread: threading.Thread | None = None
        self.stop_event: threading.Event = threading.Event()
        self.logger: Any = None
        self.intergap_delay: Optional[int] = None        

        # Directory paths
        self.exp_dir: Path = global_vars.EXPERIMENTS_DIR


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

                # Show experiment queue
                self.vt.table_experiment_queue(
                    self.queue
                )

                # Display interactive menu and get user choice
                choice: str = self.vt.console_select_menu(
                    choices=[
                        {"name": "🧪 Add Experiment to Queue", "value": "add_experiment_queue"},
                        {"name": "🗑️ Remove Experiment from Queue", "value": "remove_experiment_queue"},
                        {"name": "▶️🧪 Start One Queue Experiment", "value": "launch_first_experiment"},
                        {"name": "🛑🧪 Stop Current Experiment", "value": "stop_current_experiment"},
                        {"name": "▶️🏭 Start Whole Queue", "value": "launch_whole_queue"},
                        {"name": "🛑🏭 Stop Whole Queue", "value": "stop_whole_queue"},
                        {"name": "⏳ Show Progress", "value": "show_progress"},
                        {"name": "📄 Show Current Experiment Log", "value": "show_current_experiment_log"},
                        {"name": "📄 Show Current Experiment Data", "value": "show_current_experiment_data"},
                        {"name": "🔄 Refresh view", "value": "refresh_view"},
                        {"name": "❌ Exit", "value": "exit"},
                    ],
                    indent=1
                )

                # Map menu options to corresponding methods
                submenu: dict[str, Callable[[], None]] = {
                    "add_experiment_queue":         self.add_experiment_queue,
                    "remove_experiment_queue":      self.remove_experiment_queue,
                    "launch_first_experiment":      self.launch_first_experiment,
                    "stop_current_experiment":      self.stop_current_experiment,
                    "launch_whole_queue":           self.launch_whole_queue,
                    "stop_whole_queue":             self.stop_whole_queue,
                    "show_progress":                self.show_progress,
                    "show_current_experiment_log":  self.show_current_experiment_log,
                    "show_current_experiment_data": self.show_current_experiment_data,
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
# 📌 Function: add_experiment_queue
# ─────────────────────────────────────────────────────────────────────────────
    def add_experiment_queue(self, file_cfg: Optional[Path] = None, quiet: bool = False) -> None:

        # Display section title
        if not quiet: self.vt.console_message("title", "Adding Experiment", "🧪")

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
                self.vt.console_message("error", f"No experiments found in '{self.exp_dir}'.", indent=1)
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
           
            repetitions = int(self.vt.console.input("Enter number of repetitions:"))
            for _ in range(repetitions):
                experiment = Experiment(file_cfg=filepath_cfg)
                self.queue.append(experiment)
                            
            self.vt.console_message("info", f"Experiment {filepath_cfg} added {repetitions} times to the experiment queue.")

        except Exception as e:
            # Handle errors during file reading or parsing
            self.vt.console_message("error", f"Error adding experiment: {e}", indent=1)

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: remove_experiment_queue
# ─────────────────────────────────────────────────────────────────────────────
    def remove_experiment_queue(self) -> None:
        if not self.queue:
            self.vt.console_message("error", f"The experiment queue is empty.")
            return 
        
        choices = [{"name": f"{i}. Experiment with HashID {obj.hash_id}", "value": obj} for i, obj in enumerate(self.queue, 1)]
        selected = self.vt.console_select_menu(
            choices=choices,
            message="Available queued experiments:",
            indent=1
        )

        self.queue.remove(selected)
        self.vt.console_message("success", f"Experiment {selected} removed from queue.", indent=1)

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
# 📌 Function: launch_first_experiment
# ─────────────────────────────────────────────────────────────────────────────
    def launch_first_experiment(self, quiet: bool = False) -> None:
        """
        Starts an experiment in a background thread and sets up logging.

        Initializes a timestamped logger with a rotating file handler, then launches
        the experiment asynchronously using a daemon thread. Any exceptions during
        execution are logged automatically.

        """
        if len(self.queue) == 0:
            self.vt.console_message("error", "No experiments in the queue.")
            return

        # Notify user that experiment is starting
        if not quiet: self.vt.console_message("title", "Starting First Experiment of the queue.", "🧪")

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
                self.launch_an_experiment()
            except Exception:
                self.logger.exception("Experiment failed with an exception")

        # Launch the experiment in a background thread
        self.stop_event.clear()
        self.thread = threading.Thread(target=thread_target, daemon=True)
        self.thread.start()

        # Notify user that logging has started
        if not quiet: self.vt.console_message("success", f"Experiment logging saving in {self.output_log}")

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: launch_an_experiment
# ─────────────────────────────────────────────────────────────────────────────
    def launch_an_experiment(self, quiet: bool = False) -> None:

        # Ensure an experiment is loaded before proceeding
        if len(self.queue) == 0:
            self.vt.console_message("error", "No experiment in the queue. Please add an experiment first.", indent=1, logger=self.logger)
            return
        
        self.current_experiment = self.queue.pop()

        # If PTP enabled, kill actual clients and load new PTP clients
        if self.current_experiment.synccore_start != -1:
            self.synccore.stop_ptp(preconfirmation=True, quiet=True)
            self.synccore.load_clients(file_cfg=self.current_experiment.fn_absolute_path, logger=self.logger, extra_indent=1, quiet=True)

        # Load datasources
        self.dataex.load_datasources(file_cfg=self.current_experiment.fn_absolute_path, quiet = True)

        # Display experiment summary
        if not quiet: 
            self.vt.console_message("info", f"Experiment Name: {self.current_experiment.fn}", logger=self.logger)
            self.vt.console_message("info", f"dataex Datasources: {self.current_experiment.dataex_datasources} | Starting at: {str(datetime.timedelta(seconds=self.current_experiment.dataex_start))}", logger=self.logger)
            if self.current_experiment.synccore_start != -1:
                self.vt.console_message("info", f"PTP Clients: {self.current_experiment.synccore_clients} | Starting at: {str(datetime.timedelta(seconds=self.current_experiment.synccore_start))}", logger=self.logger)
            if self.current_experiment.stl_start != -1:
                self.vt.console_message("info", f"STL Program: {self.current_experiment.stl_fn} | Starting at: {str(datetime.timedelta(seconds=self.current_experiment.stl_start))}", logger=self.logger)
            self.vt.console_message("info", f"Total duration: {int(self.current_experiment.duration / 60)} min | Data duration: {int(self.current_experiment.dataex_duration / 60)} min", logger=self.logger)

        # Display experiment start message
        self.vt.console_message("title", "Starting Experiment", "⚗️", logger=self.logger)

        # Notify via Telegram
        self.telegram_bot.send_message(message=f"⚗️ Starting Experiment {self.current_fn} with ID {self.current_hash_id}")

        # Update internal state and record start time
        self.current_experiment.state = "Running"
        start_time: float = time.time()
        self.current_experiment.start_ts = start_time

        # Define tasks with their scheduled start times
        tasks: List[Tuple[int, Callable[[], None], str]] = [
            (
                self.current_experiment.dataex_start,
                lambda: self.dataex.start_extraction(
                    suffix_out=f"{self.current_experiment.fn}_{self.current_experiment.hash_id}",
                    dir_out=self.current_experiment.exp_output_dir,
                    duration_out=self.current_experiment.dataex_duration,
                    logger=self.logger,
                    extra_indent=1
                ),
                "dataex"
            )
        ]

        # Include PTP task if configured
        if self.current_experiment.synccore_start != -1:
            tasks.append((
                self.current_experiment.synccore_start,
                lambda: self.synccore.start_ptp(
                    logger=self.logger,
                    extra_indent=1,
                    stop = False
                ),
                "PTP"
            ))

        # Include STL task if configured
        if self.current_experiment.stl_start != -1:
            tasks.append((
                self.current_experiment.stl_start,
                lambda: self.loadgen.start_stl_program(
                    self.current_experiment.fn_absolute_path,
                    self.current_experiment.stl_duration,
                    self.current_experiment.output_yaml,
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
        remaining: float = self.current_experiment.duration - (time.time() - start_time)
        if remaining > 0:
            self.interrupted_sleep(remaining, self.stop_event)
        
        # Finalize experiment
        if self.stop_event.is_set():
            self.interrupted_sleep(10, self.stop_event)
            self.vt.console_message("caution", "Experiment stopped.", logger=self.logger)
            self.current_experiment.state = "Stopped"
            # Notify Telegram
            self.telegram_bot.send_message(message=f"⚠️ Stopped Experiment {self.current_fn} with ID {self.current_hash_id}")

        else: 
            self.vt.console_message("success", "Experiment completed.", logger=self.logger)
            self.vt.console_message("info", "Waiting 10 seconds for finish.", logger=self.logger)
            self.current_experiment.state = "Finished"
            # Stop PTP if configured to do so
            if self.current_experiment.synccore_stop_at_end is True:
                self.synccore.stop_ptp(preconfirmation=True,logger=self.logger)
            # Notify Telegram
            self.telegram_bot.send_message(message=f"✅ Finished Experiment {self.current_fn} with ID {self.current_hash_id}")


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: launch_whole_queue
# ─────────────────────────────────────────────────────────────────────────────
    def launch_whole_queue(self) -> None:

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
        self.telegram_bot.send_message(message=f"🏭 Starting a batch of the experiment {selected}, {self.total_repetitions} repetitions and {self.delay_between} seconds between experiments.")
        
        def batch_runner(stop_event: threading.Event) -> None:
            for i in range(self.total_repetitions):
                if stop_event.is_set():
                    break

                if stop_event.is_set():
                    break

                self.load_experiment(filepath_cfg, quiet=True)
                if stop_event.is_set():
                    break

                self.launch_experiment_bg(quiet=True)
                if stop_event.is_set():
                    break

                if i < self.total_repetitions - 1:
                    for _ in range(int(self.current_experiment.duration + self.delay_between)):
                        if stop_event.is_set():
                            break
                        time.sleep(1)

        self.batch_thread = threading.Thread(target=lambda: batch_runner(self.stop_event), daemon=True)
        self.batch_thread.start()

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: stop_current_experiment
# ─────────────────────────────────────────────────────────────────────────────
    def stop_current_experiment(self, extra_indent: int = 0) -> None:
        """
        Stops all components of a running experiment and updates its current_state.

        Attempts to stop PTP synchronization, data extraction, and STL traffic generation
        if they were configured. Any errors encountered during shutdown are reported.
        The experiment current_state is updated to `"Stopped"` once all components are terminated.

        ### Args:
        - **extra_indent** (`int`): Indentation level for console messages. Defaults to `0`.
        """

        # Display section title
        self.vt.console_message("title", "Stopping/Cleaning Experiment", "🛑", indent=extra_indent, logger=self.logger)
        self.vt.console_message("title", "Stopping/Cleaning Experiment", "🛑", indent=extra_indent)


        # Check if an experiment is currently running
        if self.current_state != "Running":
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
            
        # Update experiment current_state
        self.thread.join(timeout=5)
        self.current_state = "Stopped"
        self.vt.console_message("success", "All experiment components stopped successfully.", logger=self.logger)
        self.vt.console_message("success", "All experiment components stopped successfully.", indent=extra_indent)

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: stop_whole_queue
# ─────────────────────────────────────────────────────────────────────────────
    def stop_whole_queue(self, extra_indent: int = 0) -> None:
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
        self.telegram_bot.send_message(message=f"🏭 Batch of the experiment {self.current_fn} stopped at {self.actual_repetition}/{self.total_repetitions}.")


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: show_progress
# ─────────────────────────────────────────────────────────────────────────────
    def show_progress(self) -> None:
        """
        Displays real-time progress of the self.current_experiment.

        Console messages are used to notify the user if no experiment is running.
        """
        # Display section title
        self.vt.console_message("title", "Showing progress", "⏳")

        # Check if an experiment has been started
        if not self.current_fn:
            self.vt.console_message("caution", "No data extraction was started.", indent=1)
            return

        # Show real-time progress bar
        if self.current_state == "Running":
            self.vt.real_time_progress(self.current_start_ts, self.current_experiment.duration, "⏳ Experiment running...", repetition_info= f"{self.actual_repetition}/{self.total_repetitions}")


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: show_current_experiment_log
# ─────────────────────────────────────────────────────────────────────────────
    def show_current_experiment_log(self) -> None:
        """
        Displays the real-time log output of the self.current_experiment.

        If no experiment is currently running, a warning message is shown.
        Otherwise, the log file is streamed live in the console.
        """

        # Check if experiment is running
        if self.current_state != "Running":
            self.vt.console_message("caution", "No experiment was started.", indent=1)
            return

        # Stream the real-time log output
        log_path: Path = self.output_log
        self.vt.real_time_log(log_path)


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: show_current_experiment_data
# ─────────────────────────────────────────────────────────────────────────────
    def show_current_experiment_data(self) -> None:
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
        
        if self.current_experiment:
            if not quiet: self.vt.console_message("clean", "Deleting current self.current_experiment...")

            self.current_experiment = None

            # Notify user
            if not quiet: self.vt.console_message("success", "Laboratory cleaned.", indent=1)

