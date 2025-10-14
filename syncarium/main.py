#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# main.py

**Project**: Syncarium - Intelligent Timing Platform Toolkit  
**Description**: Entry point for launching TUI or TUI interface  
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada  
**Created**: 2025-05-23  
**Version**: 1.2.0  
**License**: GPLv3
"""


# ─────────────────────────────────────────────────────────────────────────────
# Standard Library Imports
import sys
import platform

# ─────────────────────────────────────────────────────────────────────────────
# Third-Party Imports
# (None used directly in this file)

# ─────────────────────────────────────────────────────────────────────────────
# Local Application Imports
# (None used directly in this file)


# ─────────────────────────────────────────────────────────────
# 📌 Function: check_os
# ─────────────────────────────────────────────────────────────
def check_os():
    """
    Check if the operating system is Linux.

    If the current operating system is not Linux, print a message and exit the program.

    This function is useful for ensuring that a script only runs in a Linux environment.
    """
    if platform.system() != "Linux":
        print("This script can only be run on Linux.")
        sys.exit(1)

# ─────────────────────────────────────────────────────────────
# 📌 Function: launch_tui
# ─────────────────────────────────────────────────────────────
def launch_tui():
    """
    Launches the Textual User Interface (TUI) version of Syncarium.

    This function imports and executes the main entry point of the TUI
    application, which is implemented using the Rich library.
    """
    from syncarium import TuiApp
    tui = TuiApp()
    tui.main()

# ─────────────────────────────────────────────────────────────
# 📌 Function: main
# ─────────────────────────────────────────────────────────────
def main():
    """
    Main entry point for Syncarium.
    """
    check_os()

    launch_tui()

# ─────────────────────────────────────────────────────────────
# 🚀 Main
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
