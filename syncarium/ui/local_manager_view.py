#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
local_manager_view.py

**Project**: Syncarium Platform
**Description**: UI component for managing both network namespaces and PTP clients.
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada
**License**: GPLv3
"""

import streamlit as st
from pathlib import Path
import yaml
import subprocess
from typing import List, Dict, Any
import time

def get_active_namespaces_table() -> List[Dict[str, str]]:
    """
    Fetches active network namespaces and returns a list of dictionaries 
    containing detailed information for display in a Streamlit table.

    Returns:
        List[Dict[str, str]]: A list of dictionaries with Namespace, Interface, 
                               IP Address, MAC Address, and Gateway info.
    """
    try:
        # Get the list of network namespaces
        result = subprocess.run(["ip", "netns", "list"], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        data = []
        
        if lines and lines[0]:
            for line in lines:
                ns = line.split()[0]
                
                # Default values
                iface = "N/A"
                ip = "N/A"
                mac = "N/A"
                gw = "N/A"

                # Get interfaces in the namespace
                try:
                    interfaces_result = subprocess.run(
                        ["sudo", "ip", "netns", "exec", ns, "ip", "-o", "link", "show"],
                        capture_output=True, text=True, check=True
                    )
                    interfaces = interfaces_result.stdout.strip().split('\n')
                    
                    # We assume the primary interface is the first non-loopback one
                    for if_line in interfaces:
                        parts = if_line.split()
                        if len(parts) >= 2:
                            current_iface = parts[1].strip(':')
                            if current_iface != "lo":
                                iface = current_iface
                                break
                    
                    if iface != "N/A":
                        # Get MAC address
                        mac_result = subprocess.run(
                            ["sudo", "ip", "netns", "exec", ns, "ip", "link", "show", iface],
                            capture_output=True, text=True, check=True
                        )
                        mac_line = next((l for l in mac_result.stdout.splitlines() if "link/ether" in l), None)
                        if mac_line:
                            mac = mac_line.split()[1]

                        # Get IP addresses
                        ip_result = subprocess.run(
                            ["sudo", "ip", "netns", "exec", ns, "ip", "-o", "-4", "addr", "show"],
                            capture_output=True, text=True, check=True
                        )
                        ips = ip_result.stdout.strip().split('\n')
                        for ip_line in ips:
                            if iface in ip_line:
                                parts = ip_line.split()
                                if len(parts) >= 4:
                                    ip = parts[3]
                                    break

                        # Get default gateways
                        gw_result = subprocess.run(
                            ["sudo", "ip", "netns", "exec", ns, "ip", "route", "show", "default"],
                            capture_output=True, text=True, check=True
                        )
                        gws = gw_result.stdout.strip().split('\n')
                        for gw_line in gws:
                            if "via" in gw_line:
                                parts = gw_line.split()
                                if len(parts) >= 3:
                                    gw = parts[2]
                                    break
                except subprocess.CalledProcessError:
                    pass # Keep default N/A values on failure

                data.append({
                    "Namespace": ns,
                    "Interface": iface,
                    "IP Address": ip,
                    "MAC Address": mac,
                    "Gateway": gw
                })
        return data
    except Exception:
        return []

def render_local_manager(objs: Dict[str, Any]) -> None:
    """
    Renders the Unified Local Manager UI.
    
    Args:
        objs (Dict[str, Any]): Dictionary containing initialized application objects, 
                                specifically "local_manager".
    """
    main_container = st.container()
    
    with main_container:
        st.header("🛠️ Local Manager Control")
        lm = objs["local_manager"]
        
        # --- SECTION 1: Network Status ---
        st.subheader("🌐 Network Infrastructure")
        namespaces_data = get_active_namespaces_table()
        if namespaces_data:
            st.table(namespaces_data)
        else:
            st.info("No active network namespaces detected.")
        
        st.markdown("---")
        
        # --- SECTION 2: Namespace Management ---
        st.subheader("🏗️ Namespace Management")
        
        # Presets for Namespaces
        ns_presets = [f.name for f in Path(lm.config_dir).glob("*.yaml")]
        if ns_presets:
            selected_ns_preset = st.selectbox("Select Namespace Configuration", ns_presets)
            if st.button("🚀 Start Namespaces from Preset"):
                with st.spinner("Deploying namespaces..."):
                    success, error_msg = lm.start_namespaces(file_cfg=selected_ns_preset)
                    if success:
                        for i in range(3, 0, -1):
                            st.success(f"Success! Refreshing in {i}s...")
                            time.sleep(1)
                        st.rerun()
                    else:
                        st.error(error_msg)
        
        # Upload for Namespaces
        uploaded_ns_file = st.file_uploader("Upload Custom Namespace Config", type=["yaml"], key="ns_upload")
        if uploaded_ns_file:
            if st.button("🚀 Start Namespaces from Upload", key="ns_upload_btn"):
                with st.spinner("Deploying..."):
                    success, error_msg = lm.start_namespaces(file_cfg=uploaded_ns_file.name)
                    if success:
                        st.rerun()
                    else:
                        st.error(error_msg)

        # --- SECTION 3: PTP Client Status ---
        st.markdown("---")
        st.subheader("⏱️ PTP Client Status")
        
        if lm.loaded_clients:
            clients_status = []
            for client_name, data in lm.loaded_clients.items():
                clients_status.append({
                    "Client": client_name,
                    "PID": data.get("pid", "N/A"),
                    "Namespace": data.get("namespace"),
                    "Interface": data.get("interface"),
                    "Status": data.get("status", "Loaded")
                })
            st.table(clients_status)
        else:
            st.info("No PTP clients loaded. Use the 'PTP Configuration' section below.")

        st.markdown("---")
        
        # --- SECTION 4: PTP Management ---
        st.subheader("📡 PTP Configuration & Operations")
        
        # PTP Presets
        ptp_presets = [f.name for f in Path(lm.ptp_profile_dir).glob("*.yaml")]
        if ptp_presets:
            selected_ptp_preset = st.selectbox("Select PTP Configuration", ptp_presets)
            if st.button("🚀 Load and Start PTP from Preset"):
                with st.spinner("Loading and starting PTP..."):
                    if lm.load_clients(file_cfg=selected_ptp_preset):
                        processes = lm.start_ptp(stop_existing=True)
                        if processes:
                            st.success("PTP processes launched successfully.")
                            st.rerun()
                        else:
                            st.error("Configuration loaded but no processes were launched.")
                    else:
                        st.error("Failed to load configuration.")
        
        # PTP Upload
        uploaded_ptp_file = st.file_uploader("Upload Custom PTP Config", type=["yaml"], key="ptp_upload")
        if uploaded_ptp_file:
            if st.button("🚀 Load and Start PTP from Upload", key="ptp_upload_btn"):
                with st.spinner("Loading and starting PTP..."):
                    if lm.load_clients(file_cfg=uploaded_ptp_file.name):
                        processes = lm.start_ptp(stop_existing=True)
                        if processes:
                            st.rerun()
                        else:
                            st.error("Configuration loaded but no processes were launched.")
                    else:
                        st.error("Failed to load configuration.")

        # PTP Connectivity Tools
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📡 Ping PTP Server"):
                results = lm.ping_server()
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
            if lm.loaded_clients:
                selected_client = st.selectbox("Select Client to View Logs", options=list(lm.loaded_clients.keys()))
                if st.button("📄 Show PTP Logs"):
                    log_content = lm.show_logs(selected_client)
                    st.info(f"Showing last 100 lines of {selected_client}")
                    st.code(log_content, language="log")
            else:
                st.warning("No clients loaded to view logs.")

        st.markdown("---")
        
        # --- SECTION 5: Danger Zone ---
        st.subheader("⚠️ Cleanup Operations")
        st.warning("The following actions will stop all PTP processes and delete all network namespaces.")
        col_stop1, col_stop2 = st.columns(2)
        with col_stop1:
            if st.button("🛑 STOP ALL PTP", type="primary", use_container_width=True):
                if lm.stop_ptp(preconfirmation=True):
                    st.success("All PTP processes stopped and logs cleared.")
                    st.rerun()
                else:
                    st.error("Error occurred while stopping PTP.")
        with col_stop2:
            if st.button("🧨 DELETE ALL NAMESPACES", type="primary", use_container_width=True):
                success, error_msg = lm.stop_namespaces()
                if success:
                    for i in range(3, 0, -1):
                        st.success(f"Namespaces deleted! Refreshing in {i}s...")
                        time.sleep(1)
                    st.rerun()
                else:
                    st.error(error_msg)