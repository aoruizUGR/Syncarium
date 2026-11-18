import csv
import datetime
import multiprocessing
import queue
import time
import threading
import yaml

from pathlib import Path
from typing import Any, Dict, List, Optional

import path_config.global_paths as global_paths
import syncarium.core.dsources as dsources


class DataExtractor:

    def __init__(self) -> None:
        self.datasources_dir: Path = global_paths.DATASOURCES_DIR
        self.output_dir: Path = global_paths.OUTPUT_DIR
        self.loaded_datasources: List[dsources.DataSource] = []
        self.writer_process: multiprocessing.Process = multiprocessing.Process()
        self.csv_output_filepath: Optional[Path] = None
        self.yaml_output_filepath: Optional[Path] = None
        self.start_time: Optional[float] = None
        self.duration: Optional[int] = None

    def load_datasources(
        self,
        file_cfg: Optional[Path] = None,
    ) -> None:
        if self.writer_process.is_alive():
            return

        self.loaded_datasources.clear()

        if file_cfg:
            filepath_cfg: Path = file_cfg
        else:
            config_files = [f.name for f in Path(self.datasources_dir).glob("*.yaml")]
            if not config_files:
                return
            filepath_cfg = Path(self.datasources_dir) / config_files[0]
            
        try:
            with open(filepath_cfg, 'r') as file:
                yaml_data = yaml.safe_load(file)
                data = yaml_data.get("dataex_datasources", {})

            for source_name, source_info in data.items():
                try:
                    data_class = source_info.pop('data_class')
                    
                    if data_class == 'FileLogDataSource':
                        log_path = global_paths.LOG_DIR / Path(source_info["filepath"])
                        if not log_path.is_file():
                            log_path.parent.mkdir(parents=True, exist_ok=True)
                            log_path.touch()
                        
                        self.loaded_datasources.append({
                            "class": dsources.FileLogDataSource,
                            "name": source_name,
                            "args": {
                                "pattern": source_info["pattern"],
                                "filepath": str(log_path)
                            }
                        })
                    
                    elif data_class == "PPSAnalyzerDataSource":
                        self.loaded_datasources.append({
                            "class": dsources.PPSAnalyzerDataSource,
                            "name": source_name,
                            "args": {
                                "serial_port": source_info["serial_port"],
                                "pps_inputs": source_info["pps_inputs"],
                                "cable_delays": source_info["cable_delays"],
                            }
                        })
                    elif data_class == "CounterDataSource":
                        self.loaded_datasources.append({
                            "class": dsources.CounterDataSource,
                            "name": source_name,
                            "args": {
                                "resource_name": source_info["resource_name"],
                            }
                        })
                except Exception as e:
                    print(f"Error loading data source {source_name}: {e}")
                    continue
        except Exception as e:
            print(f"Error loading datasources: {e}")
            return

    def start_extraction(
        self,
        csv_fn_out: Optional[Path] = None,
        duration_out: Optional[int] = None
    ) -> None:
        if self.writer_process.is_alive() or not self.loaded_datasources:
            return

        if csv_fn_out is None:
            fn: str = "metrics"
            duration: int = 60
            self.csv_output_filepath = self.output_dir / f"{fn}.csv"
            self.yaml_output_filepath = self.output_dir / f"{fn}.yaml"
        else:
            duration = duration_out if duration_out is not None else 60
            self.csv_output_filepath = csv_fn_out

        self.csv_output_filepath.parent.mkdir(exist_ok=True, parents=True)
        self.yaml_output_filepath.parent.mkdir(exist_ok=True, parents=True)

        self.start_time = time.time()
        self.duration = duration

        source_configs = [
            {
                "class": source["class"],
                "name": source["name"],
                "args": source["args"]
            }
            for source in self.loaded_datasources
        ]

        self.writer_process = multiprocessing.Process(
            target=self.write_metrics,
            args=(duration, source_configs)
        )
        self.writer_process.start()

    def write_metrics(
        self,
        duration: int,
        source_configs: List[Dict[str, Any]]
    ) -> None:
        import signal

        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, lambda signum, frame: event.set())

        event = threading.Event()
        q: queue.Queue = queue.Queue(maxsize=1000)

        sources = []
        for config in source_configs:
            try:
                source_class = config["class"]
                name = config["name"]
                args = config["args"]
                source = source_class(name, q, event, **args)
                source.start()
                sources.append(source)
            except Exception:
                continue

        try:
            with self.csv_output_filepath.open("w", newline="", buffering=1) as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "metric", "value"])

                t_end = time.time() + duration
                while time.time() < t_end and not event.is_set():
                    try:
                        timestamp, metric, value = q.get(timeout=1)
                        writer.writerow([timestamp, metric, value])
                    except queue.Empty:
                        continue
        finally:
            event.set()
            for source in sources:
                source.join()

            self.stop_time = time.time()
            stop_time_hr = datetime.datetime.fromtimestamp(self.stop_time).strftime("%d-%m-%Y %H:%M:%S")

    def stop_extraction(self) -> None:
        if not self.writer_process.is_alive():
            return

        self.writer_process.terminate()
        self.writer_process.join()

        self.csv_output_filepath = None
        self.start_time = None
        self.duration = None