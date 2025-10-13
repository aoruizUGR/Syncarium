#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# experiment.py

**Project**: Syncarium - Intelligent Timing Platform Toolkit  
**Description**: Syncarium Experiment  
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada  
**Created**: 2025-10-09
**Version**: 1.1.0  
**License**: GPLv3
"""

# ─────────────────────────────────────────────────────────────────────────────
# Standard Library Imports
import yaml
import time
import hashlib
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Third-Party Imports
# (None used directly in this file)

# ─────────────────────────────────────────────────────────────────────────────
# Local Application Imports
import syncarium.options.global_vars as global_vars

# ─────────────────────────────────────────────────────────────
# 🧪 Experiment Class
# ─────────────────────────────────────────────────────────────
class Experiment:

# ─────────────────────────────────────────────────────────────────────────────
# 🚧 Function: constructor
# ─────────────────────────────────────────────────────────────────────────────
    def __init__(self, file_cfg: Path = None) -> None:

        with file_cfg.open('r') as file:
            data: dict = yaml.safe_load(file)

            # Load experiment metadata
            self.fn = file_cfg.stem
            self.fn_absolute_path = Path(file_cfg).resolve()
            self.hash_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:4]
            self.fn_hashid = f"{self.fn}_{self.hash_id}"
            self.start_ts = None
            self.duration = int(data.get("total_duration"))
            self.state = "Queued"

            # Load configuration values
            self.stl_fn = data.get("loadgen_stl_program")
            self.dataex_datasources = list(data.get("dataex_datasources", {}).keys())
            self.synccore_clients = list(data.get("synccore_clients", {}).keys())

            # Prepare output directories
            self.exp_output_dir = global_vars.OUTPUT_DIR / Path(data.get("output_filepath"))
            self.exp_output_dir.mkdir(parents=True, exist_ok=True)

            # Prepare output file paths
            self.output_log  = self.exp_output_dir / f"{self.fn_hashid}.log"
            self.output_yaml = self.exp_output_dir / f"{self.fn_hashid}.yaml"
            self.output_csv  = self.exp_output_dir / f"{self.fn_hashid}.csv"

            # Load start times and current_durations
            self.stl_start = int(data.get("loadgen_stl_start"))
            self.stl_duration = self.duration - 60
            self.dataex_start = int(data.get("dataex_start"))
            self.dataex_duration = self.duration - self.dataex_start
            self.synccore_start = int(data.get("synccore_start"))
            self.synccore_stop_at_end = bool(data.get("synccore_stop_at_end"))
        

        