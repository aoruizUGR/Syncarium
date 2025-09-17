#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 File Name   : syslog.py
 Project     : Syncarium - Intelligent Timing Platform Toolkit
 Description : System Log Data Source Class.
 Author      : PhD Student Alberto Ortega Ruiz, PhD Student Víctor Vázquez, University of Granada
 Created     : 2025-05-02
 Version     : 1.0.0
 License     : GPLv3
===============================================================================
"""

# ─────────────────────────────────────────────────────────────────────────────
# Standard Library Imports
import os
import re
import time
import signal
import multiprocessing
from typing import List, Generator, TextIO

# ─────────────────────────────────────────────────────────────────────────────
# Third-Party Imports
# (None used directly in this file)

# ─────────────────────────────────────────────────────────────────────────────
# Local Application Imports
from syncarium.tui.core.dsources import DataSource


# ─────────────────────────────────────────────────────────────
#  🛢️ System Log Data Source SubSubClass
# ─────────────────────────────────────────────────────────────
class SysLogDataSource(DataSource):
    """
    A data source that monitors the system log and extracts metrics using a regex pattern.

    This subclass of `DataSource` reads from `/var/log/syslog`, applies a regular expression
    to each new line, and sends extracted named groups as metrics to a shared queue.

    ### Attributes
    - **pattern** (`str`): Regular expression pattern with named groups used to extract metrics.
    """

# ─────────────────────────────────────────────────────────────────────────────
# 🚧 Function: constructor
# ─────────────────────────────────────────────────────────────────────────────
    def __init__(self, name: str, queue: multiprocessing.Queue, event: multiprocessing.synchronize.Event, pattern: str) -> None:
        """
        Initializes a `SysLogDataSource` with a regex pattern for metric extraction.

        ### Args
        - **name** (`str`): Identifier for the data source.
        - **queue** (`multiprocessing.Queue`): Queue for sending extracted metrics.
        - **event** (`multiprocessing.synchronize.Event`): Event used to control the process lifecycle.
        - **pattern** (`str`): Regular expression pattern with named groups to match log lines.
        """
        super().__init__(name, queue, event)
        self.pattern = pattern


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: follow
# ─────────────────────────────────────────────────────────────────────────────
    def follow(self, file: TextIO) -> Generator[str, None, None]:
        """
        Generator that yields new lines appended to a file in real time.

        Mimics the behavior of `tail -f`, continuously reading new lines from the end
        of the file until the stop event is triggered.

        ### Args
        - **file** (`TextIO`): File object to monitor.

        ### Yields
        - **str**: New lines appended to the file.
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
        Starts the log monitoring process.

        Opens `/var/log/syslog`, follows it in real time, and applies the regex pattern
        to each new line. If a match is found, extracts named groups and sends them
        as timestamped metrics to the shared queue.
        """
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        with open("/var/log/syslog") as file:
            for line in self.follow(file):
                res = re.search(self.pattern, line)
                if not res:
                    continue

                timestamp = time.time_ns()
                for name, value in res.groupdict().items():
                    self.send_metric(timestamp, name, value)


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: source_features
# ─────────────────────────────────────────────────────────────────────────────
    def source_features(self) -> List[str]:
        """
        Returns a list of features specific to this data source.

        ### Returns
        - **List[str]**: A list containing the regex pattern used for metric extraction.
        """
        features = []
        features.append(self.pattern)
        return features

