import streamlit as st
from typing import Dict, Any
from pathlib import Path

from syncarium.core.experiment_orchestrator import ExperimentOrchestrator
from syncarium.core.experiment import Experiment


def render_exp_orchestra(objs: Dict[str, Any]) -> None:
    # Initialize the ExperimentOrchestrator with required dependencies
    if "experiment_orchestrator" not in objs:
        objs["experiment_orchestrator"] = ExperimentOrchestrator(
            objs["local_manager"],
            objs["traffic_generator"]
        )
    
    eo: ExperimentOrchestrator = objs["experiment_orchestrator"]
    st.header("🧪 Experiment Orchestrator")
    st.markdown("---")
    
    # Queue Visualization as table
    st.markdown("### 📊 Experiment Queue")
    if eo.queue:
        # Create a table with delete buttons for each experiment
        queue_data = []
        for i, exp in enumerate(eo.queue):
            queue_data.append({
                "Position": i + 1,
                "Name": exp.fn_hashid,
                "Duration (s)": exp.duration,
                "State": exp.state
            })
        
        # Create a DataFrame to handle the table
        import pandas as pd
        df = pd.DataFrame(queue_data)
        
        # Display the table with custom buttons
        st.dataframe(df, width='stretch')
        
        # Add a separate section for deleting specific experiments
        st.markdown("### 🗑️ Remove Specific Experiment")
        st.markdown("Select an experiment from the queue to remove it:")
        experiment_options = [f"{exp.fn_hashid} (Duration: {exp.duration}s, State: {exp.state})" for exp in eo.queue]
        if experiment_options:
            selected_experiment = st.selectbox("Choose experiment to remove:", experiment_options)
            if st.button("🗑️ Remove Selected Experiment"):
                # Find the experiment to remove
                selected_hashid = selected_experiment.split(" (")[0]  # Extract hashid from the option string
                exp_to_remove = None
                for exp in eo.queue:
                    if exp.fn_hashid == selected_hashid:
                        exp_to_remove = exp
                        break
                
                if exp_to_remove:
                    eo.queue.remove(exp_to_remove)
                    st.success(f"Experiment '{exp_to_remove.fn_hashid}' removed from queue")
                    st.rerun()
                else:
                    st.error("Experiment not found in queue")
        else:
            st.info("No experiments available to remove")
    else:
        st.info("Queue is empty")
    
    # Experiment Queue Management
    st.markdown("### 📋 Queue Management")
    st.markdown("Manage the queue of experiments to be executed")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Add Experiment to Queue**")
        experiment_presets = ["preset_experiment.yaml"]  # Placeholder for actual presets
        selected_preset = st.selectbox("Select Experiment Configuration", experiment_presets)
        
        if st.button("➕ Add to Queue"):
            # Logic to add experiment to queue
            preset_path = Path("syncarium/presets/experiments") / selected_preset
            if preset_path.exists():
                try:
                    experiment = Experiment(file_cfg=preset_path)
                    eo.queue.append(experiment)
                    st.success("Experiment added to queue")
                except Exception as e:
                    st.error(f"Error loading experiment: {str(e)}")
            else:
                st.error(f"File not found: {preset_path}")
            st.rerun()
    
    with col2:
        st.markdown("**Queue Status**")
        queue_size = len(eo.queue)
        st.metric("Experiments in Queue", queue_size)
        
        if queue_size > 0:
            st.write("First experiment in queue:")
            first_exp = eo.queue[0] if queue_size > 0 else None
            if first_exp:
                st.write(f"**Duration:** {first_exp.duration} seconds")
                st.write(f"**State:** {first_exp.state}")
    
    st.markdown("---")
    
    if st.button("🚀 Launch Queue"):
        if queue_size > 0:
            # Logic to launch the queue
            eo.launch_queue()
            st.success("Queue launched")
            st.rerun()
        else:
            st.warning("Queue is empty")
    
    if st.button("🛑 Stop Queue"):
        # Logic to stop the queue
        eo.stop_queue()
        st.success("Queue stopped")
        st.rerun()
    
    # Current Experiment Status
    st.markdown("### 🏃 Current Experiment")
    st.markdown("Status of currently running experiment")
    
    if eo.current_experiment:
        exp = eo.current_experiment
        st.markdown(f"### **{exp.fn_hashid}**")
        st.write(f"**State:** {exp.state}")
        st.write(f"**Duration:** {exp.duration} seconds")
        st.write(f"**Start Time:** {exp.start_ts}")
        
        if st.button("⏹️ Stop Current Experiment"):
            # Logic to stop current experiment
            eo.stop_current_exp()
            st.success("Current experiment stopped")
            st.rerun()
    else:
        st.info("No experiment currently running")
    
    # Inter-experiment Delay
    st.markdown("### ⏱️ Inter-Experiment Delay")
    st.markdown("Configure delay between experiments")
    delay = st.number_input(
        "Delay (seconds)",
        min_value=0,
        max_value=3600,
        value=eo.interexp_delay or 900,
        key="interexp_delay"
    )
    
    if st.button("💾 Set Delay"):
        eo.interexp_delay = delay
        st.success(f"Inter-experiment delay set to {delay} seconds")
        st.rerun()