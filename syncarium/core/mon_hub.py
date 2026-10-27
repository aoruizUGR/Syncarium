#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# mon_hub.py

**Project**: Syncarium - Intelligent Timing Platform Toolkit
**Description**: Syncarium Monitoring & Telemetry Hub
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada
**Created**: 2026-10-26
**Version**: 1.3.0
**License**: GPLv3
"""


# ─────────────────────────────────────────────────────────────────────────────
# Standard Library Imports
import os
import subprocess
import webbrowser
from pathlib import Path
from typing import Any, Callable, Dict, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Third-Party Imports
# (None used directly in this file)


# ─────────────────────────────────────────────────────────────────────────────
# Local Application Imports
import syncarium.utils as utils
import syncarium.options.global_vars as global_vars


# ─────────────────────────────────────────────────────────────
# 📊 MonHub Class
# ─────────────────────────────────────────────────────────────
class MonHub:
    """
    Monitoring and Telemetry Hub for Syncarium.

    Provides deployment and management of the monitoring infrastructure used
    for real-time telemetry transport, storage, and visualization.

    The monitoring infrastructure is based on:

    - Mosquitto MQTT Broker for telemetry transport.
    - InfluxDB for time-series data storage.
    - Grafana for real-time visualization.
    - An internal MQTT to InfluxDB injector.

    The internal injector subscribes to the configured Syncarium MQTT topics,
    processes incoming telemetry messages, and stores the resulting measurements
    in InfluxDB.

    The injector is started and stopped automatically together with the
    monitoring infrastructure. It is not exposed as an independent component
    through the TUI.

    ### Attributes
    - **vt** (`utils.ViewTools`): Utility tools for rendering terminal views.
    - **monitoring_dir** (`Path`): Root monitoring configuration directory.
    - **compose_file** (`Path`): Docker Compose deployment file.
    - **mqtt_dir** (`Path`): MQTT configuration directory.
    - **grafana_dir** (`Path`): Grafana configuration directory.
    - **influxdb_dir** (`Path`): InfluxDB configuration directory.
    - **grafana_url** (`str`): URL used to access Grafana.
    - **mqtt_host** (`str`): MQTT broker hostname or address.
    - **mqtt_port** (`int`): MQTT broker TCP port.
    - **influxdb_url** (`str`): URL used to access InfluxDB.
    - **influxdb_org** (`str`): InfluxDB organization name.
    - **influxdb_bucket** (`str`): InfluxDB telemetry bucket.
    - **active_clients** (`Dict[str, Dict[str, Any]]`): Known telemetry clients.
    - **injector_process** (`Optional[Any]`): Internal injector runtime handle.
    """


# ─────────────────────────────────────────────────────────────────────────────
# 🚧 Function: constructorl
# ─────────────────────────────────────────────────────────────────────────────
    def __init__(
        self,
        vt: utils.ViewTools
    ) -> None:
        """
        Initializes the Monitoring and Telemetry Hub.

        Sets up the Docker Compose deployment, monitoring service endpoints,
        environment variables, and runtime state required to manage the
        complete observability infrastructure.

        ### Args:
        - **vt** (`utils.ViewTools`): Utility tools for rendering terminal views.
        """

        # Store the shared ViewTools instance
        self.vt: utils.ViewTools = vt

        # Docker Compose deployment file
        self.compose_file: Path = global_vars.DOCKER_COMPOSE_FILE

        # MQTT service configuration used by the internal injector
        self.mqtt_host: str = global_vars.MQTT_HOST
        self.mqtt_port: int = global_vars.MQTT_PORT
        self.mqtt_topic: str = global_vars.MQTT_TOPIC
        self.mqtt_client_id: str = global_vars.MQTT_CLIENT_ID

        # InfluxDB service configuration used by the internal injector
        self.influxdb_url: str = global_vars.INFLUXDB_URL
        self.influxdb_token: str = global_vars.INFLUXDB_TOKEN
        self.influxdb_org: str = global_vars.INFLUXDB_ORG
        self.influxdb_bucket: str = global_vars.INFLUXDB_BUCKET

        # Grafana service endpoint
        self.grafana_url: str = global_vars.GRAFANA_URL

        # Environment variables passed to Docker Compose
        self.compose_environment: Dict[str, str] = os.environ.copy()

        self.compose_environment.update({
            "MQTT_PORT": str(global_vars.MQTT_PORT),
            "INFLUXDB_PORT": str(global_vars.INFLUXDB_PORT),
            "INFLUXDB_USERNAME": global_vars.INFLUXDB_USERNAME,
            "INFLUXDB_PASSWORD": global_vars.INFLUXDB_PASSWORD,
            "INFLUXDB_TOKEN": global_vars.INFLUXDB_TOKEN,
            "INFLUXDB_ORG": global_vars.INFLUXDB_ORG,
            "INFLUXDB_BUCKET": global_vars.INFLUXDB_BUCKET,
            "INFLUXDB_RETENTION": str(global_vars.INFLUXDB_RETENTION),
            "GRAFANA_PORT": str(global_vars.GRAFANA_PORT),
            "GRAFANA_ADMIN_USER": global_vars.GRAFANA_ADMIN_USER,
            "GRAFANA_ADMIN_PASSWORD": global_vars.GRAFANA_ADMIN_PASSWORD,
        })

        # Runtime telemetry client information
        self.active_clients: Dict[str, Dict[str, Any]] = {}

        # Internal MQTT to InfluxDB injector handle
        self.injector_process: Optional[Any] = None


# ─────────────────────────────────────────────────────────────────────────────
# 📋 Function: main_menu
# ─────────────────────────────────────────────────────────────────────────────
    def main_menu(self) -> None:
        """
        Displays and manages the interactive MonHub menu.

        Continuously renders a terminal-based menu using `ViewTools`, allowing
        the user to deploy, stop, inspect, and access the Syncarium monitoring
        infrastructure.

        The loop runs until the user selects **"❌ Exit"** or interrupts the
        execution with **Ctrl+C**.

        ### Menu Options:
        - 🚀 Start Monitoring Infrastructure → `start_infrastructure`
        - 🛑 Stop Monitoring Infrastructure → `stop_infrastructure`
        - 📡 Show Infrastructure Status → `show_status`
        - 👥 Show Connected Clients → `show_clients`
        - 📈 Open Grafana Dashboard → `open_grafana`
        - 🔄 Refresh View → refreshes the current menu
        - ❌ Exit → exits the MonHub menu

        ### Notes:
        - Starting the infrastructure also starts the internal telemetry injector.
        - Stopping the infrastructure also stops the internal telemetry injector.
        - Graceful menu termination is supported through **Ctrl+C**.
        """

        try:
            while True:
                # Display software title
                self.vt.console_software_title(delay=0)

                # Display MonHub menu title
                self.vt.console_message(
                    "main_title",
                    "Monitoring & Telemetry Hub",
                    "📊"
                )

                # Display interactive menu
                choice: str = self.vt.console_select_menu(
                    choices=[
                        {"name": "🚀 Start Monitoring Infrastructure", "value": "start_infrastructure"},
                        {"name": "🛑 Stop Monitoring Infrastructure", "value": "stop_infrastructure"},
                        {"name": "📡 Show Infrastructure Status", "value": "show_status"},
                        {"name": "👥 Show Connected Clients", "value": "show_clients"},
                        {"name": "📈 Open Grafana Dashboard", "value": "open_grafana"},
                        {"name": "🔄 Refresh View", "value": "refresh_view"},
                        {"name": "❌ Exit", "value": "exit"}
                    ],
                    indent=1
                )

                # Map menu options to corresponding methods
                submenu: Dict[str, Callable[[], None]] = {
                    "start_infrastructure": self.start_infrastructure,
                    "stop_infrastructure": self.stop_infrastructure,
                    "show_status": self.show_status,
                    "show_clients": self.show_clients,
                    "open_grafana": self.open_grafana,
                }

                # Handle user selection
                if choice == "exit":
                    break

                elif choice != "refresh_view":
                    action: Optional[Callable[[], None]] = submenu.get(choice)

                    if action:
                        action()
                        input("\n🔙 Press ⏎ to return to the menu...")

        except KeyboardInterrupt:
            # Gracefully handle Ctrl+C interruption
            self.vt.console_message("exit", "Exiting...")


# ─────────────────────────────────────────────────────────────────────────────
# 🚀 Function: start_infrastructure
# ─────────────────────────────────────────────────────────────────────────────
    def start_infrastructure(self) -> None:
        """
        Starts the complete Syncarium monitoring infrastructure.

        Deploys all services defined in the MonHub Docker Compose stack.
        The stack is expected to contain:

        - Mosquitto MQTT Broker.
        - InfluxDB.
        - Grafana.

        The configuration values required by Docker Compose are obtained from
        `global_vars` and passed through `compose_environment`.

        Once Docker Compose successfully starts the required containers and
        confirms that the services are healthy, the internal MQTT to InfluxDB
        injector is started automatically.

        ### Notes:
        - Docker Engine and Docker Compose must be available.
        - Containers are started in detached mode.
        - Service health checks must be defined in Docker Compose.
        - The injector remains transparent to the user.
        """

        # Display section title
        self.vt.console_message(
            "title",
            "Starting Monitoring Infrastructure",
            "🚀"
        )

        # Validate Docker Compose file
        if not self.compose_file.is_file():
            self.vt.console_message(
                "error",
                f"Docker Compose file not found: {self.compose_file}",
                indent=1
            )
            return

        try:
            # Start all monitoring containers in detached mode
            self.vt.console_message(
                "info",
                "Starting monitoring containers...",
                indent=1
            )

            result: subprocess.CompletedProcess[str] = subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    str(self.compose_file),
                    "up",
                    "-d",
                    "--wait"
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=self.compose_file.parent,
                env=self.compose_environment
            )

            # Display relevant Docker Compose output
            if result.stdout.strip():
                self.vt.console.print(result.stdout.rstrip())

            # Start the internal MQTT to InfluxDB injector
            self._start_injector()

            # Notify successful startup
            self.vt.console_message(
                "success",
                "Monitoring infrastructure started successfully.",
                indent=1
            )

        except FileNotFoundError:
            # Docker command is unavailable
            self.vt.console_message(
                "error",
                "Docker command not found. Verify that Docker is installed.",
                indent=1
            )

        except subprocess.CalledProcessError as e:
            # Extract Docker Compose error output
            error_message: str = (
                e.stderr.strip()
                if e.stderr and e.stderr.strip()
                else str(e)
            )

            self.vt.console_message(
                "error",
                f"Unable to start monitoring infrastructure: {error_message}",
                indent=1
            )

        except Exception as e:
            # Handle unexpected startup errors
            self.vt.console_message(
                "error",
                f"Unexpected error starting monitoring infrastructure: {e}",
                indent=1
            )


# ─────────────────────────────────────────────────────────────────────────────
# 🛑 Function: stop_infrastructure
# ─────────────────────────────────────────────────────────────────────────────
    def stop_infrastructure(self) -> None:
        """
        Stops the Syncarium monitoring infrastructure.

        Stops the internal MQTT to InfluxDB injector and shuts down all
        containers belonging to the MonHub Docker Compose stack.

        Docker volumes are preserved so that InfluxDB measurements, Grafana
        configuration, and MQTT persistent data remain available after the
        infrastructure is started again.

        ### Notes:
        - The injector is stopped before the MQTT broker and InfluxDB.
        - Docker Compose removes the stack containers and network.
        - Persistent Docker volumes are not removed.
        """

        # Display section title
        self.vt.console_message(
            "title",
            "Stopping Monitoring Infrastructure",
            "🛑"
        )

        # Validate Docker Compose file
        if not self.compose_file.is_file():
            self.vt.console_message(
                "error",
                f"Docker Compose file not found: {self.compose_file}",
                indent=1
            )
            return

        try:
            # Stop the internal MQTT to InfluxDB injector
            self._stop_injector()

            # Stop all monitoring containers
            self.vt.console_message(
                "info",
                "Stopping monitoring containers...",
                indent=1
            )

            result: subprocess.CompletedProcess[str] = subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    str(self.compose_file),
                    "down"
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=self.compose_file.parent,
                env=self.compose_environment
            )

            # Display relevant Docker Compose output
            if result.stdout.strip():
                self.vt.console.print(result.stdout.rstrip())

            # Clear registered runtime clients
            self.active_clients.clear()

            # Notify successful shutdown
            self.vt.console_message(
                "success",
                "Monitoring infrastructure stopped successfully.",
                indent=1
            )

        except FileNotFoundError:
            # Docker command is unavailable
            self.vt.console_message(
                "error",
                "Docker command not found. Verify that Docker is installed.",
                indent=1
            )

        except subprocess.CalledProcessError as e:
            # Extract Docker Compose error output
            error_message: str = (
                e.stderr.strip()
                if e.stderr and e.stderr.strip()
                else str(e)
            )

            self.vt.console_message(
                "error",
                f"Unable to stop monitoring infrastructure: {error_message}",
                indent=1
            )

        except Exception as e:
            # Handle unexpected shutdown errors
            self.vt.console_message(
                "error",
                f"Unexpected error stopping monitoring infrastructure: {e}",
                indent=1
            )


# ─────────────────────────────────────────────────────────────────────────────
# 📡 Function: show_status
# ─────────────────────────────────────────────────────────────────────────────
    def show_status(self) -> None:
        """
        Displays the current monitoring infrastructure status.

        Queries Docker Compose and displays the state of every container
        belonging to the MonHub monitoring stack, including stopped or failed
        containers.

        Possible states may include:

        - Running.
        - Exited.
        - Restarting.
        - Created.
        - Healthy.
        - Unhealthy.

        The current internal injector state is displayed after the container
        status.

        ### Notes:
        - This method does not modify the monitoring infrastructure.
        - Docker Compose environment variables are obtained from `global_vars`.
        - Stopped containers are included using the `--all` option.
        """

        # Display section title
        self.vt.console_message(
            "title",
            "Monitoring Infrastructure Status",
            "📡"
        )

        # Validate Docker Compose file
        if not self.compose_file.is_file():
            self.vt.console_message(
                "error",
                f"Docker Compose file not found: {self.compose_file}",
                indent=1
            )
            return

        try:
            # Query monitoring container status
            result: subprocess.CompletedProcess[str] = subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    str(self.compose_file),
                    "ps",
                    "--all"
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=self.compose_file.parent,
                env=self.compose_environment
            )

            # Display Docker Compose status
            if result.stdout.strip():
                self.vt.console.print(result.stdout.rstrip())

            else:
                self.vt.console_message(
                    "info",
                    "No monitoring containers have been created.",
                    indent=1
                )

            # Display internal injector status
            injector_status: str = (
                "Running"
                if self.injector_process is not None
                else "Stopped"
            )

            self.vt.console_message(
                "info",
                f"Internal telemetry injector: {injector_status}",
                indent=1
            )

        except FileNotFoundError:
            # Docker command is unavailable
            self.vt.console_message(
                "error",
                "Docker command not found. Verify that Docker is installed.",
                indent=1
            )

        except subprocess.CalledProcessError as e:
            # Extract Docker Compose error output
            error_message: str = (
                e.stderr.strip()
                if e.stderr and e.stderr.strip()
                else str(e)
            )

            self.vt.console_message(
                "error",
                f"Unable to obtain monitoring status: {error_message}",
                indent=1
            )

        except Exception as e:
            # Handle unexpected status errors
            self.vt.console_message(
                "error",
                f"Unexpected error obtaining monitoring status: {e}",
                indent=1
            )


# ─────────────────────────────────────────────────────────────────────────────
# 👥 Function: show_clients
# ─────────────────────────────────────────────────────────────────────────────
    def show_clients(self) -> None:
        """
        Displays telemetry clients known by the monitoring platform.

        Shows clients that have published telemetry data through MQTT and have
        been registered by the internal injector.

        Each client entry may contain information such as:

        - Hostname.
        - Namespace or network interface.
        - Last-seen timestamp.
        - MQTT topic.
        - Current synchronization state.

        ### Notes:
        - Client tracking will be populated by the injector.
        - The exact client metadata depends on the MQTT message schema.
        - This initial implementation displays the current dictionary contents.
        """

        # Display section title
        self.vt.console_message(
            "title",
            "Connected Telemetry Clients",
            "👥"
        )

        # Notify if no clients are currently registered
        if not self.active_clients:
            self.vt.console_message(
                "info",
                "No telemetry clients registered yet.",
                indent=1
            )
            return

        # Display each known telemetry client
        for client_name, client_info in sorted(self.active_clients.items()):
            self.vt.console_message(
                "info",
                f"{client_name}: {client_info}",
                indent=1
            )


# ─────────────────────────────────────────────────────────────────────────────
# 📈 Function: open_grafana
# ─────────────────────────────────────────────────────────────────────────────
    def open_grafana(self) -> None:
        """
        Opens the Grafana interface in the default web browser.

        Uses the configured Grafana URL from `global_vars` and requests the
        operating system to open it with the default browser.

        ### Notes:
        - Grafana must be running and reachable from the local machine.
        - Opening the browser does not guarantee that Grafana is healthy.
        """

        # Display section title
        self.vt.console_message(
            "title",
            "Opening Grafana Dashboard",
            "📈"
        )

        try:
            # Open Grafana in the default browser
            opened: bool = webbrowser.open(self.grafana_url)

            if opened:
                self.vt.console_message(
                    "success",
                    f"Grafana opened at: {self.grafana_url}",
                    indent=1
                )

            else:
                self.vt.console_message(
                    "caution",
                    f"Unable to open a browser automatically. Access Grafana at: {self.grafana_url}",
                    indent=1
                )

        except Exception as e:
            # Handle browser execution errors
            self.vt.console_message(
                "error",
                f"Unable to open Grafana: {e}",
                indent=1
            )


# ─────────────────────────────────────────────────────────────────────────────
# 🔒 Function: _start_injector
# ─────────────────────────────────────────────────────────────────────────────
    def _start_injector(self) -> None:
        """
        Starts the internal MQTT to InfluxDB injector.

        The injector is responsible for subscribing to the configured Syncarium
        MQTT topics and writing received telemetry measurements into InfluxDB.

        It is started automatically after the Docker Compose monitoring services
        have been deployed.

        ### Notes:
        - This is an internal function.
        - It is not exposed through the TUI.
        - The MQTT and InfluxDB implementation will replace the current placeholder.
        """

        # Prevent duplicate injector instances
        if self.injector_process is not None:
            self.vt.console_message(
                "info",
                "Internal telemetry injector is already running.",
                indent=2
            )
            return

        # TODO:
        # Replace this placeholder with the MQTT subscriber implementation.
        #
        # The injector will:
        # 1. Connect to the Mosquitto MQTT broker.
        # 2. Subscribe to the configured Syncarium telemetry topics.
        # 3. Validate and normalize incoming telemetry messages.
        # 4. Register active telemetry clients.
        # 5. Write telemetry measurements into InfluxDB.

        self.injector_process = True

        self.vt.console_message(
            "success",
            "Internal telemetry injector started.",
            indent=2
        )


# ─────────────────────────────────────────────────────────────────────────────
# 🔒 Function: _stop_injector
# ─────────────────────────────────────────────────────────────────────────────
    def _stop_injector(self) -> None:
        """
        Stops the internal MQTT to InfluxDB injector.

        Releases resources associated with MQTT subscriptions and terminates the
        internal injector runtime.

        It is called automatically before stopping the Docker Compose monitoring
        infrastructure.

        ### Notes:
        - This is an internal function.
        - It is not exposed through the TUI.
        - The final implementation should disconnect MQTT gracefully.
        """

        # Check whether the injector is running
        if self.injector_process is None:
            self.vt.console_message(
                "info",
                "Internal telemetry injector is not running.",
                indent=2
            )
            return

        # TODO:
        # Replace this placeholder with the graceful MQTT injector shutdown.

        self.injector_process = None

        self.vt.console_message(
            "success",
            "Internal telemetry injector stopped.",
            indent=2
        )


# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: exit
# ─────────────────────────────────────────────────────────────────────────────
    def exit(self) -> None:
        """
        Performs MonHub cleanup operations.

        Stops the internal telemetry injector if it is active. This method does
        not automatically stop the Docker Compose monitoring infrastructure,
        allowing Mosquitto, InfluxDB, and Grafana to continue running after the
        Syncarium TUI exits.

        To stop the complete monitoring platform, use
        `stop_infrastructure()` explicitly.
        """

        # Stop only the injector owned by the current Syncarium process
        self._stop_injector()