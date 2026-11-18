import streamlit as st
from typing import Any, Dict

from syncarium.core import LocalManager, TrafficGenerator, ExperimentOrchestrator #, MonHub
from syncarium.ui import (
    render_dashboard,
    render_local_manager,
    render_traffic_generator,
    render_exp_orchestra
    # render_mon_hub,
)


def initialize_session_state() -> None:
    if "app_objects" not in st.session_state:
        
        st.session_state.app_objects = {
            "local_manager": LocalManager(),
            "traffic_generator": TrafficGenerator(),
            # "monhub": MonHub()
        }

def main() -> None:
    st.set_page_config(page_title="Syncarium Platform", page_icon="⏱️", layout="wide")
    initialize_session_state()
    objs: Dict[str, Any] = st.session_state.app_objects

    st.title("⏱️ Syncarium Platform")
    
    menu = st.sidebar.selectbox(
        "Navigation Menu",
        ["Dashboard", "🌐 Local Manager", "🚦 Traffic Generator",
         "🧪 ExperimentOrchestrator", "📊 MonHub"]
    )

    views = {
        "Dashboard": render_dashboard,
        "🌐 Local Manager": render_local_manager,
        "🚦 Traffic Generator": render_traffic_generator,
        "🧪 ExperimentOrchestrator": render_exp_orchestra,
        # "📊 MonHub": render_mon_hub,
    }

    if menu in views:
        views[menu](objs)
    else:
        st.warning(f"The module '{menu}' is not yet implemented.")

    st.sidebar.markdown("---")
    if st.sidebar.button("🛑 Emergency Shutdown"):
        if "dataex" in objs and hasattr(objs["dataex"], "stop_extraction"):
            objs["dataex"].stop_extraction()
        st.error("Cleanup initiated.")
        st.rerun()

if __name__ == "__main__":
    main()