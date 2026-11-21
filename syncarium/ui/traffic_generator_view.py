import streamlit as st
import os

from typing import Dict, Any
import path_config.global_paths as global_paths

from syncarium.core.traffic_generator import TrafficGenerator
from syncarium.ui.utils import show_success_refresh


def handle_process_action(action_func, success_message: str, error_message: str, *args, **kwargs) -> bool:
    if action_func(*args, **kwargs):
        show_success_refresh(success_message)
        return True
    else:
        st.error(error_message)
        return False


def display_all_ports(port_attrs: Dict[str, Any]) -> None:
    st.markdown("#### 🔌 Port Configuration")
    if port_attrs:
        port_config_data = [
            {
                "ID": port_id,
                "Description": attr.get("description", ""),
                "MAC": attr.get("hw_mac", ""),
                "PCI": attr.get("pci_addr", ""),
                "IP": attr.get("src_ipv4", ""),
                "Status": attr.get("status", ""),
                "Link": attr.get("link", ""),
                "Speed": f"{attr.get('speed', 0)}",
                "Cores": str(attr.get("cores", []))
            }
            for port_id, attr in port_attrs.items()
        ]
        st.table(port_config_data)
    else:
        st.caption("No port configuration information available.")


def _stat_row(stat: Dict[str, Any]) -> Dict[str, Any]:
    """Filas comunes de estadísticas (paquetes, bytes, velocidades y utilidades)."""
    return {
        "Packets TX": stat.get("opackets", 0),
        "Packets RX": stat.get("ipackets", 0),
        "Bytes TX": f"{stat.get('obytes', 0)/1e6:.2f} MB",
        "Bytes RX": f"{stat.get('ibytes', 0)/1e6:.2f} MB",
        "TX Speed": f"{stat.get('tx_bps', 0)/1e6:.2f} Mbps",
        "RX Speed": f"{stat.get('rx_bps', 0)/1e6:.2f} Mbps",
        "TX Util": f"{stat.get('tx_util', 0):.1f}%",
        "RX Util": f"{stat.get('rx_util', 0):.1f}%",
    }


def display_all_stats(stats: Dict[str, Any]) -> None:
    if not stats:
        st.info("No statistics available.")
        return

    st.markdown("#### 🌐 Global Statistics")
    g_stat = next((stats[k] for k in ("global", "total") if isinstance(stats.get(k), dict)), None)
    if g_stat is not None:
        st.table([{"Metric": "Global", **_stat_row(g_stat)}])
    else:
        st.caption("No global statistics found.")

    st.markdown("#### 🚦 Statistics by Port")
    port_data = []
    for port_id, port_stat in stats.items():
        if port_id in ("global", "total", "flow_stats", "latency") or not isinstance(port_stat, dict):
            continue
        row = _stat_row(port_stat)
        port_data.append({
            "Port": port_id,
            "Packets TX": row["Packets TX"],
            "Packets RX": row["Packets RX"],
            "Bytes TX": row["Bytes TX"],
            "Bytes RX": row["Bytes RX"],
            "TX Errors": port_stat.get("oerrors", 0),
            "RX Errors": port_stat.get("ierrors", 0),
            "TX Speed": row["TX Speed"],
            "RX Speed": row["RX Speed"],
            "TX Util": row["TX Util"],
            "RX Util": row["RX Util"],
        })
    if port_data:
        st.table(port_data)
    else:
        st.caption("No port statistics available.")


def list_stl_profiles(load_dir: str) -> list:
    try:
        if os.path.exists(load_dir):
            return [f for f in os.listdir(load_dir) if f.endswith('.py')]
        else:
            return []
    except Exception:
        return []


