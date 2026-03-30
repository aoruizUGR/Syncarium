#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# exp_orchestra.py

**Project**: Syncarium - Intelligent Timing Platform Toolkit  
**Description**: Syncarium ExpOrchestra  
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada  
**Created**: 2025-06-27  
**Version**: 1.2.0  
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
        self.interexp_delay: Optional[int] = 900       

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
        - 🧪 Add Experiment → add_exp
        - 🗑️ Remove Experiment → remove_exp
        - ▶️🧪 Start First Experiment → launch_first_exp
        - 🛑🧪 Stop Current Experiment → stop_current_exp
        - ▶️🏭 Start Queue → launch_queue
        - 🛑🏭 Stop Queue → stop_queue
        - ⏳ Show Current Experiment Progress → show_current_exp_progress
        - 📄 Show Current Experiment Log → show_current_exp_log
        - 📄 Show Current Experiment Data → show_current_exp_data
        - 🔄 Refresh view → refresh_view
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
                self.vt.console_message("info", f"Delay between experiments: {self.interexp_delay} seconds")

                # Show experiment queue
                self.vt.table_experiment_queue(
                    self.queue
                )

                self.vt.table_current_experiment(
                    self.current_experiment
                )

                # Display interactive menu and get user choice
                choice: str = self.vt.console_select_menu(
                    choices=[
                        {"name": "🧪 Add Experiment", "value": "add_exp"},
                        {"name": "🗑️ Remove Experiment", "value": "remove_exp"},
                        {"name": "▶️🧪 Start First Experiment", "value": "launch_first_exp"},
                        {"name": "🛑🧪 Stop Current Experiment", "value": "stop_current_exp"},
                        {"name": "▶️🏭 Start Queue", "value": "launch_queue"},
                        {"name": "🛑🏭 Stop Queue", "value": "stop_queue"},
                        {"name": "🕒 Set Inter-Experiment Delay", "value": "set_interexp_delay"},
                        {"name": "⏳ Show Current Experiment Progress", "value": "show_current_exp_progress"},
                        {"name": "📄 Show Current Experiment Log", "value": "show_current_exp_log"},
                        {"name": "📄 Show Current Experiment Data", "value": "show_current_exp_data"},
                        {"name": "🔄 Refresh view", "value": "refresh_view"},
                        {"name": "❌ Exit", "value": "exit"}
                    ],
                    indent=1
                )

                # Map menu options to corresponding methods
                submenu: dict[str, Callable[[], None]] = {
                    "add_exp":                self.add_exp,
                    "remove_exp":            self.remove_exp,
                    "launch_first_exp":      self.launch_first_exp,
                    "stop_current_exp":             self.stop_current_exp,
                    "launch_queue":                 self.launch_queue,
                    "stop_queue":                   self.stop_queue,
                    "set_interexp_delay":           self.set_interexp_delay,
                    "show_current_exp_progress":                self.show_current_exp_progress,
                    "show_current_exp_log":         self.show_current_exp_log,
                    "show_current_exp_data":        self.show_current_exp_data,
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
# 📌 Function: add_exp
# ─────────────────────────────────────────────────────────────────────────────
    def add_exp(self, file_cfg: Optional[Path] = None, quiet: bool = False) -> None:

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
            repetitions = int(self.vt.console.input("Enter number of repetitions [1]: ") or 1)
            for _ in range(repetitions):
                experiment = Experiment(file_cfg=filepath_cfg)
                self.queue.append(experiment)
                            
            self.vt.console_message("info", f"Experiment {filepath_cfg} added {repetitions} times to the experiment queue.")

        except Exception as e:
            # Handle errors during file reading or parsing
            self.vt.console_message("error", f"Error adding experiment: {e}", indent=1)

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: remove_exp
# ─────────────────────────────────────────────────────────────────────────────
    def remove_exp(self) -> None:
        if not self.queue:
            self.vt.console_message("error", f"The experiment queue is empty.")
            return 
        
        choices = [{"name": f"{i}. Experiment with HashID {obj.hash_id}", "value": obj} for i, obj in enumerate(self.queue, 1)]
        selected: Experiment = self.vt.console_select_menu(
            choices=choices,
            message="Available queued experiments:",
            indent=1
        )

        self.queue.remove(selected)
        self.vt.console_message("success", f"Experiment {selected.fn} with HashID {selected.hash_id} removed from queue.", indent=1)

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
# 📌 Function: launch_first_exp
# ─────────────────────────────────────────────────────────────────────────────
    def launch_first_exp(self, quiet: bool = False) -> None:
        if len(self.queue) == 0:
            self.vt.console_message("error", "No experiments in the queue.")
            return

        # Notify user that experiment is starting
        if not quiet: self.vt.console_message("title", "Starting First Experiment of the queue.", "🧪")

        self.current_experiment = self.queue.popleft()

        # Create and configure logger
        timestamp: str = time.strftime('%d-%m-%Y_%H:%M:%S')
        self.logger = logging.getLogger(f"experiment_logger_{timestamp}")
        self.logger.setLevel(logging.DEBUG)

        # Add rotating file handler if not already present
        if not self.logger.handlers:
            handler = RotatingFileHandler(self.current_experiment.output_log, maxBytes=5_000_000, backupCount=3)
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
        if not quiet: self.vt.console_message("success", f"Experiment logging saving in {self.current_experiment.output_log}")

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: launch_an_experiment
# ─────────────────────────────────────────────────────────────────────────────
    def launch_an_experiment(self, quiet: bool = False) -> None:

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
        self.telegram_bot.send_message(message=f"⚗️ Starting Experiment {self.current_experiment.fn} with ID {self.current_experiment.hash_id}")

        # Update internal state and record start time
        self.current_experiment.state = "Running"
        start_time: float = time.time()
        self.current_experiment.start_ts = start_time

        # Define tasks with their scheduled start times
        tasks: List[Tuple[int, Callable[[], None], str]] = [
            (
                self.current_experiment.dataex_start,
                lambda: self.dataex.start_extraction(
                    csv_fn_out      = self.current_experiment.output_csv,
                    yaml_fn_out     = self.current_experiment.output_yaml,
                    duration_out    = self.current_experiment.dataex_duration,
                    logger          = self.logger,
                    extra_indent    = 1
                ),
                "DataEx"
            )
        ]

        # Include PTP task if configured
        if self.current_experiment.synccore_start != -1:
            tasks.append((
                self.current_experiment.synccore_start,
                lambda: self.synccore.start_ptp(
                    logger          = self.logger,
                    extra_indent    = 1,
                    stop            = False
                ),
                "SyncCore"
            ))

        # Include STL task if configured
        if self.current_experiment.stl_start != -1:
            tasks.append((
                self.current_experiment.stl_start,
                lambda: self.loadgen.start_stl_program(
                    file_cfg        = self.current_experiment.fn_absolute_path,
                    stl_duration    = self.current_experiment.stl_duration,
                    stl_output      = self.current_experiment.output_yaml,
                    logger          = self.logger,
                    extra_indent    = 1
                ),
                "LoadGen"
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
            self.vt.console_message("info", f"Experiment will run for {int(self.current_experiment.dataex_duration)} seconds.", indent=1, logger=self.logger)

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
            self.telegram_bot.send_message(message=f"⚠️ Stopped Experiment {self.current_experiment.fn} with ID {self.current_experiment.hash_id}")

        else: 
            self.vt.console_message("success", "Experiment completed.", logger=self.logger)
            self.vt.console_message("info", "Waiting 10 seconds for finish.", logger=self.logger)
            self.current_experiment.state = "Finished"
            # Stop PTP if configured to do so
            if self.current_experiment.synccore_stop_at_end is True:
                self.synccore.stop_ptp(preconfirmation=True,logger=self.logger)
            # Notify Telegram
            self.telegram_bot.send_message(message=f"✅ Finished Experiment {self.current_experiment.fn} with ID {self.current_experiment.hash_id}")

        if len(self.queue) == 0:
            self.telegram_bot.send_message(message=f"🏭 Queue empty.")


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: stop_current_exp
# ─────────────────────────────────────────────────────────────────────────────
    def stop_current_exp(self, extra_indent: int = 0) -> None:
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
        if self.current_experiment.state != "Running":
            self.vt.console_message("warning", "No experiment is currently running.", indent=1)
            return

        errors: List[str] = []
        self.stop_event.set()

        # Attempt to stop PTP component if it was configured
        if self.current_experiment.synccore_start != -1:
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
        if self.current_experiment.stl_start != -1:
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
        self.current_experiment.state = "Stopped"
        self.vt.console_message("success", "All experiment components stopped successfully.", logger=self.logger)
        self.vt.console_message("success", "All experiment components stopped successfully.", indent=extra_indent)

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: launch_queue
# ─────────────────────────────────────────────────────────────────────────────
    def launch_queue(self) -> None:
        
        if len(self.queue) == 0:
            self.vt.console_message("error", "No experiments in the queue.")
            return            

        # Ask user for number of repetitions and delay
        self.vt.console_message("title", "Launching entire queue...", "🏭")

        
        # Notify via Telegram
        self.telegram_bot.send_message(message=f"🏭 Starting entire experiment queue with {self.interexp_delay} seconds between experiments.")
        
        def queue_runner(stop_event: threading.Event) -> None:

            while len(self.queue) != 0:

                if stop_event.is_set():
                    break

                self.launch_first_exp(quiet=True)

                if stop_event.is_set():
                    break

                for _ in range(int(self.current_experiment.duration + self.interexp_delay)):
                    if stop_event.is_set():
                        break
                    time.sleep(1)

        self.queue_thread = threading.Thread(target=lambda: queue_runner(self.stop_event), daemon=True)
        self.queue_thread.start()

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: stop_queue
# ─────────────────────────────────────────────────────────────────────────────
    def stop_queue(self, extra_indent: int = 0) -> None:
        """
        Stops all running experiments in the current queue.

        Signals the stop event to interrupt any ongoing or scheduled experiment launches.
        Also calls `stop_experiment()` to clean up the currently running experiment, and
        waits for the queue thread to finish execution.

        A Telegram notification is sent to indicate the queue was stopped.

        ### Args:
        - **extra_indent** (`int`): Indentation level for console messages. Defaults to `0`.
        """

        # Signal to stop all threads
        self.stop_event.set()

        # Stop the currently running experiment
        self.stop_current_exp(extra_indent=extra_indent)

        self.vt.console_message("title", "Stopping Experiment Queue", "🛑", indent=extra_indent)
        
        # Stop entire queue
        self.queue_thread.join()

        self.vt.console_message("success", "Queue stop signal sent.", indent=extra_indent)

        # Notify via Telegram
        self.telegram_bot.send_message(message=f"🏭 Queue stopped.")

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: set_interexp_delay
# ─────────────────────────────────────────────────────────────────────────────
    def set_interexp_delay(self) -> None:
        # Display section title
        self.vt.console_message("title", "Setting Inter-Experiment Delay", "🕒")
        
        self.interexp_delay = int(self.vt.console.input("Enter number of seconds to wait between experiments:"))

        self.vt.console_message("success", "Inter-experiment delay set.")


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: show_current_exp_progress
# ─────────────────────────────────────────────────────────────────────────────
    def show_current_exp_progress(self) -> None:
        """
        Displays real-time progress of the self.current_experiment.

        Console messages are used to notify the user if no experiment is running.
        """
        # Display section title
        self.vt.console_message("title", "Showing progress", "⏳")

        # Check if an experiment has been started
        if not self.current_experiment:
            self.vt.console_message("caution", "No data extraction was started.", indent=1)
            return

        # Show real-time progress bar
        if self.current_experiment.state == "Running":
            self.vt.real_time_progress(self.current_experiment.start_ts, self.current_experiment.duration, "⏳ Experiment running...")


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: show_current_exp_log
# ─────────────────────────────────────────────────────────────────────────────
    def show_current_exp_log(self) -> None:
        """
        Displays the real-time log output of the self.current_experiment.

        If no experiment is currently running, a warning message is shown.
        Otherwise, the log file is streamed live in the console.
        """

        # Check if experiment is running
        if self.current_experiment.state != "Running":
            self.vt.console_message("caution", "No experiment was started.", indent=1)
            return

        # Stream the real-time log output
        log_path: Path = self.current_experiment.output_log
        self.vt.real_time_log(log_path)


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: show_current_exp_data
# ─────────────────────────────────────────────────────────────────────────────
    def show_current_exp_data(self) -> None:
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
        log_path: Path = self.dataex.csv_output_filepath
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

