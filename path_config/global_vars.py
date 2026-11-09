#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
global_vars.py

**Project**: Syncarium - Intelligent Timing Platform Toolkit
**Description**: Syncarium global variables
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada
**License**: GPLv3
"""

from pathlib import Path

# ─────────────────────────────────────────────────────────────
# MAIN DIRS VARS
# ─────────────────────────────────────────────────────────────

ROOT_DIR: Path = Path(__file__).resolve().parent.parent

SYNCARIUM_DIR: Path = ROOT_DIR / "syncarium"

CONFIG_DIR: Path = SYNCARIUM_DIR / "presets"

UTILS_DIR: Path = SYNCARIUM_DIR / "utils"

SCRIPTS_DIR: Path = SYNCARIUM_DIR / "scripts"

OUTPUT_DIR: Path = ROOT_DIR / "output"

LOG_DIR: Path = ROOT_DIR / "logs"


# ─────────────────────────────────────────────────────────────
# PLATINIT VARS
# ─────────────────────────────────────────────────────────────

NAMESPACES_DIR: Path = CONFIG_DIR / "namespaces"

# ─────────────────────────────────────────────────────────────
# SYNCCORE VARS
# ─────────────────────────────────────────────────────────────

LINUXPTP_DIR: Path = ROOT_DIR.parent / "linuxptp_versions" / "linuxptp-3.1.1" #  <-------- Config LinuxPTP personal path

PTP_PROFILE_DIR: Path = CONFIG_DIR / "ptp"

NTP_PROFILE_DIR: Path = CONFIG_DIR / "ntp"

ANSIBLE_API_PATH: Path = Path("")

# ─────────────────────────────────────────────────────────────
# LOADGEN VARS
# ─────────────────────────────────────────────────────────────

DPDK_PROFILE_DIR: Path = CONFIG_DIR / "dpdk"

TGEN_DIR: Path = Path("")

LOAD_DIR: Path = CONFIG_DIR / "load"


# ─────────────────────────────────────────────────────────────
# DATAEX VARS
# ─────────────────────────────────────────────────────────────

DATASOURCES_DIR: Path = CONFIG_DIR / "datasources"


# ─────────────────────────────────────────────────────────────
# EXPORCHESTRA VARS
# ─────────────────────────────────────────────────────────────

EXPERIMENTS_DIR: Path = CONFIG_DIR / "experiments"

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