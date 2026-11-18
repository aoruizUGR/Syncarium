import yaml
import time
import hashlib

from pathlib import Path

import path_config.global_paths as global_paths


class Experiment:

    def __init__(self, file_cfg: Path = None) -> None:
        with file_cfg.open('r') as file:
            data: dict = yaml.safe_load(file)

            self.fn = file_cfg.stem
            self.fn_absolute_path = Path(file_cfg).resolve()
            self.hash_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:6]
            self.fn_hashid = f"{self.fn}_{self.hash_id}"
            self.start_ts = None
            self.duration = int(data.get("total_duration"))
            self.state = "Queued"
            self.exp_output_dir = global_paths.OUTPUT_DIR / Path(data.get("output_filepath"))
            self.exp_output_dir.mkdir(parents=True, exist_ok=True)

            self.output_yaml = self.exp_output_dir / f"{self.fn_hashid}.yaml"
            self.output_csv  = self.exp_output_dir / f"{self.fn_hashid}.csv"

            self.stl_fn = data.get("stl_profile")
            self.data_extractor_sources = list(data.get("data_extractor_sources", {}).keys())
            self.ptp_clients = list(data.get("ptp_clients", {}).keys())

            self.stl_start = int(data.get("loadgen_stl_start", -1))
            self.stl_duration = self.duration - 60
            self.data_extractor_start = int(data.get("data_extractor_start", 0))
            self.data_extractor_duration = self.duration - self.data_extractor_start
            self.ptp_start = int(data.get("ptp_start"))
            self.ptp_stop_at_end = bool(data.get("ptp_stop_at_end"))
        
