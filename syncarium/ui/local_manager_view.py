import streamlit as st
import subprocess

from typing import List, Dict, Any
from pathlib import Path

from syncarium.core.local_manager import LocalManager
from syncarium.ui.utils import show_success_refresh, handle_yaml_preview


def get_active_namespaces_table() -> List[Dict[str, str]]:
    try:
        result = subprocess.run(["ip", "netns", "list"], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        data = []

        if lines and lines[0]:
            for line in lines:
                ns = line.split()[0]

                iface = ip = mac = gw = "N/A"

                try:
                    interfaces_result = subprocess.run(
                        ["sudo", "ip", "netns", "exec", ns, "ip", "-o", "link", "show"],
                        capture_output=True, text=True, check=True
                    )
                    for if_line in interfaces_result.stdout.strip().split('\n'):
                        parts = if_line.split()
                        if len(parts) >= 2:
                            candidate = parts[1].strip(':')
                            if candidate != "lo":
                                iface = candidate
                                break

                    if iface != "N/A":
                        mac_result = subprocess.run(
                            ["sudo", "ip", "netns", "exec", ns, "ip", "link", "show", iface],
                            capture_output=True, text=True, check=True
                        )
                        mac_line = next((l for l in mac_result.stdout.splitlines() if "link/ether" in l), None)
                        if mac_line:
                            mac = mac_line.split()[1]

                        ip_result = subprocess.run(
                            ["sudo", "ip", "netns", "exec", ns, "ip", "-o", "-4", "addr", "show"],
                            capture_output=True, text=True, check=True
                        )
                        for ip_line in ip_result.stdout.strip().split('\n'):
                            if iface in ip_line and len(ip_line.split()) >= 4:
                                ip = ip_line.split()[3]
                                break

                        gw_result = subprocess.run(
                            ["sudo", "ip", "netns", "exec", ns, "ip", "route", "show", "default"],
                            capture_output=True, text=True, check=True
                        )
                        for gw_line in gw_result.stdout.strip().split('\n'):
                            if "via" in gw_line and len(gw_line.split()) >= 3:
                                gw = gw_line.split()[2]
                                break
                except subprocess.CalledProcessError:
                    pass

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


def render_preset_section(profile_dir: Path, label: str, button_label: str, action) -> None:
    """Renderiza la sección de presets (selectbox + preview + botón de acción)."""
    st.markdown("**Presets**")
    presets = [f.name for f in Path(profile_dir).glob("*.yaml")]
    if not presets:
        st.warning(f"No presets found in profile directory.")
        return

    selected_preset = st.selectbox(label, presets)
    if not selected_preset:
        return

    preset_path = Path(profile_dir) / selected_preset
    try:
        yaml_content = preset_path.read_text()
        st.markdown(f"**Preview of `{selected_preset}`**")
        st.text_area(
            "YAML Content", value=yaml_content, height=200,
            key=f"yaml_preview_{str(preset_path).replace('/', '_').replace('.', '_')}"
        )
    except Exception as e:
        st.warning(f"Could not load YAML preview: {str(e)}")

    if st.button(button_label):
        action(selected_preset)


def render_upload_section(label: str, button_label: str, key: str, action) -> None:
    """Renderiza la sección de subida de archivo custom (uploader + preview + botón)."""
    st.markdown("**Custom Upload**")
    uploaded_file = st.file_uploader(label, type=["yaml"], key=key)
    if not uploaded_file:
        return

    handle_yaml_preview(uploaded_file, uploaded_file.name)

    if st.button(button_label, key=f"{key}_btn"):
        action(uploaded_file.name)


def render_local_manager(objs: Dict[str, Any]) -> None:
    lm: LocalManager = objs["local_manager"]
    st.header("🛠️ Local Manager Control")

    tab1, tab2 = st.tabs([
        "🌐 Network Infrastructure",
        "⏱️ PTP Management"
    ])

    with tab1:
        st.subheader("Network Infrastructure")
        namespaces_data = get_active_namespaces_table()
        if namespaces_data:
            st.table(namespaces_data)
        else:
            st.info("No active network namespaces detected.")

        st.markdown("### Manage Network Namespaces")
        col_ns1, col_ns2 = st.columns(2)
        with col_ns1:
            def start_ns_preset(preset: str) -> None:
                with st.spinner("Deploying namespaces..."):
                    success, error_msg = lm.start_namespaces(file_cfg=preset)
                    if success:
                        show_success_refresh("Success!")
                    else:
                        st.error(error_msg)

            render_preset_section(
                lm.config_dir, "Select Namespace Configuration",
                "🚀 Start Namespaces from Preset", start_ns_preset
            )

        with col_ns2:
            def start_ns_upload(filename: str) -> None:
                with st.spinner("Deploying..."):
                    success, error_msg = lm.start_namespaces(file_cfg=filename)
                    if success:
                        show_success_refresh("Success!")
                    else:
                        st.error(error_msg)

            render_upload_section(
                "Upload Custom Namespace Config",
                "🚀 Start Namespaces from Upload", "ns_upload", start_ns_upload
            )

        st.markdown("### Namespace Cleanup")
        if st.button("Stop all Namespaces", type="primary", use_container_width=True):
            success, error_msg = lm.stop_namespaces()
            if success:
                show_success_refresh("Namespaces deleted!")
            else:
                st.error(error_msg)

    with tab2:
        st.subheader("PTP Client Status")
        if lm.loaded_clients:
            clients_status = [
                {
                    "Client": client_name,
                    "PID": str(data.get("pid", "N/A")),
                    "Namespace": data.get("namespace"),
                    "Interface": data.get("interface"),
                    "Config File": data.get("config", "N/A"),
                    "Status": data.get("status", "Loaded")
                }
                for client_name, data in lm.loaded_clients.items()
            ]
            st.table(clients_status)
        else:
            st.info("No PTP clients loaded. Use the configuration section below.")

        st.markdown("### Manage PTP Configurations")
        col_ptp1, col_ptp2 = st.columns(2)

        def start_ptp_from_config(file_cfg: str) -> None:
            with st.spinner("Loading and starting PTP..."):
                if lm.load_clients(file_cfg=file_cfg):
                    processes = lm.start_ptp(stop_existing=True)
                    if processes:
                        show_success_refresh("PTP processes launched successfully!", 3)
                    else:
                        st.error("Configuration loaded but no processes were launched.")
                else:
                    st.error("Failed to load configuration.")

        with col_ptp1:
            render_preset_section(
                lm.ptp_clients_profile_dir, "Select PTP Configuration",
                "🚀 Load and Start PTP from Preset", start_ptp_from_config
            )

        with col_ptp2:
            render_upload_section(
                "Upload Custom PTP Config",
                "🚀 Load and Start PTP from Upload", "ptp_upload", start_ptp_from_config
            )

        st.markdown("### PTP Clients Cleanup")
        if st.button("Stop all PTP", type="primary", use_container_width=True):
            if lm.stop_ptp():
                show_success_refresh("All PTP processes stopped and logs cleared!")
            else:
                st.error("Error occurred while stopping PTP.")

        st.markdown("### Tools")
        if lm.loaded_clients:
            if st.button("📡 Ping PTP Server"):
                results = lm.ping_server()
                for res in results:
                    if "Error" in res["status"]:
                        st.error(f"{res['client']}: {res['status']}")
                    else:
                        st.success(f"{res['client']}: {res['status']}")
                        st.caption(f"Output: {res['output']}")

            selected_client = st.selectbox("Select Client to View Logs", options=list(lm.loaded_clients.keys()))
            if st.button("📄 Show PTP Logs"):
                log_content = lm.show_logs(selected_client)
                st.info(f"Showing last 100 lines of {selected_client}")
                st.code(log_content, language="log")
        else:
            st.warning("No clients loaded to view logs.")
