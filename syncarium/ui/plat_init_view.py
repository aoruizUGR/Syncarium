#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plat_init_view.py

**Project**: Syncarium Platform
**Description**: UI component for managing network namespaces and device drivers.
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada
**License**: GPLv3
"""

import streamlit as st
from pathlib import Path
import yaml
import subprocess
from typing import List, Dict, Any

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

def render_plat_init(objs: Dict[str, Any]) -> None:
    """
    Renders the Platform Initialization UI.

    Args:
        objs (Dict[str, Any]): Dictionary containing initialized application objects, 
                                specifically "platinit".
    """
    # Envolvemos todo el contenido en un contenedor para aislar la vista
    # y evitar que residuos de otras pestañas se mezclen.
    main_container = st.container()
    
    with main_container:
        st.header("⚙️ Platform Initialization")
        
        # Access pure logic via objs
        plat = objs["platinit"]
        
        # --- Summary Panel ---
        st.subheader("📋 Current Status: Active Namespaces")
        # Call the system directly to see what's running
        namespaces_data = get_active_namespaces_table()
        if namespaces_data:
            st.table(namespaces_data)
        else:
            st.info("No namespaces currently active in the system.")
        
        st.markdown("---")
        
        # --- Namespace Management ---
        st.subheader("🌐 Namespace Management")
        
        # List existing presets in the config directory
        presets = [
            f.name for f in Path(plat.config_dir).glob("*.yaml")
        ]
        
        if presets:
            st.write("**Presets available in configuration directory:**")
            selected_preset = st.selectbox("Select a Preset Configuration", presets)
            
            if selected_preset:
                with st.expander(f"🔍 Preview: {selected_preset}", expanded=False):
                    try:
                        preset_path = Path(plat.config_dir) / selected_preset
                        with open(preset_path, 'r') as f:
                            content = yaml.safe_load(f)
                        st.json(content)
                    except Exception as e:
                        st.error(f"Could not preview file: {e}")

            if st.button("🚀 Start Namespaces from Preset"):
                with st.spinner("Processing preset..."):
                    success = plat.start_namespaces(file_cfg=selected_preset)
                    if success:
                        st.success(f"Preset '{selected_preset}' started successfully.")
                        st.rerun()
                    else:
                        st.error("Failed to start preset.")
        
        st.markdown("---")
        st.write("**Or upload a custom configuration:**")
        uploaded_file = st.file_uploader("Upload Namespace Configuration (YAML)", type=["yaml"])
        
        if uploaded_file:
            with st.expander("🔍 Preview Uploaded File", expanded=False):
                try:
                    content = yaml.safe_load(uploaded_file)
                    st.json(content)
                except Exception as e:
                    st.error(f"Invalid YAML format: {e}")

            if st.button("🚀 Start Namespaces from Upload"):
                with st.spinner("Processing upload..."):
                    success = plat.start_namespaces(file_cfg=uploaded_file.name)
                    if success:
                        st.success("Uploaded namespaces started successfully.")
                        st.rerun()
                    else:
                        st.error("Failed to start uploaded configuration.")

        # --- Danger Zone / Cleanup ---
        st.markdown("---")
        st.subheader("⚠️ Cleanup Operations")
        st.warning("The following action will permanently delete all active network namespaces.")
        if st.button("🛑 STOP ALL NAMESPACES", type="primary", use_container_width=True):
            if plat.stop_namespaces():
                st.success("All namespaces successfully deleted.")
                st.rerun()
            else:
                st.error("Error occurred while stopping namespaces.")

        st.markdown("---")
        
        # --- Driver Management ---
        st.subheader("📦 Driver Management")
        drivers = [
            f.stem[len("devdriver_"):]
            for f in Path(plat.scripts_dir).glob("devdriver_*.sh")
        ]
        
        if drivers:
            selected_driver = st.selectbox("Select Driver to Load", drivers)
            if st.button("🚀 Load Selected Driver"):
                success = plat.load_device_driver(selected_driver)
                if success:
                    st.success(f"Driver '{selected_driver}' loaded successfully.")
                    st.rerun()
                else:
                    st.error("Failed to load driver.")
        else:
            st.warning("No drivers found in scripts directory.")