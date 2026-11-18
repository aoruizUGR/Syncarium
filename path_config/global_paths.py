from pathlib import Path


ROOT_DIR: Path = Path(__file__).resolve().parent.parent

SYNCARIUM_DIR: Path = ROOT_DIR / "syncarium"

PRESET_DIR: Path = SYNCARIUM_DIR / "presets"

UTILS_DIR: Path = SYNCARIUM_DIR / "utils"

SCRIPTS_DIR: Path = SYNCARIUM_DIR / "scripts"

OUTPUT_DIR: Path = ROOT_DIR / "output"

LOG_DIR: Path = ROOT_DIR / "logs"

LINUXPTP_DIR: Path = ROOT_DIR.parent / "linuxptp_versions" / "linuxptp-3.1.1" #  <-------- Config LinuxPTP personal path

TGEN_DIR: Path = ROOT_DIR.parent / "traffic_generators"

DPDK_PROFILE_DIR: Path = PRESET_DIR / "dpdk"

NAMESPACES_PROFILE_DIR: Path = PRESET_DIR / "namespaces"

PTP_CLIENTS_PROFILE_DIR: Path = PRESET_DIR / "ptp"

LINUXPTP_PROFILE_DIR: Path = PRESET_DIR / PTP_CLIENTS_PROFILE_DIR / "linuxptp"

TRAFFIC_PROFILE_DIR: Path = PRESET_DIR / "traffic"

DATASOURCES_DIR: Path = PRESET_DIR / "datasources"

EXPERIMENTS_DIR: Path = PRESET_DIR / "experiments"

MONITORING_DIR: Path = PRESET_DIR / "monitoring"

DOCKER_COMPOSE_FILE: Path = MONITORING_DIR / "docker-compose.yaml"

MQTT_DIR: Path = MONITORING_DIR / "mqtt"

GRAFANA_DIR: Path = MONITORING_DIR / "grafana"

INFLUXDB_DIR: Path = MONITORING_DIR / "influxdb"

MQTT_CONFIG_FILE: Path = MQTT_DIR / "mosquitto.conf"

MQTT_HOST: str = "localhost"

MQTT_PORT: int = 1883

MQTT_TOPIC: str = "syncarium/ptp/#"

MQTT_CLIENT_ID: str = "syncarium-injector"

INFLUXDB_HOST: str = "localhost"

INFLUXDB_PORT: int = 8086

INFLUXDB_URL: str = f"http://{INFLUXDB_HOST}:{INFLUXDB_PORT}"

INFLUXDB_USERNAME: str = "syncarium"

INFLUXDB_PASSWORD: str = "syncarium"

INFLUXDB_TOKEN: str = "syncarium-local-development-token"

INFLUXDB_ORG: str = "syncarium"

INFLUXDB_BUCKET: str = "ptp_metrics"

INFLUXDB_RETENTION: int = 0

GRAFANA_HOST: str = "localhost"

GRAFANA_PORT: int = 3000

GRAFANA_URL: str = f"http://{GRAFANA_HOST}:{GRAFANA_PORT}"

GRAFANA_ADMIN_USER: str = "admin"

GRAFANA_ADMIN_PASSWORD: str = "syncarium"