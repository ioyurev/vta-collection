import math
import time
import warnings

from loguru import logger as log
from PySide6 import QtCore

from vta_collection.adam_4011 import Adam4011
from vta_collection.adam_4021 import Adam4021
from vta_collection.config import config
from vta_collection.measurement import DataPoint, Measurement

TEST_INTERVAL = 0.1


class Heater(QtCore.QThread):
    _is_running = False
    data_ready = QtCore.Signal(DataPoint)
    start_time = 0.0
    error_occured = QtCore.Signal(Exception)
    output = 0.0
    speed = config.default_speed
    heat_enabled = False
    t0 = 0.0
    meas: Measurement | None = None
    recording_enabled = False

    def __init__(self, adam4011: Adam4011, adam4021: Adam4021, parent=None):
        super().__init__(parent)
        self.adam4011 = adam4011
        self.adam4021 = adam4021
        self.error_occured.connect(log.error)

    def reset_meas(self):
        if hasattr(self, "meas") and self.meas:
            self.meas.reset()
            del self.meas

    def set_meas(self, meas: Measurement):
        self.reset_meas()
        self.meas = meas
        with warnings.catch_warnings(action="ignore"):
            self.data_ready.disconnect()
        self.data_ready.connect(meas.make_data_connection())
        log.debug("Recording connection defined")

    def start(self):
        if not config.is_test_mode:
            if not self.adam4011.converter.found:
                log.error("Heater can't be started")
                return
        log.debug("Starting heater thread")
        return super().start()

    def run(self):
        self._run_body()

    def stop_thread(self):
        self.reset_meas()
        self.stop_heating()
        log.debug("Stopping heater thread")
        self._is_running = False
        self.exit()
        self.wait()

    def stop_heating(self):
        if hasattr(self, "meas") and self.meas:
            self.meas.set_recording_enabled(enabled=False)
            self.reset_heating()
        self.heat_enabled = False
        log.debug("Heating stoped")

    def start_heating(self):
        self.set_start_time()
        self.meas.set_recording_enabled(enabled=True)
        self.heat_enabled = True
        log.debug("Heating started")

    def reset_heating(self):
        log.debug("Heating reset")
        self.output = 0.0

    def set_speed(self, value: int):
        self.speed = value / 1000
        log.debug(f"Heat speed changed to {value}")

    def set_start_time(self):
        self.start_time = time.monotonic()
        self.t0 = 0.0

    def get_loop_time(self):
        return time.monotonic() - self.start_time

    def _run_body(self):
        self._is_running = True
        if config.is_test_mode:
            self._get_data = self._test_get_data
            self._set_output = self._test_set_output
            self._loopcallback = self._test_loopcallback
        while self._is_running:
            try:
                self._loopcallback()
            except Exception as e:
                self.error_occured.emit(Exception(f"LoopError: {e}"))

    def _get_data(self):
        return self.adam4011.get_data()

    def _heatup(self, t: float):
        if self.heat_enabled:
            self.output += self.speed * (t - self.t0)
            self.t0 = t
            self._set_output(value=self.output)

    def _set_output(self, value: float):
        self.adam4021.set_output(value=value)

    def _loop_body(self):
        emf = self._get_data()
        t1 = self.get_loop_time()
        self._heatup(t=t1)
        t2 = self.get_loop_time()
        self.data_ready.emit(DataPoint(t1=t1, emf=emf, t2=t2, output=self.output))

    def _loopcallback(self):
        self._loop_body()

    def _test_get_data(self):
        return math.sin(time.monotonic())

    def _test_set_output(self, value):
        pass

    def _test_loopcallback(self):
        time.sleep(TEST_INTERVAL)
        self._loop_body()
