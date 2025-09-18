#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ppsanalyzer.py

**Project**: Syncarium – Intelligent Timing Platform Toolkit  
**Description**: NetTimeLogic PPS Analyzer Data Source Class  
**Author**:  
- Original: Martin Burri `<info@burrima.ch>`, Sven Meier `<contact@nettimelogic.com>`  
- Adapted: PhD Student Alberto Ortega Ruiz, PhD Student Víctor Vázquez, University of Granada  
**Created**: 2025-05-02  
**Version**: 1.1.0  
**License**: GPLv3 (with portions under LGPLv3)

---

This file includes adapted code from the UniversalPpsAnalyzer project,  
originally licensed under the GNU Lesser General Public License v3.

The original source code is available at:  
[https://github.com/NetTimeLogic-OpenSource/UniversalpsAnalyzer

© 2020, NetTimeLogic GmbH, Switzerland.  
See [http://www.gnu.org/licenses/](http://se details.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Standard Library Imports
import time
import queue
import threading
from datetime import datetime, timedelta
from typing import List
from functools import reduce

# ─────────────────────────────────────────────────────────────────────────────
# Third-Party Imports
import serial

# ─────────────────────────────────────────────────────────────────────────────
# Local Application Imports
from syncarium.core.dsources import DataSource


# ─────────────────────────────────────────────────────────────
#  🛢️ PPS Analyzer Data Source SubSubClass
# ─────────────────────────────────────────────────────────────
class PPSAnalyzerDataSource(DataSource):
    """
    Data source class for interfacing with a PPS (Pulse Per Second) analyzer.

    This class defines constants and register mappings used to interact
    with a PPS hardware module. It does not implement active data acquisition
    but serves as a base or utility class for accessing PPS-related registers.

    ### Attributes
    - **NUM_TSU** (`int`): Total number of Timestamping Units (TSUs).
    - **REG** (`dict[str, int]`): Register map with relative addresses for PPS control.
    - **port** (`str`): Serial port used for UART communication.
    - **uart** (`Any`): UART interface (to be initialized externally).
    - **pps_inputs** (`List[int]`): List of active PPS input indices.
    - **cable_delays** (`List[int]`): Cable delay values (in nanoseconds) for each input.
    - **tsu_state** (`List[bool]`): Active/inactive state of each TSU.
    - **base_addrs** (`List[int]`): Base memory addresses for each TSU.
    """


# ─────────────────────────────────────────────────────────────────────────────
# 🚧 Function: constructor
# ─────────────────────────────────────────────────────────────────────────────
    def __init__(
        self,
        name: str,
        queue: queue.Queue,
        event: threading.Event,
        serial_port: str = "/dev/ttyUSB1",
        pps_inputs: List[int] | None = None,
        cable_delays: List[int] | None = None
    ) -> None:
        """
        Initializes a `PPSAnalyzerDataSource` instance with configuration for PPS hardware.

        ### Args
        - **name** (`str`): Identifier for the thread or component.
        - **queue** (`queue.Queue`): Queue for inter-thread communication.
        - **event** (`threading.Event`): Event used for synchronization.
        - **serial_port** (`str`, optional): Serial port for UART communication. Defaults to `"/dev/ttyUSB1"`.
        - **pps_inputs** (`List[int]`, optional): List of active PPS input indices. Defaults to all TSUs.
        - **cable_delays** (`List[int]`, optional): Cable delay values (in nanoseconds). Defaults to zero delay.

        ### Raises
        - **ValueError**: If `pps_inputs` and `cable_delays` have mismatched lengths.
        """

        super().__init__(name, queue, event)

        self.NUM_TSU = 9  # Total number of Timestamping Units (TSUs)

        # Register map with relative addresses for PPS module control
        self.REG = {
            "ENABLE": 0x00,        # Register to enable the PPS module
            "POLARITY": 0x08,      # Register to configure signal polarity
            "VERSION": 0x0C,       # Register to read firmware/hardware version
            "CABLE_DELAY": 0x20,   # Register to set cable delay compensation
            "INT_CLEAR": 0x30,     # Register to clear interrupt flags
            "INT_ENABLE": 0x34,    # Register to enable specific interrupts
            "EVENT_COUNT": 0x38,   # Register to count PPS events
            "TS_NS": 0x44,         # Register to read timestamp in nanoseconds
            "TS_S": 0x48           # Register to read timestamp in seconds
        }

        self.port = serial_port
        self.uart = None  # UART interface will be initialized later

        # Use all TSUs by default if no specific PPS inputs are provided
        self.pps_inputs = pps_inputs if pps_inputs is not None else list(range(self.NUM_TSU))

        # Default cable delays to 0 if not specified
        self.cable_delays = cable_delays if cable_delays is not None else [0] * self.NUM_TSU

        # Ensure each PPS input has a corresponding cable delay
        if len(self.pps_inputs) != len(self.cable_delays):
            raise ValueError("❌ 'pps_inputs' and 'cable_delays' must have the same length.")

        # Track the active/inactive state of each TSU
        self.tsu_state = [False] * self.NUM_TSU

        # Compute base memory addresses for each TSU
        self.base_addrs = [0x10000000 * (i + 1) for i in range(self.NUM_TSU)]


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: _checksum
# ─────────────────────────────────────────────────────────────────────────────
    def _checksum(self, data: str) -> str:
        """
        Calculates the XOR checksum of a string.

        ### Args
        - **data** (`str`): Input string to compute the checksum from.

        ### Returns
        - **str**: Two-character hexadecimal checksum string (zero-padded).
        """
        return format(reduce(lambda x, y: x ^ ord(y), data, 0), 'X').zfill(2)


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: _comm
# ─────────────────────────────────────────────────────────────────────────────
    def _comm(self, code: str, fields: List[str] = [], tries: int = 2) -> List[str]:
        """
        Sends a command to the PPS device over UART and parses the response.

        Constructs a command string with checksum, sends it via UART, and validates
        the response. Retries the communication if an error occurs.

        ### Args
        - **code** (`str`): Command code to send.
        - **fields** (`List[str]`, optional): List of fields to include in the command.
        - **tries** (`int`, optional): Number of retry attempts in case of failure. Defaults to 2.

        ### Returns
        - **List[str]**: Parsed fields from the device response.

        ### Raises
        - **Exception**: If communication fails or response is invalid after all retries.
        """

        for attempt in range(tries):
            try:
                # Construct the command string with checksum
                payload = f"{code}{',' if fields else ''}{','.join(fields)}"
                checksum = self._checksum(payload)
                tx = f"${payload}*{checksum}\r\n"
                self.uart.write(tx.encode())

                # Read and decode the response
                rx = self.uart.readline().decode().strip()
                if not rx.startswith('$'):
                    raise Exception("Invalid response format")

                # Split and validate checksum
                content, received_chk = rx[1:].split("*")
                if received_chk != self._checksum(content):
                    raise Exception("Checksum mismatch")

                parts = content.split(',')
                if parts[0] == "ER":
                    raise Exception("Device returned an error")

                return parts[1:]

            except Exception:
                if attempt == tries - 1:
                    raise  # Raise the last exception if all attempts fail

                # Reinitialize UART before retrying
                self.uart.close()
                self.uart = serial.Serial(port=self.port, baudrate=1000000, timeout=3)

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: _read
# ─────────────────────────────────────────────────────────────────────────────
    def _read(self, addr: int | str) -> int:
        """
        Reads a 32-bit hexadecimal value from a given memory address.

        ### Args
        - **addr** (`int | str`): Address to read from. Can be an integer or a hexadecimal string.

        ### Returns
        - **int**: Value read from the address, converted from hexadecimal to integer.
        """

        # Format address as hex string if it's not already
        addr = f"0x{addr:08X}" if not isinstance(addr, str) else addr

        # Send read command and parse the second field of the response
        return int(self._comm("RC", [addr])[1], 16)

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: _write
# ─────────────────────────────────────────────────────────────────────────────
    def _write(self, addr: int | str, val: int | str) -> None:
        """
        Writes a 32-bit hexadecimal value to a given memory address.

        ### Args
        - **addr** (`int | str`): Target address to write to. Can be an integer or a hexadecimal string.
        - **val** (`int | str`): Value to write. Can be an integer or a hexadecimal string.
        """

        # Format address and value as hex strings if they are integers
        addr = f"0x{addr:08X}" if not isinstance(addr, str) else addr
        
        if not isinstance(val, str):
            val = val & 0xFFFFFFFF # Ensure a 32 bits unsigned int
            val = f"0x{val:08X}"

        # Send write command with address and value
        self._comm("WC", [addr, val])

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: setUp
# ─────────────────────────────────────────────────────────────────────────────
    def setUp(self) -> None:
        """
        Initializes the UART connection and configures the TSU modules.

        Opens the UART interface, clears previous configuration, enables each
        configured PPS input, and applies cable delay compensation.
        """

        # Open UART connection with specified port and settings
        self.uart = serial.Serial(port=self.port, baudrate=1000000, timeout=3)

        # Clear configuration on the device
        self._comm("CC")

        # Enable each configured TSU and apply cable delay
        for i in range(len(self.pps_inputs)):
            self.setEnable(self.pps_inputs[i], True)
            self._write(
                self.base_addrs[self.pps_inputs[i]] + self.REG["CABLE_DELAY"],
                self.cable_delays[i]
            )

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: setEnable
# ─────────────────────────────────────────────────────────────────────────────
    def setEnable(self, idx: int, enable: bool) -> None:
        """
        Enables or disables a specific TSU (Timestamping Unit).

        Writes to the appropriate registers to activate or deactivate the TSU,
        configure its interrupt behavior, and update its internal state.

        ### Args
        - **idx** (`int`): Index of the TSU to configure.
        - **enable** (`bool`): `True` to enable the TSU, `False` to disable it.
        """

        base = self.base_addrs[idx]

        # Write to the ENABLE register
        self._write(base + self.REG["ENABLE"], int(enable))

        if enable:
            # Enable interrupts for the TSU
            self._write(base + self.REG["INT_ENABLE"], 1)

            # Clear any pending interrupts
            self._write(base + self.REG["INT_CLEAR"], 1)

        # Update internal TSU state
        self.tsu_state[idx] = enable

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: hasTimestamp
# ─────────────────────────────────────────────────────────────────────────────
    def hasTimestamp(self, idx: int) -> bool:
        """
        Checks whether a timestamp is available for the specified TSU.

        ### Args
        - **idx** (`int`): Index of the TSU to check.

        ### Returns
        - **bool**: `True` if a timestamp is available, `False` otherwise.
        """

        return self._read(self.base_addrs[idx] + self.REG["INT_CLEAR"]) > 0

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: getEventCount
# ─────────────────────────────────────────────────────────────────────────────
    def getEventCount(self, idx: int) -> int:
        """
        Returns the number of PPS events detected by the specified TSU.

        ### Args
        - **idx** (`int`): Index of the TSU to query.

        ### Returns
        - **int**: Number of events counted by the TSU.
        """

        return self._read(self.base_addrs[idx] + self.REG["EVENT_COUNT"])

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: readTimestamp
# ─────────────────────────────────────────────────────────────────────────────
    def readTimestamp(self, idx: int) -> tuple[int, int]:
        """
        Reads the timestamp from the specified TSU.

        Retrieves both the seconds and nanoseconds components of the timestamp,
        and clears the interrupt flag afterward.

        ### Args
        - **idx** (`int`): Index of the TSU to read from.

        ### Returns
        - **tuple[int, int]**: A tuple containing `(seconds, nanoseconds)`.
        """

        base = self.base_addrs[idx]

        # Read nanoseconds and seconds from the timestamp registers
        ns = self._read(base + self.REG["TS_NS"])
        s = self._read(base + self.REG["TS_S"])

        # Clear the interrupt flag after reading the timestamp
        self._write(base + self.REG["INT_CLEAR"], 1)

        return s, ns

    
# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: run
# ─────────────────────────────────────────────────────────────────────────────
    def run(self) -> None:
        """
        Main execution loop for the PPS monitoring thread.

        Initializes the system, monitors enabled TSUs for new timestamps,
        detects missed events, and sends metrics for each valid PPS signal.
        """

        self.setUp()

        # Initialize event counters for each active TSU
        counts = {i: self.getEventCount(i) if self.tsu_state[i] else 0 for i in self.pps_inputs}

        # Prime the timestamp registers by reading once
        for i in self.pps_inputs:
            if self.tsu_state[i]:
                self.readTimestamp(i)

        s0 = None
        start = nextCycle = datetime.now()

        while not self.event.is_set():
            for i in self.pps_inputs:
                if self.tsu_state[i]:
                    has_ts = self.hasTimestamp(i)
                    if has_ts:
                        count = self.getEventCount(i)

                        # Detect and report missed timestamps (optional)
                        if count - counts[i] > 1:
                            missed = count - counts[i] - 1
                            #self.send_metric(time.time_ns(), f"missed_timestamps_{i}", missed)

                        counts[i] = count

                        # Read and normalize timestamp
                        s, ns = self.readTimestamp(i)
                        if ns > 5e8:
                            s += 1
                            ns -= int(1e9)

                        if s0 is None:
                            s0 = s

                        # Send metric with current timestamp
                        self.send_metric(time.time_ns(), f"PPS_{i}", ns)

            # Wait until the next 0.5-second cycle
            nextCycle += timedelta(seconds=0.5)
            sleep = (nextCycle - datetime.now()).total_seconds()
            if sleep > 0:
                time.sleep(sleep)

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: stop
# ─────────────────────────────────────────────────────────────────────────────
    def stop(self) -> None:
        """
        Stops the PPS monitoring thread and releases resources.

        Disables all active TSUs, closes the UART connection if open,
        and calls the parent class's `stop` method.
        """

        # Disable all enabled TSUs
        for i in self.enabled_tsus:
            self.setEnable(i, False)

        # Close UART connection if open
        if self.uart:
            self.uart.close()

        # Call parent stop method
        super().stop()

