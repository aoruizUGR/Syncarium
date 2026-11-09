#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
load_gen_view.py

**Project**: Syncarium Platform
**Description**: UI component for managing load generators (TRex and STL).
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada
**License**: GPLv3
"""

import streamlit as st
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import syncarium.options.global_vars as global_vars

def render_load_gen(objs: Dict[str, Any]) -> None:
    """
    Renders the LoadGen UI in the Streamlit application.

    Args:
        objs (Dict[str, Any]): Dictionary containing initialized application objects, 
                                specifically "loadgen".
    """
    main_container = st.container()
    
    with main_container:
        st.header("🚀 Load Generator Management")
        loadgen = objs["loadgen"]
        
        # --- Selection Section ---
        st.subheader("🚦 Select Traffic Generator")
        
        try:
            generators = [f.name for f in global_vars.TGEN_DIR.iterdir() if f.is_dir()]
        except Exception:
            generators = []

        if not generators:
            st.error(f"No generators found in {global_vars.TGEN_DIR}")
            return

        # Use a selectbox to choose the generator
        # If loadgen.loadgen_name is already set, it will pre-select it
        selected_name = st.selectbox(
            "Choose Traffic Generator",
            options=generators,
            index=generators.index(loadgen.loadgen_name) if loadgen.loadgen_name in generators else 0
        )

        # If the user changed the selection, update the backend object
        if selected_name != loadgen.loadgen_name:
            if loadgen.select_load_gen(selected_name):
                st.success(f"Switched to {selected_name}")
                st.rerun()
            else:
                st.error("Failed to switch generator.")
        else:
            st.info(f"Active Generator: **{loadgen.loadgen_name}** (v{loadgen.loadgen_ver})")

        st.markdown("---")

        # --- TRex Management Section ---
        if loadgen.loadgen_name and loadgen.loadgen_name.startswith("trex_"):
            st.subheader("🦖 TRex Server Controls")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🖥️ Start TRex Server", use_container_width=True):
                    with st.spinner("Starting TRex Server..."):
                        if loadgen.start_trex_server():
                            st.success("TRex Server started.")
                            st.rerun()
                        else:
                            st.error("Failed to start TRex Server.")
                
            with col2:
                if st.button("🛑 Stop TRex Server", use_container_width=True):
                    if loadgen.stop_trex_server():
                        st.success("TRex Server stopped.")
                        st.rerun()
                    else:
                        st.error("Failed to stop TRex Server.")

            st.markdown("---")
            st.subheader("📦 Driver & Configuration")
            
            # DPDK Driver Setup
            dpdk_files = [f.name for f in loadgen.dpdk_profile_dir.iterdir() if f.suffix == ".yaml"]
            if dpdk_files:
                selected_dpdk = st.selectbox("Select DPDK Profile", dpdk_files)
                if st.button("📦 Load DPDK Driver"):
                    if loadgen.load_dpdk_driver(selected_dpdk):
                        st.success(f"Driver loaded using {selected_dpdk}")
                        st.rerun()
                    else:
                        st.error("Error loading driver.")
            else:
                st.info("No DPDK profiles found.")

            st.markdown("---")
            st.subheader("🖼️ TRex TUI")
            if st.button("🖼️ Launch TRex TUI"):
                if loadgen.start_trex_tui():
                    st.success("TUI launched.")
                else:
                    st.error("Failed to launch TUI.")

        # --- STL Program Section ---
        st.markdown("---")
        st.subheader("🚀 STL Program Management")
        
        if loadgen.stl_state == "Launched":
            st.warning(f"STL Program is currently RUNNING (PID: {loadgen.stl_process.pid})")
            if st.button("🛑 Stop STL Program", type="primary", use_container_width=True):
                if loadgen.stop_stl_program(preconfirmation=True):
                    st.success("STL Program stopped.")
                    st.rerun()
                else:
                    st.error("Error stopping STL program.")
        else:
            st.info("No STL program is currently running.")
            
            # STL File Selection
            stl_files = [str(f.relative_to(loadgen.load_dir)) for f in loadgen.load_dir.rglob("*.yaml") if f.is_file()]
            if stl_files:
                selected_stl = st.selectbox("Select STL Configuration", stl_files)
                
                col_dur, col_out = st.columns(2)
                with col_dur:
                    duration = st.number_input("Duration (s)", min_value=1, value=10)
                with col_out:
                    output_id = st.text_input("Output Identifier", value="default")

                if st.button("🚀 Start STL Program"):
                    with st.spinner("Launching STL..."):
                        # Convert relative path back to absolute for the backend
                        abs_path = loadgen.load_dir / selected_stl
                        if loadgen.start_stl_program(file_cfg=str(abs_path), stl_duration=duration, stl_output=output_id):
                            st.success("STL Program launched.")
                            st.rerun()
                        else:
                            st.error("Failed to launch STL program.")
            else:
                st.error("No STL configurations found in the directory.")

        st.markdown("---")
        if st.button("🧹 Cleanup LoadGen State", type="secondary"):
            # Reset internal states
            loadgen.stl_state = None
            loadgen.stl_process = None
            st.info("State reset.")
            st.rerun()