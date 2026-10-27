#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# global_vars.py

**Project**: Syncarium - Intelligent Timing Platform Toolkit
**Description**: Syncarium global variables
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada
**Created**: 2025-09-19
**Version**: 1.3.0
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

# OUTPUT_DIR: Path = ROOT_DIR / "output"
OUTPUT_DIR: Path = ROOT_DIR.parent / "output"

SUBMODULES_DIR: Path = ROOT_DIR / "submodules"

LOG_DIR: Path = ROOT_DIR / "logs"


# ─────────────────────────────────────────────────────────────
# PLATINIT VARS
# ─────────────────────────────────────────────────────────────

NAMESPACES_DIR: Path = CONFIG_DIR / "namespaces_scenarios"


# ─────────────────────────────────────────────────────────────
# MONHUB VARS
# ─────────────────────────────────────────────────────────────

# Monitoring configuration directory
MONITORING_DIR: Path = CONFIG_DIR / "monitoring"

# Docker Compose deployment file
DOCKER_COMPOSE_FILE: Path = MONITORING_DIR / "docker-compose.yaml"

# Service configuration directories
MQTT_DIR: Path = MONITORING_DIR / "mqtt"

GRAFANA_DIR: Path = MONITORING_DIR / "grafana"

INFLUXDB_DIR: Path = MONITORING_DIR / "influxdb"

# MQTT configuration file
MQTT_CONFIG_FILE: Path = MQTT_DIR / "mosquitto.conf"

# MQTT connection parameters
MQTT_HOST: str = "localhost"

MQTT_PORT: int = 1883

MQTT_TOPIC: str = "syncarium/ptp/#"

MQTT_CLIENT_ID: str = "syncarium-injector"

# InfluxDB connection parameters
INFLUXDB_HOST: str = "localhost"

INFLUXDB_PORT: int = 8086

INFLUXDB_URL: str = f"http://{INFLUXDB_HOST}:{INFLUXDB_PORT}"

INFLUXDB_USERNAME: str = "syncarium"

INFLUXDB_PASSWORD: str = "syncarium"

INFLUXDB_TOKEN: str = "syncarium-local-development-token"

INFLUXDB_ORG: str = "syncarium"

INFLUXDB_BUCKET: str = "ptp_metrics"

# Zero seconds means unlimited retention
INFLUXDB_RETENTION: int = 0

# Grafana connection parameters
GRAFANA_HOST: str = "localhost"

GRAFANA_PORT: int = 3000

GRAFANA_URL: str = f"http://{GRAFANA_HOST}:{GRAFANA_PORT}"

GRAFANA_ADMIN_USER: str = "admin"

GRAFANA_ADMIN_PASSWORD: str = "syncarium"


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
# EXPORCHESTRA VARS
# ─────────────────────────────────────────────────────────────

EXPERIMENTS_DIR: Path = CONFIG_DIR / "experiments_scenarios"