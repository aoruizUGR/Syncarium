#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dashboard.py

**Project**: Syncarium Platform
**Description**: UI component for rendering real-time system telemetry and hardware status.
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada
**License**: GPLv3
"""

import streamlit as st
import psutil
import platform
from typing import Optional

def get_cpu_model() -> str:
    """
    Retrieves the CPU model name from the system files.

    Returns:
        str: The CPU model name or the system processor identifier if file read fails.
    """
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    return line.split(":")[1].strip()
    except:
        pass
    return platform.processor()

def get_cpu_temp() -> Optional[float]:
    """
    Retrieves the current CPU temperature from the thermal zone files.

    Returns:
        Optional[float]: The temperature in Celsius, or None if inaccessible.
    """
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return int(f.read()) / 1000.0
    except:
        return None

def render_dashboard(objs: dict) -> None:
    """
    Renders the system telemetry dashboard in the Streamlit UI.

    Args:
        objs (dict): Dictionary containing initialized application objects.
    """
    st.header("🚀 System Telemetry")
    st.markdown("### *Real-time Node Status*")
    st.markdown("---")

    metrics_placeholder = st.empty()

    cpu_usage = psutil.cpu_percent(interval=None) or psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory()
    temp = get_cpu_temp()
    pids_count = len(psutil.pids())

    with metrics_placeholder.container():
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("CPU Usage", f"{cpu_usage}%")
        with col2:
            st.metric("RAM Usage", f"{ram.percent}%", f"{ram.used // (1024**2)}MB / {ram.total // (1024**2)}MB")
        with col3:
            st.metric("Active Processes", pids_count)
        with col4:
            st.metric("CPU Temp", f"{temp}°C" if temp else "N/A")

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🐧 Kernel Information")
        kernel_info = f"{platform.system()} {platform.release()} ({platform.version()})"
        st.info(f"**Kernel:** {kernel_info}")
        st.write(f"**Hostname:** {platform.node()}")
        st.write(f"**Architecture:** {platform.machine()}")

    with col_right:
        st.subheader("📋 Hardware Info")
        st.info(f"**Processor:** {get_cpu_model()}")
        st.write(f"**Physical Cores:** {psutil.cpu_count(logical=False)}")
        st.write(f"**Logical Cores:** {psutil.cpu_count(logical=True)}")

    st.markdown("---")
    
    st.subheader("🌐 Network Interfaces")
    net_col1, net_col2 = st.columns(2)
    interfaces = psutil.net_if_addrs()
    
    with net_col1:
        st.write("**Ethernet/Wireless**")
        for name, addrs in interfaces.items():
            if name != 'lo': 
                ipv4 = next((addr.address for addr in addrs if addr.family == 2), "N/A")
                st.text(f"{name}: {ipv4}")
    
    with net_col2:
        st.write("**Loopback & Virtuals**")
        for name, addrs in interfaces.items():
            if name == 'lo':
                ipv4 = next((addr.address for addr in addrs if addr.family == 2), "N/A")
                st.text(f"{name}: {ipv4}")