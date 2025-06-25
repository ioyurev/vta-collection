import math
import time
from abc import abstractmethod
from typing import TYPE_CHECKING

from PySide6 import QtCore

from vta_collection.heater.heater import Heater
from vta_collection.measurement import DataPoint

TEST_INTERVAL = 0.1

if TYPE_CHECKING:
    from vta_collection.heater.controller import HeaterController


class LoopException(Exception):
    pass


class OutputException(Exception):
    pass


class AbstractLoop(QtCore.QThread):
    error_occurred = QtCore.Signal(Exception)
    data_ready = QtCore.Signal(DataPoint)

    def __init__(self):
        super().__init__()
        self.heater = Heater(self)
        self.thread_is_running = False
        self.enabled = False

    def start_thread(self):
        if not self.isRunning():
            super().start()

    def run(self):
        self.thread_is_running = True
        while self.thread_is_running:
            if self.enabled:
                try:
                    self.loop_body()
                except Exception as e:
                    self.error_occurred.emit(LoopException(e))

    def stop_thread(self):
        self.set_enabled(False)
        self.thread_is_running = False
        self.exit()
        self.wait()

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def loop_body(self):
        emf = self.get_data()
        t1 = time.monotonic()
        self.heater.heatup(last_t=t1)
        t2 = time.monotonic()
        data = DataPoint(
            t1=round(t1, 3),
            emf=emf,
            t2=round(t2, 3),
            output=round(self.heater.output, 3),
        )
        self.data_ready.emit(data)

    @abstractmethod
    def get_data(self):
        raise NotImplementedError

    @abstractmethod
    def set_output(self, value: float):
        raise NotImplementedError


class RealLoop(AbstractLoop):
    controller: "HeaterController"

    def __init__(self, controller: "HeaterController"):
        super().__init__()
        self.controller = controller

    def get_data(self):
        return self.controller.adam4011.get_data()

    def set_output(self, value: float):
        try:
            self.controller.adam4021.set_output(value=value)
        except Exception as e:
            self.error_occurred.emit(OutputException(e))


class TestLoop(AbstractLoop):
    def get_data(self):
        return math.sin(time.monotonic())

    def set_output(self, value: float):
        pass

    def loop_body(self):
        time.sleep(TEST_INTERVAL)
        super().loop_body()
