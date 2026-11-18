import time
import streamlit as st
import subprocess

from typing import List, Dict, Any, Optional
from pathlib import Path

from syncarium.core.local_manager import LocalManager


def get_active_namespaces_table() -> List[Dict[str, str]]:
    try:
        result = subprocess.run(["ip", "netns", "list"], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        data = []
        
        if lines and lines[0]:
            for line in lines:
                ns = line.split()[0]
                
                iface = "N/A"
                ip = "N/A"
                mac = "N/A"
                gw = "N/A"

                try:
                    interfaces_result = subprocess.run(
                        ["sudo", "ip", "netns", "exec", ns, "ip", "-o", "link", "show"],
                        capture_output=True, text=True, check=True
                    )
                    interfaces = interfaces_result.stdout.strip().split('\n')
                    
                    for if_line in interfaces:
                        parts = if_line.split()
                        if len(parts) >= 2:
                            current_iface = parts[1].strip(':')
                            if current_iface != "lo":
                                iface = current_iface
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
                        ips = ip_result.stdout.strip().split('\n')
                        for ip_line in ips:
                            if iface in ip_line:
                                parts = ip_line.split()
                                if len(parts) >= 4:
                                    ip = parts[3]
                                    break

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
        
        with st.expander("🏗️ Namespace Management", expanded=True):
            st.markdown("### Manage Network Namespaces")
            col_ns1, col_ns2 = st.columns(2)
            with col_ns1:
               st.markdown("**Presets**")
               ns_presets = [f.name for f in Path(lm.config_dir).glob("*.yaml")]
               if ns_presets:
                   selected_ns_preset = st.selectbox("Select Namespace Configuration", ns_presets)
                   
                   if selected_ns_preset:
                       try:
                           preset_path = Path(lm.config_dir) / selected_ns_preset
                           with open(preset_path, 'r') as f:
                               yaml_content = f.read()
                           st.markdown(f"**Preview of `{selected_ns_preset}`**")
                           st.text_area("YAML Content", value=yaml_content, height=200, key=f"yaml_preview_ns_{selected_ns_preset}_{str(preset_path).replace('/', '_').replace('.', '_')}")
                       except Exception as e:
                           st.warning(f"Could not load YAML preview: {str(e)}")
                   
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
                
            st.markdown("### Namespace Cleanup")
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
                    "Config File": data.get("config", "N/A"),
                    "Status": data.get("status", "Loaded")
                })
            st.table(clients_status)
        else:
            st.info("No PTP clients loaded. Use the configuration section below.")

        st.markdown("---")
        
        with st.expander("📡 PTP Configuration", expanded=True):
            st.markdown("### Manage PTP Configurations")
            col_ptp1, col_ptp2 = st.columns(2)
            with col_ptp1:
                st.markdown("**Presets**")
                ptp_presets = [f.name for f in Path(lm.ptp_clients_profile_dir).glob("*.yaml")]
                if ptp_presets:
                    selected_ptp_preset = st.selectbox("Select PTP Configuration", ptp_presets)
                    if selected_ptp_preset:
                        try:
                            preset_path = Path(lm.ptp_clients_profile_dir) / selected_ptp_preset
                            with open(preset_path, 'r') as f:
                                yaml_content = f.read()
                            st.markdown(f"**Preview of `{selected_ptp_preset}`**")
                            st.text_area("YAML Content", value=yaml_content, height=200, key=f"yaml_preview_ptp_{selected_ptp_preset}_{str(preset_path).replace('/', '_').replace('.', '_')}")
                        except Exception as e:
                            st.warning(f"Could not load YAML preview: {str(e)}")
                
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

            with col_ptp2:
                st.markdown("**Custom Upload**")
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
                        st.markdown("---")

            st.markdown("### PTP Clients Cleanup")
            if st.button("Stop all PTP", type="primary", use_container_width=True):
                if lm.stop_ptp():
                    placeholder = st.empty()
                    for i in range(3, 0, -1):
                        placeholder.success(f"All PTP processes stopped and logs cleared! Refreshing in {i}s...")
                        time.sleep(1)
                    st.rerun()
                else:
                    st.error("Error occurred while stopping PTP.")
                    
        st.markdown("---")
        
        with st.expander("🛠️ Connectivity Tools", expanded=True):
            st.markdown("### Tools")
            if lm.loaded_clients:
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
            
                selected_client = st.selectbox("Select Client to View Logs", options=list(lm.loaded_clients.keys()))
                if st.button("📄 Show PTP Logs"):
                    log_content = lm.show_logs(selected_client)
                    st.info(f"Showing last 100 lines of {selected_client}")
                    st.code(log_content, language="log")
            else:
                st.warning("No clients loaded to view logs.")

        st.markdown("---")