def render_stl_controls(objs: Dict[str, Any]) -> None:
    tg: TrafficGenerator = objs["traffic_generator"]

    st.markdown("## 📜 STL Profile Management")

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

    try:
        with open(os.path.join(tg.load_dir, selected_profile), 'r') as f:
            profile_content = f.read()

        st.markdown("### Profile Details")
        st.text_area("Profile Content", value=profile_content, height=200, key="profile_content")
    except Exception as e:
        st.error(f"Error reading profile: {str(e)}")

    st.markdown("---")
    st.subheader("STL Program Execution")

    col1, col2, col3 = st.columns(3)

    with col1:
        duration = st.number_input(
            "Duration (seconds)",
            min_value=1,
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
            handle_process_action(
                tg.start_stl_program,
                "STL program started successfully!",
                "Failed to start STL program.",
                file_cfg=os.path.join(tg.load_dir, selected_profile),
                stl_duration=duration,
                stl_output=output_file
            )

    st.markdown("---")
    st.subheader("Current STL Status")

    if tg.stl_state == "Launched":
        st.success(f"STL program is currently running. Process state: {tg.stl_state}")
        if st.button("⏹️ Stop STL Program", use_container_width=True):
            handle_process_action(
                tg.stop_stl_program,
                "STL program stopped successfully!",
                "Failed to stop STL program."
            )
    else:
        st.info(f"STL program is not running. Current state: {tg.stl_state}")

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
    tg: TrafficGenerator = objs["traffic_generator"]
    for key, default in [("trex_stats", None), ("show_stats", False), ("show_port_configs", False)]:
        st.session_state.setdefault(key, default)

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
                index=0
            )

            if st.button("Select Generator", key="select_generator_btn"):
                handle_process_action(
                    tg.select_traffic_gen,
                    f"Switched to {selected_name}! Refreshing in 3s...",
                    "Failed to switch generator.",
                    selected_name
                )

    with tab2:
        st.subheader("Traffic Generator Status")
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

        st.markdown("### Server Controls")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🖥️ Start TRex Server", use_container_width=True):
                handle_process_action(
                    tg.start_trex_server,
                    "TRex Server started! Refreshing in 3s...",
                    "Failed to start TRex Server."
                )
        with col2:
            if st.button("🛑 Stop TRex Server", use_container_width=True):
                handle_process_action(
                    tg.stop_trex_server,
                    "TRex Server stopped! Refreshing in 3s...",
                    "Failed to stop TRex Server."
                )

        st.markdown("### DPDK Management")
        dpdk_files = [f.name for f in tg.dpdk_profile_dir.iterdir() if f.suffix == ".yaml"]
        if dpdk_files:
            selected_dpdk = st.selectbox("Select DPDK Profile", dpdk_files)
            if st.button("📦 Load DPDK Driver", use_container_width=True):
                handle_process_action(
                    tg.load_dpdk_driver,
                    f"Driver loaded using {selected_dpdk}! Refreshing in 3s...",
                    "Failed to load DPDK driver. Ensure you have sudo privileges and the correct configuration.",
                    selected_dpdk
                )
        else:
            st.info("No DPDK profiles found.")

        st.markdown("### Active DPDK Drivers")
        active_dpdk_drivers = tg.get_active_dpdk_drivers()
        if active_dpdk_drivers:
            st.table(active_dpdk_drivers)
        else:
            st.info("No active DPDK drivers detected.")

    with tab3:
        st.subheader("📊 TRex Statistics")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Reset Statistics", key="reset_stats_btn"):
                handle_process_action(
                    tg.clear_trex_stats,
                    "Statistics reset successfully!",
                    "Failed to reset statistics."
                )

        with col2:
            update_interval = st.toggle("🔄 Auto-update every second", value=False, key="auto_update")

        @st.fragment(run_every="1s" if st.session_state.get("auto_update", False) else None)
        def render_trex_stats():
            stats_data = tg.get_trex_stats()

            if stats_data and "error" not in stats_data:
                st.session_state["trex_stats"] = stats_data
            elif "trex_stats" in st.session_state:
                st.warning("Could not fetch statistics. Please ensure TRex server is running.")

            cached = st.session_state.get("trex_stats")
            if cached:
                display_all_stats(cached.get("stats", {}))
                st.markdown("---")
                display_all_ports(cached.get("port_attrs", {}))

        render_trex_stats()

    with tab4:
        render_stl_controls(objs)
