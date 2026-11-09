#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_core_view.py

**Project**: Syncarium Platform
**Description**: UI component for managing PTP synchronization, client loading, and logs.
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada
**License**: GPLv3
"""

import streamlit as st
from pathlib import Path
import yaml
from typing import Dict, Any

def render_sync_core(objs: Dict[str, Any]) -> None:
    """
    Renders the Synchronization Core UI in the Streamlit application.

    Args:
        objs (Dict[str, Any]): Dictionary containing initialized application objects, 
                                specifically "synccore".
    """
    main_container = st.container()
    
    with main_container:
        st.header("⏱️ Synchronization Core")
        
        core = objs["synccore"]
        
        st.subheader("📋 Current Status: Loaded PTP Clients")
        
        if core.loaded_clients:
            clients_status = []
            for client_name, data in core.loaded_clients.items():
                clients_status.append({
                    "Client": client_name,
                    "PID": data.get("pid", "N/A"),
                    "Namespace": data.get("namespace"),
                    "Interface": data.get("interface"),
                    "Status": data.get("status", "Loaded")
                })
            
            if clients_status:
                st.table(clients_status)
            else:
                st.info("No clients loaded.")
        else:
            st.info("No PTP clients loaded. Please load a configuration file first.")
        
        st.markdown("---")
        
        st.subheader("📂 Configuration Management")
        
        presets = [
            f.name for f in Path(core.ptp_profile_dir).glob("*.yaml")
        ]
        
        if presets:
            st.write("**Presets available in configuration directory:**")
            selected_preset = st.selectbox("Select a Preset Configuration", presets)
            
            if selected_preset:
                with st.expander(f"🔍 Preview: {selected_preset}", expanded=False):
                    try:
                        preset_path = Path(core.ptp_profile_dir) / selected_preset
                        with open(preset_path, 'r') as f:
                            content = yaml.safe_load(f)
                        st.json(content)
                    except Exception as e:
                        st.error(f"Could not preview file: {e}")

            if st.button("🚀 Load and Start PTP from Preset"):
                with st.spinner("Loading and starting PTP..."):
                    if core.load_clients(file_cfg=selected_preset):
                        processes = core.start_ptp(stop_existing=True)
                        if processes:
                            st.success("PTP processes launched successfully.")
                            st.rerun()
                        else:
                            st.error("Configuration loaded but no processes were launched.")
                    else:
                        st.error("Failed to load configuration.")
        
        st.markdown("---")
        st.write("**Or upload a custom configuration:**")
        uploaded_file = st.file_uploader("Upload PTP Configuration (YAML)", type=["yaml"])
        
        if uploaded_file:
            with st.expander("🔍 Preview Uploaded File", expanded=False):
                try:
                    content = yaml.safe_load(uploaded_file)
                    st.json(content)
                except Exception as e:
                    st.error(f"Invalid YAML format: {e}")

            if st.button("🚀 Load and Start PTP from Upload"):
                with st.spinner("Loading and starting PTP..."):
                    if core.load_clients(file_cfg=uploaded_file.name):
                        processes = core.start_ptp(stop_existing=True)
                        if processes:
                            st.success("PTP processes launched successfully.")
                            st.rerun()
                        else:
                            st.error("Configuration loaded but no processes were launched.")
                    else:
                        st.error("Failed to load uploaded configuration.")

        st.markdown("---")
        
        st.subheader("📡 Connectivity & Logs")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📡 Ping PTP Server"):
                results = core.ping_server()
                if results:
                    for res in results:
                        if "Error" in res["status"]:
                            st.error(f"{res['client']}: {res['status']}")
                        else:
                            st.success(f"{res['client']}: {res['status']}")
                            st.caption(f"Output: {res['output']}")
                else:
                    st.warning("No clients loaded to ping.")

        with col2:
            if core.loaded_clients:
                selected_client = st.selectbox("Select Client to View Logs", options=list(core.loaded_clients.keys()))
                if st.button("📄 Show PTP Logs"):
                    log_content = core.show_logs(selected_client)
                    st.info(f"Showing last 100 lines of {selected_client}")
                    st.code(log_content, language="log")
            else:
                st.warning("No clients loaded to view logs.")

        st.markdown("---")
        
        st.subheader("⚠️ Cleanup Operations")
        st.warning("The following action will stop all PTP processes and delete all log files.")
        if st.button("🛑 STOP ALL PTP", type="primary", use_container_width=True):
            if core.stop_ptp(preconfirmation=True):
                st.success("All PTP processes stopped and logs cleared.")
                st.rerun()
            else:
                st.error("Error occurred while stopping PTP.")