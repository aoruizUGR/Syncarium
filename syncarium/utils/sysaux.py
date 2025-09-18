#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# sysaux.py

**Project**: Syncarium - Intelligent Timing Platform Toolkit  
**Description**: System auxiliar utilities.  
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada  
**Created**: 2025-06-06  
**Version**: 1.0.0  
**License**: GPLv3
"""


# ─────────────────────────────────────────────────────────────────────────────
# Standard Library Imports
import os
import platform
import glob
from typing import Optional, List

# ─────────────────────────────────────────────────────────────────────────────
# Third-Party Imports
from rich.console import Console

# ─────────────────────────────────────────────────────────────────────────────
# Local Application Imports
# (None used directly in this file)

# ─────────────────────────────────────────────────────────────
# 🧠 System Auxiliar Class
# ─────────────────────────────────────────────────────────────
class SysAuxiliar:
    """
        Provides system-level utilities for Syncarium, including hardware inspection
        and temperature monitoring.

        ### Attributes
        - **console** (`Console`): Rich Console instance used for output rendering.
    """

# ─────────────────────────────────────────────────────────────────────────────
# 🚧 Function: constructor
# ─────────────────────────────────────────────────────────────────────────────
    def __init__(self, console: Optional[Console] = None) -> None:
        """
        Initializes the system utility class with optional console output.

        ### Args
        - **console** (`Optional[Console]`): Rich Console instance for output.
        If not provided, a default Console is created.
        """

        self.console: Console = console or Console()
        
# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: get_pci_device
# ─────────────────────────────────────────────────────────────────────────────
    def get_pci_device(self, interface: str) -> str:
        """
        Retrieves the PCI device ID associated with a given network interface.

        Resolves the symbolic link from `/sys/class/net/{interface}/device` to its
        corresponding PCI device path and extracts the PCI ID. Returns "Unknown"
        if the operation fails.

        ### Args
        - **interface** (`str`): Name of the network interface (e.g., `"eth0"`).

        ### Returns
        - `str`: PCI device ID or `"Unknown"` if not found.
        """

        try:
            device_path = os.path.realpath(f'/sys/class/net/{interface}/device')
            pci_id = os.path.basename(device_path)
            return pci_id
        except Exception:
            return "Unknown"
        
# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: get_cpu_model
# ─────────────────────────────────────────────────────────────────────────────
    def get_cpu_model(self) -> str:
        """
        Retrieves the CPU model name from the system.

        Attempts to read the model name from `/proc/cpuinfo`. If unavailable,
        falls back to `platform.processor()`.

        ### Returns
        - `str`: CPU model name or `"Unknown"` if it cannot be determined.
        """

        try:
            # Read CPU model from /proc/cpuinfo
            with open('/proc/cpuinfo') as f:
                for line in f:
                    if line.startswith('model name'):
                        return line.split(':')[1].strip()
        except Exception:
            # Fallback if reading fails
            return platform.processor() or "Unknown"
        
# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: get_temperatures
# ─────────────────────────────────────────────────────────────────────────────
    def get_temperatures(self) -> list[dict[str, Optional[str]]]:
        """
        Reads system temperature sensors from `/sys/class/hwmon`.

        Iterates through available hwmon devices, identifies sensor names,
        and reads temperature values. Converts millidegree Celsius readings
        to Celsius and returns structured sensor data.

        ### Returns
        - `List[Dict[str, Optional[str]]]`: List of temperature readings with
        sensor name, label, and temperature in Celsius.
        """

        sensors = []

        # Iterate over all hwmon devices
        for hwmon_path in glob.glob("/sys/class/hwmon/hwmon*"):
            try:
                # Try to read the sensor name
                with open(os.path.join(hwmon_path, "name")) as f:
                    sensor_name = f.read().strip()
            except FileNotFoundError:
                sensor_name = "unknown"

            # Look for all temperature input files
            for temp_input in glob.glob(os.path.join(hwmon_path, "temp*_input")):
                try:
                    # Extract the temperature sensor number (e.g., '1' from 'temp1_input')
                    temp_num = temp_input.split("_")[0][-1]
                    label_path = os.path.join(hwmon_path, f"temp{temp_num}_label")

                    # Try to read the label if it exists
                    if os.path.exists(label_path):
                        with open(label_path) as f:
                            label = f.read().strip()
                    else:
                        label = f"temp{temp_num}"

                    # Read the temperature in millidegrees Celsius and convert to Celsius
                    with open(temp_input) as f:
                        temp_millicelsius = int(f.read().strip())
                        temperature = temp_millicelsius / 1000.0

                    # Store sensor data
                    sensors.append({
                        "sensor": sensor_name,
                        "label": label,
                        "temperature": temperature
                    })
                except Exception as e:
                    print(f"Error reading {temp_input}: {e}")
        
        return sensors
    
# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: format_columns_with_bullets
# ─────────────────────────────────────────────────────────────────────────────
    def format_columns_with_bullets(
        self,
        items: List[str],
        columns: int = 3,
        width: int = 35,
        indent: int = 4
    ) -> str:        
        """
        Formats a list of strings into multiple columns with bullet points.

        Arranges the items into a grid-like structure with a specified number of columns,
        applying indentation and fixed-width formatting for alignment. If the list is empty,
        a placeholder message is returned.

        ### Args
        - **items** (`List[str]`): List of strings to format.
        - **columns** (`int`): Number of columns to display. Defaults to 3.
        - **width** (`int`): Width allocated to each column. Defaults to 35.
        - **indent** (`int`): Number of spaces to indent each row. Defaults to 4.

        ### Returns
        - `str`: Formatted string with bullet points arranged in columns.
        """

        if not items:
            return " " * indent + "• None"
        
        # Split items into rows based on the number of columns
        rows = [items[i:i + columns] for i in range(0, len(items), columns)]
        indent_space = " " * indent

        # Format each row with bullets and spacing
        return "\n".join(
            indent_space + "   ".join(f"• {item:<{width - 2}}" for item in row)
            for row in rows
        )