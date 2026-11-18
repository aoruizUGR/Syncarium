"""Frequency counter data source."""

import multiprocessing as mp
import signal
import time
import pyvisa as visa

from multiprocessing.synchronize import Event as _EventType
from pyvisa.resources import MessageBasedResource

from .datasource import DataSource


class CounterDataSource(DataSource):

    def __init__(self, queue: mp.Queue, event: _EventType, resource_name: str) -> None:
        super().__init__(queue, event)
        self.resource_name = resource_name


    def run(self) -> None:
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        rm = visa.ResourceManager()
        instr = rm.open_resource(self.resource_name)

        if isinstance(instr, MessageBasedResource):
            instr.read_termination = "\n"
            instr.write_termination = "\n"
            instr.timeout = 10 * 1e3

            instr.write("*RST")
            instr.write("SYST:TIM 2.0E0")
            instr.write("CONF:TINT (@1),(@2)")
            instr.write("INP1:COUP DC; IMP 50; RANG 5; LEV 2.0; SLOP NEG")
            instr.write("INP2:COUP DC; IMP 50; RANG 5; LEV 1.5; SLOP POS")

            while not self.event.is_set():
                instr.query("*OPC?")
                value = instr.query("READ?")
                timestamp = time.time_ns()
                self._send_metric(timestamp, "offset_hw", value)
        else:
            raise ValueError("Instrument is not a message-based resource")

