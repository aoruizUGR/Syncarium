import os
import re
import time
import queue
import threading

from pathlib import Path
from typing import Generator, TextIO, Pattern

from syncarium.core.dsources import DataSource

class FileLogDataSource(DataSource):

    def __init__(self, name: str, queue: queue.Queue, event: threading.Event, pattern: str, filepath: str) -> None:
        super().__init__(name, queue, event)
        self.pattern: Pattern = re.compile(pattern)
        self.filepath: str = filepath
        if not Path(self.filepath).is_file():
            raise FileNotFoundError(f"❌ Log file not found: {self.filepath}")

    def follow(self, file: TextIO) -> Generator[str, None, None]:
        file.seek(0, os.SEEK_END)
        while not self.event.is_set():
            line = file.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line

    def run(self) -> None:
        try:
            with open(self.filepath, 'r', encoding='utf-8') as file:
                for line in self.follow(file):
                    match = self.pattern.search(line)
                    if not match:
                        continue

                    timestamp = time.time_ns()
                    for name, value in match.groupdict().items():
                        self.send_metric(timestamp, name, value)
        except Exception as e:
            print(f"[{self.name}] ⚠️ Error: {e}")


