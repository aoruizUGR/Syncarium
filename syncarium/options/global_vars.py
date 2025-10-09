#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# global_vars.py

**Project**: Syncarium - Intelligent Timing Platform Toolkit  
**Description**: Syncarium global variables  
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada  
**Created**: 2025-09-19  
**Version**: 1.1.0  
**License**: GPLv3
"""

from pathlib import Path

# ─────────────────────────────────────────────────────────────
# MAIN DIRS VARS
# ─────────────────────────────────────────────────────────────
ROOT_DIR: Path = Path(__file__).resolve().parent.parent.parent

SYNCARIUM_DIR: Path = Path(__file__).resolve().parent.parent

CONFIG_DIR: Path = SYNCARIUM_DIR / "config"

SCRIPTS_DIR: Path = SYNCARIUM_DIR / "scripts"

#OUTPUT_DIR: Path = ROOT_DIR / "output"
OUTPUT_DIR: Path = ROOT_DIR.parent / "output"

SUBMODULES_DIR: Path = ROOT_DIR / "submodules"

LOG_DIR: Path = ROOT_DIR / "logs"


# ─────────────────────────────────────────────────────────────
# PLATINIT VARS
# ─────────────────────────────────────────────────────────────
NAMESPACES_DIR: Path = CONFIG_DIR / "namespaces_scenarios"

# ─────────────────────────────────────────────────────────────
# SYNCCORE VARS
# ─────────────────────────────────────────────────────────────
PTP_PROFILE_DIR: Path = CONFIG_DIR / "ptp_profiles"

NTP_PROFILE_DIR: Path = CONFIG_DIR / "ntp_profiles"

ANSIBLE_API_PATH: Path = SUBMODULES_DIR / "Ansible" / "lib"

# ─────────────────────────────────────────────────────────────
# LOADGEN VARS
# ─────────────────────────────────────────────────────────────
DPDK_DIR: Path = SUBMODULES_DIR / "dpdk" / "usertools"

DPDK_PROFILE_DIR: Path = CONFIG_DIR / "dpdk_profiles"

TGEN_DIR: Path = SUBMODULES_DIR / "traffic_generators"

LOAD_DIR: Path = CONFIG_DIR / "load_scenarios"

# ─────────────────────────────────────────────────────────────
# DATAEX VARS
# ─────────────────────────────────────────────────────────────
DATASOURCES_DIR: Path = CONFIG_DIR / "datasources_scenarios"

# ─────────────────────────────────────────────────────────────
# EXPORCHESTRA
# ─────────────────────────────────────────────────────────────
EXPERIMENTS_DIR: Path = CONFIG_DIR / "experiments_scenarios"

