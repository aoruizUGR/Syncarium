#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# tui.py

**Project**: Syncarium - Intelligent Timing Platform Toolkit  
**Description**: Syncarium TUI entry point  
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada  
**Created**: 2025-05-22  
**Version**: 1.1.0  
**License**: GPLv3
"""


# ─────────────────────────────────────────────────────────────────────────────
# Standard Library Imports
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# Third-Party Imports
from rich.console import Console

# ─────────────────────────────────────────────────────────────────────────────
# Local Application Imports
from syncarium.utils import ViewTools
from syncarium.core import PlatInit, SyncCore, LoadGen, DataEx, ExpOrchestra


# ─────────────────────────────────────────────────────────────
# 🖥️ TUI App Class
# ─────────────────────────────────────────────────────────────
class TuiApp:
    """
    A Text-based User Interface (TUI) application that initializes and manages
    various interactive console-based tools.

    This class serves as the main entry point for a TUI application, setting up
    different modules such as Platform Initialization, PTP management, traffic generation,
    data extraction, and utility functions.

    ### Attributes:
    - **console** (`Console`): The console object used for rendering output.
    - **platinit** (`PlatInit`): Manages Platform Initialization options.
    - **synccore** (`SyncCore`): Manages the Precision Time Protocol (PTP) menu.
    - **loadgen** (`LoadGen`): Manages the traffic generator menu.
    - **dataex** (`DataEx`): Handles the data extraction tool menu.
    - **exporchestra** (`ExpOrchestra`): Automatization of an experiment.
    - **vt** (`ViewTools`): Provides utility functions for the TUI.
    """


# ─────────────────────────────────────────────────────────────
# 🚧 Function: constructor
# ─────────────────────────────────────────────────────────────
    def __init__(self, console: Optional[Console] = None) -> None:
        """
        Initializes the TuiApp with an optional custom console.

        ### Args:
        - **console** (`Optional[Console]`): A custom console instance for output.  
        If not provided, a default `Console` instance is used.
        """

        
        # Use provided console or create a default one
        self.console: Console = console or Console()

        # Utility view tools
        self.vt: ViewTools = ViewTools(console=self.console, version="1.0.0")

        # Initialize each menu/tool with the shared console instance
        self.platinit: PlatInit = PlatInit(self.vt)
        self.synccore: SyncCore = SyncCore(self.vt)
        self.loadgen: LoadGen = LoadGen(self.vt)
        self.dataex: DataEx = DataEx(self.vt)

        # Laboratory tool depends on other modules
        self.exporchestra: ExpOrchestra = ExpOrchestra(
            self.synccore,
            self.loadgen,
            self.dataex,
            self.vt
        )

# ─────────────────────────────────────────────────────────────────────────────
# 🚀 Function: main
# ─────────────────────────────────────────────────────────────────────────────    
    def main(self) -> None:
        """
        Displays the main interactive menu of the TUI application and handles user navigation.

        This method runs an interactive loop that presents the main menu to the user,
        displays system information, and routes the user to the selected submenu.
        It gracefully handles keyboard interruptions (e.g., Ctrl+C).

        ### Menu Options:
        - ⚙️ PlatInit ----- Platform Initialization → `platinit.main_menu`
        - ⏱️ SyncCore ----- Synchronization Core → `synccore.main_menu`
        - 🚦 LoadGen ------ Load Generator → `loadgen.main_menu`
        - 📈 DataEx ------- Data Extractor → `dataex.main_menu`
        - 🧪 ExpOrchestra - Experiment Orchestration → `exporchestra.main_menu`
        - 🔄 Refresh View → `vt.refresh_view`
        - ❌ Exit → `exit`
                
        ### Notes:
        - Graceful exit is handled via **Ctrl+C**.
        """

        loop = True
        try:
            while loop:

                # Display software title
                self.vt.console_software_title()

                # Display software subtitle
                self.vt.console_software_subtitle()

                # Display platform information
                self.vt.panel_platform_info()

                # Print the menu title with formatting
                self.vt.console_message("main_title","Main Syncarium Menu", indent=0)

                # Interactive menu with InquirerPy
                choice = self.vt.console_select_menu(
                    choices= [
                        {"name": "⚙️ PlatInit ----- Platform Initialization", "value": "platinit"},
                        {"name": "⏱️ SyncCore ----- Synchronization Core", "value": "synccore"},
                        {"name": "🚦 LoadGen ------ Load Generator", "value": "loadgen"},
                        {"name": "📈 DataEx ------- Data Extractor", "value": "dataex"},
                        {"name": "🧪 ExpOrchestra - Experiment Orchestration", "value": "exporchestra"},
                        {"name": "🔄 Refresh View", "value": "refresh_view"},
                        {"name": "❌ Exit", "value": "exit"},
                    ],
                    indent=1
                )
                
                submenu = {
                    "platinit":     self.platinit.main_menu,
                    "synccore":     self.synccore.main_menu,
                    "loadgen":    self.loadgen.main_menu,
                    "dataex":       self.dataex.main_menu,
                    "exporchestra":    self.exporchestra.main_menu,
                    "refresh_view": self.vt.refresh_view,
                    "exit":         self.exit
                }

                submenu.get(choice)()
                if choice == "exit":
                    break

        except KeyboardInterrupt:
            # Handle Ctrl+C interruption gracefully
            self.exit()

# ─────────────────────────────────────────────────────────────────────────────
# 🚀 Function: exit
# ─────────────────────────────────────────────────────────────────────────────
    def exit(self) -> None:
        """
        Performs cleanup operations before exiting the TUI application.

        This method stops active processes such as data extraction and traffic generation,
        and displays exit messages to the user. Some cleanup steps are commented out
        and may be enabled as needed.
        """

        # Inform the user that cleanup is starting
        self.vt.console_message("info", "Cleaning up:", indent=0)

        # Stop data extraction process
        self.dataex.stop_extraction()

        # Optional cleanup steps (currently disabled)
        # self.synccore.stop_ptp()
        # self.platinit.stop_namespaces()

        # Stop traffic generator server
        #self.loadgen.stop_trex_server()

        # Display exit message
        self.vt.console_message("exit", "Bye!", indent=0)

