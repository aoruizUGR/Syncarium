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
    lm = objs["local_manager"]
    st.header("🛠️ Local Manager Control")

    tab1, tab2, tab3 = st.tabs([
        "🌐 Network Infrastructure",
        "⏱️ PTP Management",
        "⚠️ Cleanup & Operations"
    ])

    with tab1:
        st.subheader("Network Infrastructure")
        namespaces_data = get_active_namespaces_table()
        if namespaces_data:
            st.table(namespaces_data)
        else:
            st.info("No active network namespaces detected.")
        
        with st.expander("🏗️ Namespace Management", expanded=True):
            st.markdown("### Manage Network Namespaces")
            col_ns1, col_ns2 = st.columns(2)
            with col_ns1:
                st.markdown("**Presets**")
                ns_presets = [f.name for f in Path(lm.config_dir).glob("*.yaml")]
                if ns_presets:
                    selected_ns_preset = st.selectbox("Select Namespace Configuration", ns_presets)
                    if st.button("🚀 Start Namespaces from Preset"):
                        with st.spinner("Deploying namespaces..."):
                            success, error_msg = lm.start_namespaces(file_cfg=selected_ns_preset)
                            if success:
                                placeholder = st.empty()
                                for i in range(3, 0, -1):
                                    placeholder.success(f"Success! Refreshing in {i}s...")
                                    time.sleep(1)
                                st.rerun()
                            else:
                                st.error(error_msg)
                else:
                    st.warning("No namespace presets found in config directory.")

            with col_ns2:
                st.markdown("**Custom Upload**")
                uploaded_ns_file = st.file_uploader("Upload Custom Namespace Config", type=["yaml"], key="ns_upload")
                if uploaded_ns_file:
                    if st.button("🚀 Start Namespaces from Upload", key="ns_upload_btn"):
                        with st.spinner("Deploying..."):
                            success, error_msg = lm.start_namespaces(file_cfg=uploaded_ns_file.name)
                            if success:
                                placeholder = st.empty()
                                for i in range(3, 0, -1):
                                    placeholder.success(f"Success! Refreshing in {i}s...")
                                    time.sleep(1)
                                st.rerun()
                            else:
                                st.error(error_msg)

    with tab2:
        st.subheader("PTP Client Status")
        if lm.loaded_clients:
            clients_status = []
            for client_name, data in lm.loaded_clients.items():
                clients_status.append({
                    "Client": client_name,
                    "PID": str(data.get("pid", "N/A")),
                    "Namespace": data.get("namespace"),
                    "Interface": data.get("interface"),
                    "Status": data.get("status", "Loaded")
                })
            st.table(clients_status)
        else:
            st.info("No PTP clients loaded. Use the configuration section below.")

        st.markdown("---")
        
        with st.expander("📡 PTP Configuration", expanded=True):
            st.markdown("### Configuration")
            ptp_presets = [f.name for f in Path(lm.ptp_profile_dir).glob("*.yaml")]
            if ptp_presets:
                selected_ptp_preset = st.selectbox("Select PTP Configuration", ptp_presets)
                if st.button("🚀 Load and Start PTP from Preset"):
                    with st.spinner("Loading and starting PTP..."):
                        if lm.load_clients(file_cfg=selected_ptp_preset):
                            processes = lm.start_ptp(stop_existing=True)
                            if processes:
                                placeholder = st.empty()
                                for i in range(3, 0, -1):
                                    placeholder.success(f"PTP processes launched successfully! Refreshing in {i}s...")
                                    time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Configuration loaded but no processes were launched.")
                        else:
                            st.error("Failed to load configuration.")
            else:
                st.warning("No PTP presets found in profile directory.")

            uploaded_ptp_file = st.file_uploader("Upload Custom PTP Config", type=["yaml"], key="ptp_upload")
            if uploaded_ptp_file:
                if st.button("🚀 Load and Start PTP from Upload", key="ptp_upload_btn"):
                    with st.spinner("Loading and starting PTP..."):
                        if lm.load_clients(file_cfg=uploaded_ptp_file.name):
                            processes = lm.start_ptp(stop_existing=True)
                            if processes:
                                placeholder = st.empty()
                                for i in range(3, 0, -1):
                                    placeholder.success(f"PTP processes launched successfully! Refreshing in {i}s...")
                                    time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Configuration loaded but no processes were launched.")
                        else:
                            st.error("Failed to load configuration.")

        with st.expander("🛠️ Connectivity Tools", expanded=True):
            st.markdown("### Tools")
            if lm.loaded_clients:
                # Ping
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

                # Logs
                selected_client = st.selectbox("Select Client to View Logs", options=list(lm.loaded_clients.keys()))
                if st.button("📄 Show PTP Logs"):
                    log_content = lm.show_logs(selected_client)
                    st.info(f"Showing last 100 lines of {selected_client}")
                    st.code(log_content, language="log")
            else:
                st.warning("No clients loaded to view logs.")

    with tab3:
        st.subheader("Cleanup & Operations")
        st.warning("⚠️ **Danger Zone**: The following actions will stop all PTP processes and delete all network namespaces.")
        col_stop1, col_stop2 = st.columns(2)
        with col_stop1:
            if st.button("Stop all PTP", type="primary", use_container_width=True):
                if lm.stop_ptp(preconfirmation=True):
                    placeholder = st.empty()
                    for i in range(3, 0, -1):
                        placeholder.success(f"All PTP processes stopped and logs cleared! Refreshing in {i}s...")
                        time.sleep(1)
                    st.rerun()
                else:
                    st.error("Error occurred while stopping PTP.")
        with col_stop2:
            if st.button("Stop all Namespaces", type="primary", use_container_width=True):
                success, error_msg = lm.stop_namespaces()
                if success:
                    placeholder = st.empty()
                    for i in range(3, 0, -1):
                        placeholder.success(f"Namespaces deleted! Refreshing in {i}s...")
                        time.sleep(1)
                    st.rerun()
                else:
                    st.error(error_msg)