#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
traffic_generator_view.py

**Project**: Syncarium Platform
**Description**: UI component for managing traffic generators.
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada
**License**: GPLv3
"""

import streamlit as st
from typing import Dict, Any
import time
import path_config.global_paths as global_paths
import os


def display_port_config(port_attrs: Dict[str, Any]) -> None:
    """
    Renders port configuration in a table.

    Args:
        port_attrs (Dict[str, Any]): Dictionary containing port attributes.
    """
    st.markdown("#### ⚙️ Port Configuration")
    if port_attrs:
        port_config_data = []
        for port_id, attr in port_attrs.items():
            port_config_data.append({
                "ID": port_id,
                "Description": attr.get("description", ""),
                "MAC": attr.get("hw_mac", ""),
                "PCI": attr.get("pci_addr", ""),
                "IP": attr.get("src_ipv4", ""),
                "Status": attr.get("status", ""),
                "Link": attr.get("link", ""),
                "Speed": f"{attr.get('speed', 0)}",
                "Cores": str(attr.get("cores", []))
            })
        st.table(port_config_data)
    else:
        st.caption("No port configuration information available.")


def display_all_stats(stats: Dict[str, Any]) -> None:
    """
    Renders TRex statistics in a clean, organized manner.

    Args:
        stats (Dict[str, Any]): Dictionary containing TRex statistics.
    """
    if not stats:
        st.info("No statistics available.")
        return

    # --- Estadísticas por Puerto ---
    st.markdown("#### 🚦 Statistics by Port")
    port_data = []
    for port_id, port_stat in stats.items():
        if port_id in ("global", "total", "flow_stats", "latency"):
            continue
        if not isinstance(port_stat, dict):
            continue
        port_data.append({
            "Port": port_id,
            "Packets TX": port_stat.get("opackets", 0),
            "Packets RX": port_stat.get("ipackets", 0),
            "Bytes TX": port_stat.get("obytes", 0),
            "Bytes RX": port_stat.get("ibytes", 0),
            "TX Errors": port_stat.get("oerrors", 0),
            "RX Errors": port_stat.get("ierrors", 0),
            "TX Speed": f"{port_stat.get('tx_bps', 0):.2f} Mbit/s",
            "RX Speed": f"{port_stat.get('rx_bps', 0):.2f} Mbit/s",
            "TX Util": f"{port_stat.get('tx_util', 0)}%",
            "RX Util": f"{port_stat.get('rx_util', 0)}%",
        })
    if port_data:
        st.table(port_data)
    else:
        st.caption("No port statistics available.")

    st.markdown("---")

    # --- Estadísticas Globales ---
    global_stats = stats.get("global", {})
    st.markdown("#### 🌐 Global Statistics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Flows", global_stats.get("active_flows", 0))
    with col2:
        st.metric("Active Sockets", global_stats.get("active_sockets", 0))
    with col3:
        st.metric("Packets TX", global_stats.get("tx_pps", 0))
    with col4:
        st.metric("Packets RX", global_stats.get("rx_pps", 0))

    st.markdown("---")

    # --- Estadísticas Totales ---
    total_stats = stats.get("total", {})
    st.markdown("#### 📈 Total Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Packets TX", total_stats.get("opackets", 0))
        st.metric("Bytes TX", total_stats.get("obytes", 0))
    with col2:
        st.metric("Packets RX", total_stats.get("ipackets", 0))
        st.metric("Bytes RX", total_stats.get("ibytes", 0))

    st.markdown("---")

    # --- Latencia ---
    latency = stats.get("latency", {})
    if latency:
        st.markdown("#### ⏱️ Latency")
        global_latency = latency.get("global", {})
        st.metric("Old Flow", global_latency.get("old_flow", 0))
        st.metric("Bad Header", global_latency.get("bad_hdr", 0))
    else:
        st.caption("No latency data available.")

    st.markdown("---")

    # --- Flujos Activos ---
    flow_stats = stats.get("flow_stats", {})
    if flow_stats:
        st.markdown("#### 🌊 Active Flows")
        st.json(flow_stats)
    else:
        st.caption("No active flows available.")


def list_stl_profiles(load_dir: str) -> list:
    """
    Lists all STL profile files in the specified directory.
    
    Args:
        load_dir (str): Path to the directory containing STL profiles.
        
    Returns:
        list: List of STL profile file names.
    """
    try:
        if os.path.exists(load_dir):
            return [f for f in os.listdir(load_dir) if f.endswith('.py')]
        else:
            return []
    except Exception:
        return []


def render_stl_controls(objs: Dict[str, Any]) -> None:
    """
    Renders STL profile controls and execution options.
    
    Args:
        objs (Dict[str, Any]): Dictionary containing initialized application objects,
                                  specifically "traffic_generator".
    """
    tg = objs["traffic_generator"]
    
    st.markdown("## 📜 STL Profile Management")
    
    # List available STL profiles
    stl_profiles = list_stl_profiles(str(tg.load_dir))
    if not stl_profiles:
        st.warning("No STL profiles found in the load directory.")
        return
    
    st.subheader("Available STL Profiles")
    selected_profile = st.selectbox(
        "Select an STL Profile",
        options=stl_profiles,
        key="selected_stl_profile"
    )
    
    # Get profile details
    try:
        with open(os.path.join(tg.load_dir, selected_profile), 'r') as f:
            profile_content = f.read()
        
        st.markdown("### Profile Details")
        st.text_area("Profile Content", value=profile_content, height=200, key="profile_content")
    except Exception as e:
        st.error(f"Error reading profile: {str(e)}")
    
    # STL execution controls
    st.markdown("---")
    st.subheader("STL Program Execution")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        duration = st.number_input(
            "Duration (seconds)",
            min_value=1,
            max_value=3600,
            value=10,
            key="stl_duration"
        )
    
    with col2:
        output_file = st.text_input(
            "Output File",
            value=f"stl_output_{selected_profile.replace('.py', '')}.txt",
            key="stl_output"
        )
    
    with col3:
        st.markdown("### Execute STL Program")
        if st.button("▶️ Start STL Program", use_container_width=True):
            with st.spinner(f"Starting STL program {selected_profile}..."):
                if tg.start_stl_program(
                    file_cfg=os.path.join(tg.load_dir, selected_profile),
                    stl_duration=duration,
                    stl_output=output_file
                ):
                    st.success("STL program started successfully!")
                    # Refresh the page to update status
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Failed to start STL program.")
    
    # Show current STL process status
    st.markdown("---")
    st.subheader("Current STL Status")
    
    if tg.stl_state == "Launched":
        st.success(f"STL program is currently running. Process state: {tg.stl_state}")
        if st.button("⏹️ Stop STL Program", use_container_width=True):
            with st.spinner("Stopping STL program..."):
                if tg.stop_stl_program():
                    st.success("STL program stopped successfully!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Failed to stop STL program.")
    else:
        st.info(f"STL program is not running. Current state: {tg.stl_state}")
        
    # Display current STL process information
    st.markdown("---")
    st.subheader("STL Process Information")
    
    if tg.stl_filename:
        st.markdown(f"**Current STL Script:** `{tg.stl_filename}`")
        st.markdown(f"**Duration:** {tg.stl_duration} seconds")
        st.markdown(f"**Start Time:** {tg.stl_start_time}")
        if tg.stl_args:
            st.markdown(f"**Arguments:** {', '.join(tg.stl_args)}")
    else:
        st.info("No STL program currently loaded.")


def render_traffic_generator(objs: Dict[str, Any]) -> None:
    """
    Renders the Traffic Generator UI.

    Args:
        objs (Dict[str, Any]): Dictionary containing initialized application objects,
                               specifically "traffic_generator".
    """
    tg = objs["traffic_generator"]
    if "trex_stats" not in st.session_state:
        st.session_state["trex_stats"] = None
    if "show_stats" not in st.session_state:
        st.session_state["show_stats"] = False
    if "show_port_configs" not in st.session_state:
        st.session_state["show_port_configs"] = False

    st.header("🚀 Traffic Generator Control")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🚦 Generator Selection",
        "🦖 TRex Server Control",
        "📊 TRex Statistics",
        "📜 STL Profile Execution"
    ])

    with tab1:
        st.subheader("Generator Selection")
        try:
            generators = [f.name for f in global_paths.TGEN_DIR.iterdir() if f.is_dir()]
        except Exception:
            generators = []

        if not generators:
            st.error(f"No generators found in {global_paths.TGEN_DIR}")
        else:
            selected_name = st.selectbox(
                "Choose Traffic Generator",
                options=generators,
                index=generators.index(tg.traffic_gen_name) if tg.traffic_gen_name in generators else 0
            )

            if selected_name != tg.traffic_gen_name:
                if tg.select_traffic_gen(selected_name):
                    placeholder = st.empty()
                    for i in range(3, 0, -1):
                        placeholder.success(f"Switched to {selected_name}! Refreshing in {i}s...")
                        time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to switch generator.")
            else:
                st.info(f"Active Generator: **{tg.traffic_gen_name}** (v{tg.traffic_gen_ver})")

    with tab2:
        if tg.traffic_gen_name and tg.traffic_gen_name.startswith("trex_"):
            st.subheader("TRex Server Status")
            server_status = tg.get_server_status()
            if server_status.get("pid"):
                st.table([
                    {
                        "PID": server_status["pid"],
                        "Configuration": server_status["config"],
                        "Status": server_status["status"]
                    }
                ])
            else:
                st.info("No active traffic generator server detected.")

            st.markdown("---")

            with st.expander("🖥️ TRex Server Controls", expanded=True):
                st.markdown("### Server Controls")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🖥️ Start TRex Server", use_container_width=True):
                        with st.spinner("Starting TRex Server..."):
                            if tg.start_trex_server():
                                placeholder = st.empty()
                                for i in range(3, 0, -1):
                                    placeholder.success(f"TRex Server started! Refreshing in {i}s...")
                                    time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to start TRex Server.")
                with col2:
                    if st.button("🛑 Stop TRex Server", use_container_width=True):
                        if tg.stop_trex_server():
                            placeholder = st.empty()
                            for i in range(3, 0, -1):
                                placeholder.success(f"TRex Server stopped! Refreshing in {i}s...")
                                time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to stop TRex Server.")

            with st.expander("📦 DPDK Driver & Configuration", expanded=True):
                st.markdown("### DPDK Management")
                dpdk_files = [f.name for f in tg.dpdk_profile_dir.iterdir() if f.suffix == ".yaml"]
                if dpdk_files:
                    selected_dpdk = st.selectbox("Select DPDK Profile", dpdk_files)
                    if st.button("📦 Load DPDK Driver", use_container_width=True):
                        with st.spinner("Loading DPDK driver..."):
                            if tg.load_dpdk_driver(selected_dpdk):
                                placeholder = st.empty()
                                for i in range(3, 0, -1):
                                    placeholder.success(f"Driver loaded using {selected_dpdk}! Refreshing in {i}s...")
                                    time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to load DPDK driver. Ensure you have sudo privileges and the correct configuration.")
                else:
                    st.info("No DPDK profiles found.")

                st.markdown("---")
                st.markdown("### Active DPDK Drivers")
                active_dpdk_drivers = tg.get_active_dpdk_drivers()
                if active_dpdk_drivers:
                    st.table(active_dpdk_drivers)
                else:
                    st.info("No active DPDK drivers detected.")
        else:
            st.warning("TRex generator not selected.")

    with tab3:
        st.subheader("TRex Statistics")
        auto_refresh = st.toggle("🔄 Auto-refresh stats (1s)", key="auto_refresh_toggle")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Display Stats", use_container_width=True):
                if not st.session_state.get("trex_stats"):
                    with st.spinner("Fetching stats..."):
                        result = tg.get_trex_stats()
                        if isinstance(result, dict) and "error" in result:
                            st.error(result["error"])
                        elif result:
                            st.session_state["trex_stats"] = result
                        else:
                            st.info("No statistics available.")
                
                if st.session_state.get("trex_stats"):
                    st.session_state["show_stats"] = True
                    st.session_state["show_port_configs"] = False
        
        with col2:
            if st.button("⚙️ Display Port Configs", use_container_width=True):
                if not st.session_state.get("trex_stats"):
                    with st.spinner("Fetching stats..."):
                        result = tg.get_trex_stats()
                        if isinstance(result, dict) and "error" in result:
                            st.error(result["error"])
                        elif result:
                            st.session_state["trex_stats"] = result
                        else:
                            st.info("No statistics available.")
                
                if st.session_state.get("trex_stats"):
                    st.session_state["show_port_configs"] = True
                    st.session_state["show_stats"] = False

        if st.session_state.get("trex_stats"):
            # If auto-refresh is on, we fetch new stats every time.
            if auto_refresh:
                result = tg.get_trex_stats()
                if isinstance(result, dict) and "error" in result:
                    st.error(result["error"])
                elif result:
                    st.session_state["trex_stats"] = result
                else:
                    st.info("No statistics available.")

            stats_data = st.session_state["trex_stats"]
            stats = stats_data.get("stats", {})
            port_attrs = stats_data.get("port_attrs", {})
            
            if st.session_state.get("show_port_configs"):
                display_port_config(port_attrs)
                st.markdown("---")
            
            if st.session_state.get("show_stats"):
                display_all_stats(stats)

            if auto_refresh:
                time.sleep(1)
                st.rerun()
        else:
            if auto_refresh:
                with st.spinner("Fetching stats for auto-refresh..."):
                    result = tg.get_trex_stats()
                    if isinstance(result, dict) and "error" in result:
                        st.error(result["error"])
                    elif result:
                        st.session_state["trex_stats"] = result
                    else:
                        st.info("No statistics available.")
            else:
                st.info("No statistics fetched yet. Click a button above to fetch them.")

    with tab4:
        # STL Profile Management - This tab was missing!
        render_stl_controls(objs)
