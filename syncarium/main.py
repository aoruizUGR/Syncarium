import streamlit as st

from syncarium.core import LocalManager, TrafficGenerator
from syncarium.ui import (
    render_dashboard,
    render_local_manager,
    render_traffic_generator,
    render_exp_orchestra,
)

VIEWS = {
    "Dashboard": render_dashboard,
    "🌐 Local Manager": render_local_manager,
    "🚦 Traffic Generator": render_traffic_generator,
    "🧪 ExperimentOrchestrator": render_exp_orchestra,
}


def main() -> None:
    st.set_page_config(page_title="Syncarium Platform", page_icon="⏱️", layout="wide")

    if "app_objects" not in st.session_state:
        st.session_state.app_objects = {
            "local_manager": LocalManager(),
            "traffic_generator": TrafficGenerator(),
        }
    objs = st.session_state.app_objects

    st.title("⏱️ Syncarium Platform")
    menu = st.sidebar.selectbox("Navigation Menu", list(VIEWS))
    VIEWS[menu](objs)

    st.sidebar.markdown("---")
    if st.sidebar.button("🛑 Emergency Shutdown"):
        dataex = objs.get("dataex")
        if dataex is not None and hasattr(dataex, "stop_extraction"):
            dataex.stop_extraction()
        st.error("Cleanup initiated.")
        st.rerun()


if __name__ == "__main__":
    main()
