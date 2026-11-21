import platform
import psutil
import streamlit as st


def _cpu_model() -> str:
    try:
        with open("/proc/cpuinfo") as f:
            return next(l.split(":", 1)[1].strip() for l in f if "model name" in l)
    except (OSError, StopIteration):
        return platform.processor()


def _cpu_temp() -> float | None:
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return int(f.read()) / 1000.0
    except OSError:
        return None


def render_dashboard(objs: dict) -> None:
    st.header("🚀 System Telemetry")
    st.markdown("### *Real-time Node Status*")
    st.markdown("---")

    cpu = psutil.cpu_percent(interval=None) or psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory()
    temp = _cpu_temp()

    with st.empty():
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CPU Usage", f"{cpu}%")
        c2.metric("RAM Usage", f"{ram.percent}%", f"{ram.used // 1024**2}MB / {ram.total // 1024**2}MB")
        c3.metric("Active Processes", len(psutil.pids()))
        c4.metric("CPU Temp", f"{temp}°C" if temp else "N/A")

    st.markdown("---")
    left, right = st.columns(2)
    with left:
        st.subheader("🐧 Kernel Information")
        st.info(f"**Kernel:** {platform.system()} {platform.release()} ({platform.version()})")
        st.write(f"**Hostname:** {platform.node()}")
        st.write(f"**Architecture:** {platform.machine()}")
    with right:
        st.subheader("📋 Hardware Info")
        st.info(f"**Processor:** {_cpu_model()}")
        st.write(f"**Physical Cores:** {psutil.cpu_count(logical=False)}")
        st.write(f"**Logical Cores:** {psutil.cpu_count(logical=True)}")

    st.markdown("---")
    st.subheader("🌐 Network Interfaces")
    n1, n2 = st.columns(2)
    ifaces = psutil.net_if_addrs()
    with n1:
        st.write("**Ethernet/Wireless**")
        for name, addrs in ifaces.items():
            if name != "lo":
                st.text(f"{name}: {next((a.address for a in addrs if a.family == 2), 'N/A')}")
    with n2:
        st.write("**Loopback & Virtuals**")
        for name, addrs in ifaces.items():
            if name == "lo":
                st.text(f"{name}: {next((a.address for a in addrs if a.family == 2), 'N/A')}")
