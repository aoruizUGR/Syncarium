#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# filelog.py

**Project**: Syncarium – Intelligent Timing Platform Toolkit  
**Description**: File Log Data Source Class  
**Author**: PhD Student Alberto Ortega Ruiz, PhD Student Víctor Vázquez, University of Granada  
**Created**: 2025-05-02  
**Version**: 1.2.0  
**License**: GPLv3
"""


# ─────────────────────────────────────────────────────────────────────────────
# Standard Library Imports
import os
import re
import time
import queue
import threading
from pathlib import Path
from typing import Generator, TextIO, Pattern

# ─────────────────────────────────────────────────────────────────────────────
# Third-Party Imports
# (None used directly in this file)

# ─────────────────────────────────────────────────────────────────────────────
# Local Application Imports
from syncarium.core.dsources import DataSource

# ─────────────────────────────────────────────────────────────
#  🛢️ File Log Data Source SubSubClass
# ─────────────────────────────────────────────────────────────
class FileLogDataSource(DataSource):
    """
    A data source that monitors a log file in real time and extracts metrics using regex patterns.

    This subclass of `DataSource` watches for new lines in a log file, applies a regex pattern
    to extract named groups, and sends the extracted metrics to a shared queue.

    ### Attributes
    - **pattern** (`Pattern`): Compiled regex pattern used to extract metrics.
    - **filepath** (`str`): Path to the log file being monitored.
    """

# ─────────────────────────────────────────────────────────────────────────────
# 🚧 Function: constructor
# ─────────────────────────────────────────────────────────────────────────────
    def __init__(self, name: str, queue: queue.Queue, event: threading.Event, pattern: str, filepath: str) -> None:
        """
        Initializes a `FileLogDataSource` with a regex pattern and log file path.

        ### Args
        - **name** (`str`): Identifier for the data source.
        - **queue** (`queue.Queue`): Queue to send extracted metrics to.
        - **event** (`threading.Event`): Event used to signal thread termination.
        - **pattern** (`str`): Regex pattern used to extract metrics from log lines.
        - **filepath** (`str`): Path to the log file to monitor.

        ### Raises
        - **FileNotFoundError**: If the specified log file does not exist.
        """
        super().__init__(name, queue, event)
        self.pattern: Pattern = re.compile(pattern)
        self.filepath: str = filepath
        if not Path(self.filepath).is_file():
            raise FileNotFoundError(f"❌ Log file not found: {self.filepath}")

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: follow
# ─────────────────────────────────────────────────────────────────────────────
    def follow(self, file: TextIO) -> Generator[str, None, None]:
        """
        Generator that yields new lines appended to the file in real time.

        ### Args
        - **file** (`TextIO`): Opened file object to read from.

        ### Yields
        - **str**: New lines as they are written to the file.
        """
        file.seek(0, os.SEEK_END)
        while not self.event.is_set():
            line = file.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: run
# ─────────────────────────────────────────────────────────────────────────────
    def run(self) -> None:
        """
        Starts the thread and processes new lines from the log file.

        For each line that matches the regex pattern, extracts named groups and sends them
        as timestamped metrics to the shared queue.
        """
        try:
            with open(self.filepath, 'r', encoding='utf-8') as file:
                for line in self.follow(file):
                    match = self.pattern.search(line)
                    if not match:
                        continue

                    timestamp = time.time_ns()
                    for name, value in match.groupdict().items():
                        self.send_metric(timestamp, name, value)
        except Exception as e:
            print(f"[{self.name}] ⚠️ Error: {e}")


