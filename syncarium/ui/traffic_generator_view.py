#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
traffic_generator_view.py

**Project**: Syncarium Platform
**Description**: UI component for managing load generators (TRex and STL).
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada
**License**: GPLv3
"""

import streamlit as st
from pathlib import Path
from typing import List, Dict, Any
import time
import path_config.global_vars as global_vars


def display_stats(stats: Dict[str, Any]) -> None:
    """
    Renders TRex statistics in a clean, organized manner.

    Args:
        stats (Dict[str, Any]): Dictionary containing TRex statistics as returned
                                by `get_trex_stats()`.
    """
    # --- Estadísticas por Puerto ---
    st.markdown("#### 🚦 Estadísticas por Puerto")
    if stats:
        port_data = []
        for port_id, port_stat in stats.items():
            if port_id in ("global", "total", "flow_stats", "latency"):
                continue
            if not isinstance(port_stat, dict):
                continue
            port_data.append({
                "Puerto": port_id,
                "Packets TX": port_stat.get("opackets", 0),
                "Packets RX": port_stat.get("ipackets", 0),
                "Bytes TX": port_stat.get("obytes", 0),
                "Bytes RX": port_stat.get("ibytes", 0),
                "Errores TX": port_stat.get("oerrors", 0),
                "Errores RX": port_stat.get("ierrors", 0),
                "Vel. TX": f"{port_stat.get('tx_bps', 0):.2f} Mbit/s",
                "Vel. RX": f"{port_stat.get('rx_bps', 0):.2f} Mbit/s",
                "Util. TX": f"{port_stat.get('tx_util', 0)}%",
                "Util. RX": f"{port_stat.get('rx_util', 0)}%",
            })
        st.table(port_data)
    else:
        st.caption("No hay estadísticas de puertos disponibles.")

    st.markdown("---")

    # --- Estadísticas Globales ---
    global_stats = stats.get("global", {})
    st.markdown("#### 🌐 Estadísticas Globales")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Flujos Activos", global_stats.get("active_flows", 0))
    with col2:
        st.metric("Sockets Activos", global_stats.get("active_sockets", 0))
    with col3:
        st.metric("Packets TX", global_stats.get("tx_pps", 0))
    with col4:
        st.metric("Packets RX", global_stats.get("rx_pps", 0))

    st.markdown("---")

    # --- Estadísticas Totales ---
    total_stats = stats.get("total", {})
    st.markdown("#### 📈 Estadísticas Totales")
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
        st.markdown("#### ⏱️ Latencia")
        global_latency = latency.get("global", {})
        st.metric("Old Flow", global_latency.get("old_flow", 0))
        st.metric("Bad Header", global_latency.get("bad_hdr", 0))

    st.markdown("---")

    # --- Flujos Activos ---
    flow_stats = stats.get("flow_stats", {})
    if flow_stats:
        st.markdown("#### 🌊 Flujos Activos")
        st.json(flow_stats)
    else:
        st.caption("No hay flujos activos.")

    st.markdown("---")

    st.caption("💡 Usa 'Show original JSON' para ver la estructura completa de los datos.")


def render_traffic_generator(objs: Dict[str, Any]) -> None:
    """
    Renders the Traffic Generator UI.

    Args:
        objs (Dict[str, Any]): Dictionary containing initialized application objects,
                                 specifically "traffic_generator".
    """
    tg = objs["traffic_generator"]
    st.header("🚀 Traffic Generator Control")

    tab1, tab2, tab3 = st.tabs([
        "🚦 Generator Selection",
        "🦖 TRex Management",
        "⚠️ Cleanup & Operations"
    ])

    with tab1:
        st.subheader("Generator Selection")
        try:
            generators = [f.name for f in global_vars.TGEN_DIR.iterdir() if f.is_dir()]
        except Exception:
            generators = []

        if not generators:
            st.error(f"No generators found in {global_vars.TGEN_DIR}")
        else:
            selected_name = st.selectbox(
                "Choose Traffic Generator",
                options=generators,
                index=generators.index(tg.loadgen_name) if tg.loadgen_name in generators else 0
            )

            if selected_name != tg.loadgen_name:
                if tg.select_load_gen(selected_name):
                    placeholder = st.empty()
                    for i in range(3, 0, -1):
                        placeholder.success(f"Switched to {selected_name}! Refreshing in {i}s...")
                        time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to switch generator.")
            else:
                st.info(f"Active Generator: **{tg.loadgen_name}** (v{tg.loadgen_ver})")

    with tab2:
        if tg.loadgen_name and tg.loadgen_name.startswith("trex_"):
            st.subheader("TRex Server Status")
            server_status = tg.get_server_status()
            st.table([
                {
                    "PID": server_status["pid"] if server_status["pid"] else "N/A",
                    "Configuration": server_status["config"],
                    "Status": server_status["status"]
                }
            ])

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

            with st.expander("📊 TRex Statistics", expanded=True):
                st.markdown("### Statistics")
                if st.button("📊 Get TRex Stats", use_container_width=True):
                    with st.spinner("Fetching stats..."):
                        stats = tg.get_trex_stats()
                        if stats:
                            display_stats(stats)
                        else:
                            st.error("Could not retrieve stats.")

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
        st.subheader("Cleanup & Operations")
        st.warning("⚠️ **Danger Zone**: The following actions will stop the TRex server and terminate any active STL processes.")
        col_stop1, col_stop2 = st.columns(2)
        with col_stop1:
            if st.button("Stop TRex Server", type="primary", use_container_width=True):
                if tg.stop_trex_server():
                    placeholder = st.empty()
                    for i in range(3, 0, -1):
                        placeholder.success(f"TRex Server stopped! Refreshing in {i}s...")
                        time.sleep(1)
                    st.rerun()
                else:
                    st.error("Error occurred while stopping TRex Server.")
        with col_stop2:
            if st.button("Stop STL Program", type="primary", use_container_width=True):
                if tg.stop_stl_program(preconfirmation=True):
                    placeholder = st.empty()
                    for i in range(3, 0, -1):
                        placeholder.success(f"STL program stopped! Refreshing in {i}s...")
                        time.sleep(1)
                    st.rerun()
                else:
                    st.error("Error occurred while stopping STL program.")
