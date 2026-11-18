import time
import threading

from pathlib import Path
from typing import List, Tuple, Callable, Optional, Deque
from collections import deque

import path_config.global_paths as global_vars
from syncarium.core import LocalManager, TrafficGenerator
from syncarium.core.experiment import Experiment
from syncarium.core.data_extractor import DataExtractor


class ExperimentOrchestrator:
    
    def __init__(
        self,
        local_manager: LocalManager,
        traffic_gen: TrafficGenerator
    ) -> None:
        self.local_manager: LocalManager = local_manager
        self.traffic_gen: TrafficGenerator = traffic_gen
        self.data_extractor: DataExtractor = DataExtractor()

        self.queue: Deque[Experiment] = deque()

        self.current_experiment: Experiment = None

        self.thread: threading.Thread | None = None
        self.stop_event: threading.Event = threading.Event()
        self.interexp_delay: Optional[int] = 900

        self.exp_dir: Path = global_vars.EXPERIMENTS_DIR

    def interrupted_sleep(self, seconds: float, stop_event: threading.Event) -> None:
        interval: float = 0.5
        elapsed: float = 0.0
        while elapsed < seconds:
            if stop_event.is_set():
                break
            time.sleep(min(interval, seconds - elapsed))
            elapsed += interval

    def launch_first_exp(self) -> None:
        if len(self.queue) == 0:
            return

        self.current_experiment = self.queue.popleft()

        def thread_target() -> None:
            try:
                self.launch_an_experiment()
            except Exception:
                pass

        self.stop_event.clear()
        self.thread = threading.Thread(target=thread_target, daemon=True)
        self.thread.start()

    def launch_an_experiment(self) -> None:
        if self.current_experiment.ptp_start != -1:
            self.local_manager.stop_ptp()
            self.local_manager.load_clients(file_cfg=self.current_experiment.fn_absolute_path)

        self.data_extractor.load_datasources(file_cfg=self.current_experiment.fn_absolute_path)

        self.current_experiment.state = "Running"
        start_time: float = time.time()
        self.current_experiment.start_ts = start_time

        tasks: List[Tuple[int, Callable[[], None], str]] = [
            (
                self.current_experiment.data_extractor_start,
                lambda: self.data_extractor.start_extraction(
                    csv_fn_out      = self.current_experiment.output_csv,
                    duration_out    = self.current_experiment.data_extractor_duration
                ),
                "DataExtractor"
            )
        ]

        if self.current_experiment.ptp_start != -1:
            tasks.append((
                self.current_experiment.ptp_start,
                lambda: self.local_manager.start_ptp(
                    stop            = False
                ),
                "LocalManager"
            ))

        if self.current_experiment.stl_start != -1:
            tasks.append((
                self.current_experiment.stl_start,
                lambda: self.traffic_gen.start_stl_program(
                    file_cfg        = self.current_experiment.fn_absolute_path,
                    stl_duration    = self.current_experiment.stl_duration,
                    stl_output      = self.current_experiment.output_yaml
                ),
                "TrafficGenerator"
            ))

        tasks.sort(key=lambda x: x[0])

        for delay, func, name in tasks:
            now: float = time.time()
            wait_time: float = delay - (now - start_time)
            if wait_time > 0:
                self.interrupted_sleep(wait_time, self.stop_event)
            
            if self.stop_event.is_set():
                break

            try:
                func()
            except Exception as e:
                pass

        if not self.stop_event.is_set():
            pass

        remaining: float = self.current_experiment.duration - (time.time() - start_time)
        if remaining > 0:
            self.interrupted_sleep(remaining, self.stop_event)
        
        if self.stop_event.is_set():
            self.interrupted_sleep(10, self.stop_event)
            self.current_experiment.state = "Stopped"

        else:
            self.current_experiment.state = "Finished"
            if self.current_experiment.ptp_stop_at_end is True:
                self.local_manager.stop_ptp()

    def stop_current_exp(self) -> None:
        if self.current_experiment.state != "Running":
            return

        errors: List[str] = []
        self.stop_event.set()

        if self.current_experiment.ptp_start != -1:
            try:
                self.local_manager.stop_ptp()
            except Exception as e:
                errors.append(f"PTP: {e}")

        try:
            self.data_extractor.stop_extraction()
        except Exception as e:
            errors.append(f"DataExtractor: {e}")

        if self.current_experiment.stl_start != -1:
            try:
                self.traffic_gen.stop_stl_program()
            except Exception as e:
                errors.append(f"STL: {e}")

        if errors:
            for err in errors:
                pass
                return
            
        self.thread.join(timeout=5)
        self.current_experiment.state = "Stopped"

    def launch_queue(self) -> None:
        if len(self.queue) == 0:
            return

        
        def queue_runner(stop_event: threading.Event) -> None:
            while len(self.queue) != 0:
                if stop_event.is_set():
                    break

                self.launch_first_exp()

                if stop_event.is_set():
                    break

                for _ in range(int(self.current_experiment.duration + self.interexp_delay)):
                    if stop_event.is_set():
                        break
                    time.sleep(1)

        self.queue_thread = threading.Thread(target=lambda: queue_runner(self.stop_event), daemon=True)
        self.queue_thread.start()

    def stop_queue(self) -> None:
        self.stop_event.set()

        self.stop_current_exp()

        self.queue_thread.join()


    def set_interexp_delay(self) -> None:
        self.interexp_delay = 900

    def clean_experiment(self) -> None:
        if self.current_experiment:
            self.current_experiment = None
