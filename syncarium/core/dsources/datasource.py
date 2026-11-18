import threading
import queue

from typing import Any


class DataSource(threading.Thread):

    def __init__(self, name: str, queue: queue.Queue, event: threading.Event) -> None:
        super().__init__()
        self.name = name
        self.queue = queue
        self.event = event
        self.daemon = True
    
    def send_metric(self, timestamp: float, name: str, value: Any) -> None:
        full_name = f"{name}_{self.name}"
        self.queue.put((timestamp, full_name, value))
        # Metrics could also be forwarded to Prometheus, InfluxDB, MQTT, etc.

    def stop(self) -> None:
        self.event.set()
        self.join()
