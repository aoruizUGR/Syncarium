#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# source

**Project**: TempusNode - Intelligent Timing Platform Toolkit  
**Description**: Data Source Class.  
**Author**: PhD Student Alberto Ortega Ruiz, PhD Student Víctor Vázquez, University of Granada  
**Created**: 2025-05-02  
**Version**: 1.1.0  
**License**: GPLv3
"""


# ─────────────────────────────────────────────────────────────────────────────
# Standard Library Imports
import threading
import queue
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# Third-Party Imports
# (None used directly in this file)

# ─────────────────────────────────────────────────────────────────────────────
# Local Application Imports
# (None used directly in this file)


import threading
import queue
from typing import Any

# ─────────────────────────────────────────────────────────────
#  🛢️ Data Source SubClass
# ─────────────────────────────────────────────────────────────
class DataSource(threading.Thread):
    """
    A thread-based data source that sends timestamped metrics to a shared queue.

    ### Attributes
    - **name** (`str`): Identifier for the data source.
    - **queue** (`queue.Queue`): Shared queue to which metrics are sent.
    - **event** (`threading.Event`): Event used to signal when the thread should stop.
    """

# ─────────────────────────────────────────────────────────────────────────────
# 🚧 Function: constructor
# ─────────────────────────────────────────────────────────────────────────────
    def __init__(self, name: str, queue: queue.Queue, event: threading.Event) -> None:
        """
        Initializes a new `DataSource` thread.

        ### Args
        - **name** (`str`): Identifier for the data source.
        - **queue** (`queue.Queue`): Queue to which metrics will be sent.
        - **event** (`threading.Event`): Event used to signal thread termination.
        """
        super().__init__()
        self.name = name
        self.queue = queue
        self.event = event
        self.daemon = True


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: send_metric
# ─────────────────────────────────────────────────────────────────────────────
    def send_metric(self, timestamp: float, name: str, value: Any) -> None:
        """
        Sends a metric to the shared queue with a timestamp and a formatted name.

        ### Args
        - **timestamp** (`float`): Time the metric was recorded.
        - **name** (`str`): Base name of the metric.
        - **value** (`Any`): Value of the metric.
        """
        full_name = f"{name}_{self.name}"
        self.queue.put((timestamp, full_name, value))
        # Metrics could also be forwarded to Prometheus, InfluxDB, MQTT, etc.


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: stop
# ─────────────────────────────────────────────────────────────────────────────
    def stop(self) -> None:
        """
        Signals the thread to stop and waits for its termination.
        """
        self.event.set()
        self.join()
