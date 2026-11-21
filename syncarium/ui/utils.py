import time
import streamlit as st
from typing import Dict, Any, List


def show_success_refresh(message: str, seconds: int = 3) -> None:
    """Show a success message with countdown and refresh the app after."""
    st.toast(f"{message} Refreshing in {seconds}s...", icon="✅")
    time.sleep(seconds)
    st.rerun()


def handle_yaml_preview(file, file_name: str) -> str:
    try:
        yaml_content = file.read().decode('utf-8')
        st.markdown(f"**Preview of `{file_name}`**")
        st.text_area("YAML Content", value=yaml_content, height=200, key=f"yaml_preview_{file_name}")
        return yaml_content
    except Exception as e:
        st.warning(f"Could not load YAML preview: {str(e)}")
        return ""
