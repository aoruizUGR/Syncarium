#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py

**Project**: Syncarium Platform
**Description**: Main entry point for the Syncarium platform web interface using Streamlit.
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada
**License**: GPLv3
"""

import streamlit as st
from typing import Any, Dict
from syncarium.core import PlatInit, SyncCore, LoadGen, DataEx, ExpOrchestra, MonHub
from syncarium.utils import ViewTools, TelegramBot

from syncarium.ui import (
    render_dashboard,
    render_plat_init,
    render_sync_core,
    render_load_gen,
    # render_data_ex,
    # render_mon_hub,
    # render_exp_orchestra
)

def initialize_session_state() -> None:
    """
    Initializes the Streamlit session state with core application objects.
    
    Sets up shared instances for view tools, telegram bot, and core logic 
    components (PlatInit, SyncCore, etc.) to be accessed across different views.
    """
    if "app_objects" not in st.session_state:
        vt = ViewTools(console=None, version="1.0.0")
        tb = TelegramBot()
        
        # Initialize pure logic objects
        st.session_state.app_objects = {
            "vt": vt, 
            "tb": tb,
            "platinit": PlatInit(),
            "synccore": SyncCore(),
            "loadgen": LoadGen(),
            # "dataex": DataEx(),
            # "monhub": MonHub(),
            # "exporchestra": ExpOrchestra(
            #    st.session_state.app_objects["synccore"],
            #    st.session_state.app_objects["loadgen"],
            #    st.session_state.app_objects["dataex"],
            #    vt,
            #    tb
            # )
        }

def main() -> None:
    """
    Main execution function for the Streamlit application.
    
    Configures the page, initializes the state, handles the sidebar 
    navigation menu, and renders the selected view.
    """
    st.set_page_config(page_title="Syncarium Platform", page_icon="⏱️", layout="wide")
    initialize_session_state()
    objs: Dict[str, Any] = st.session_state.app_objects

    st.title("⏱️ Syncarium Platform")
    
    menu = st.sidebar.selectbox(
        "Navigation Menu",
        ["Dashboard", "⚙️ PlatInit", "⏱️ SyncCore", "🚦 LoadGen", 
         "📈 DataEx", "📊 MonHub", "🧪 ExpOrchestra"]
    )

    # Mapping menu titles to their respective UI functions
    views = {
        "Dashboard": render_dashboard,
        "⚙️ PlatInit": render_plat_init,
        "⏱️ SyncCore": render_sync_core,
        "🚦 LoadGen": render_load_gen,
        # "📈 DataEx": render_data_ex,
        # "📊 MonHub": render_mon_hub,
        # "🧪 ExpOrchestra": render_exp_orchestra
    }

    # Render the selected view if it exists in our views dictionary
    if menu in views:
        views[menu](objs)
    else:
        st.warning(f"The module '{menu}' is not yet implemented.")

    st.sidebar.markdown("---")
    if st.sidebar.button("🛑 Emergency Shutdown"):
        if "dataex" in objs and hasattr(objs["dataex"], "stop_extraction"):
            objs["dataex"].stop_extraction()
        st.error("Cleanup initiated.")
        st.rerun()

if __name__ == "__main__":
    main()