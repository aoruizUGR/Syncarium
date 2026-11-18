import time
import queue
import threading
import serial

from datetime import datetime, timedelta
from typing import List
from functools import reduce

from syncarium.core.dsources import DataSource


class PPSAnalyzerDataSource(DataSource):
    
    def __init__(self, name: str, queue: queue.Queue, event: threading.Event, serial_port: str = "/dev/ttyUSB1", pps_inputs: List[int] | None = None, cable_delays: List[int] | None = None) -> None:
        super().__init__(name, queue, event)
        self.NUM_TSU = 9
        self.REG = {
            "ENABLE": 0x00,
            "POLARITY": 0x08,
            "VERSION": 0x0C,
            "CABLE_DELAY": 0x20,
            "INT_CLEAR": 0x30,
            "INT_ENABLE": 0x34,
            "EVENT_COUNT": 0x38,
            "TS_NS": 0x44,
            "TS_S": 0x48
        }
        self.port = serial_port
        self.uart = None
        self.pps_inputs = pps_inputs if pps_inputs is not None else list(range(self.NUM_TSU))
        self.cable_delays = cable_delays if cable_delays is not None else [0] * self.NUM_TSU
        if len(self.pps_inputs) != len(self.cable_delays):
            raise ValueError("❌ 'pps_inputs' and 'cable_delays' must have the same length.")
        self.tsu_state = [False] * self.NUM_TSU
        self.base_addrs = [0x10000000 * (i + 1) for i in range(self.NUM_TSU)]

    def _checksum(self, data: str) -> str:
        return format(reduce(lambda x, y: x ^ ord(y), data, 0), 'X').zfill(2)

    def _comm(self, code: str, fields: List[str] = [], tries: int = 2) -> List[str]:
        for attempt in range(tries):
            try:
                payload = f"{code}{',' if fields else ''}{','.join(fields)}"
                checksum = self._checksum(payload)
                tx = f"${payload}*{checksum}\r\n"
                self.uart.write(tx.encode())
                rx = self.uart.readline().decode().strip()
                if not rx.startswith('$'):
                    raise Exception("Invalid response format")
                content, received_chk = rx[1:].split("*")
                if received_chk != self._checksum(content):
                    raise Exception("Checksum mismatch")
                parts = content.split(',')
                if parts[0] == "ER":
                    raise Exception("Device returned an error")
                return parts[1:]
            except Exception:
                if attempt == tries - 1:
                    raise
                self.uart.close()
                self.uart = serial.Serial(port=self.port, baudrate=1000000, timeout=3)

    def _read(self, addr: int | str) -> int:
        addr = f"0x{addr:08X}" if not isinstance(addr, str) else addr
        return int(self._comm("RC", [addr])[1], 16)

    def _write(self, addr: int | str, val: int | str) -> None:
        addr = f"0x{addr:08X}" if not isinstance(addr, str) else addr
        if not isinstance(val, str):
            val = val & 0xFFFFFFFF
            val = f"0x{val:08X}"
        self._comm("WC", [addr, val])

    def setUp(self) -> None:
        self.uart = serial.Serial(port=self.port, baudrate=1000000, timeout=3)
        self._comm("CC")
        for i in range(len(self.pps_inputs)):
            self.setEnable(self.pps_inputs[i], True)
            self._write(self.base_addrs[self.pps_inputs[i]] + self.REG["CABLE_DELAY"], self.cable_delays[i])

    def setEnable(self, idx: int, enable: bool) -> None:
        base = self.base_addrs[idx]
        self._write(base + self.REG["ENABLE"], int(enable))
        if enable:
            self._write(base + self.REG["INT_ENABLE"], 1)
            self._write(base + self.REG["INT_CLEAR"], 1)
        self.tsu_state[idx] = enable

    def hasTimestamp(self, idx: int) -> bool:
        return self._read(self.base_addrs[idx] + self.REG["INT_CLEAR"]) > 0

    def getEventCount(self, idx: int) -> int:
        return self._read(self.base_addrs[idx] + self.REG["EVENT_COUNT"])

    def readTimestamp(self, idx: int) -> tuple[int, int]:
        base = self.base_addrs[idx]
        ns = self._read(base + self.REG["TS_NS"])
        s = self._read(base + self.REG["TS_S"])
        self._write(base + self.REG["INT_CLEAR"], 1)
        return s, ns

    def run(self) -> None:
        self.setUp()
        counts = {i: self.getEventCount(i) if self.tsu_state[i] else 0 for i in self.pps_inputs}
        for i in self.pps_inputs:
            if self.tsu_state[i]:
                self.readTimestamp(i)
        s0 = None
        start = nextCycle = datetime.now()
        while not self.event.is_set():
            for i in self.pps_inputs:
                if self.tsu_state[i]:
                    has_ts = self.hasTimestamp(i)
                    if has_ts:
                        count = self.getEventCount(i)
                        if count - counts[i] > 1:
                            missed = count - counts[i] - 1
                        counts[i] = count
                        s, ns = self.readTimestamp(i)
                        if ns > 5e8:
                            s += 1
                            ns -= int(1e9)
                        if s0 is None:
                            s0 = s
                        self.send_metric(time.time_ns(), f"PPS_{i}", ns)
            nextCycle += timedelta(seconds=0.5)
            sleep = (nextCycle - datetime.now()).total_seconds()
            if sleep > 0:
                time.sleep(sleep)

    def stop(self) -> None:
        for i in self.enabled_tsus:
            self.setEnable(i, False)
        if self.uart:
            self.uart.close()
        super().stop()
