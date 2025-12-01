import warnings
from typing import Optional

from loguru import logger as log
from PySide6 import QtCore

from vta_collection.config import config
from vta_collection.hardware import get_hardware
from vta_collection.heater.loop import RealLoop, TestLoop
from vta_collection.measurement import DataPoint, Measurement


class HeaterController(QtCore.QObject):
    data_ready = QtCore.Signal(DataPoint)
    meas: Optional[Measurement] = None

    def __init__(self, parent=None):
        super().__init__(parent)
        hardware = get_hardware()
        self.adam4011 = hardware.adam4011
        self.adam4021 = hardware.adam4021
        if config.is_test_mode:
            self.loop = TestLoop()
        else:
            self.loop = RealLoop(self)
        self.loop.data_ready.connect(self.data_ready.emit)
        self.loop.error_occurred.connect(log.error)

    def set_meas(self, meas: Measurement):
        if self.meas:
            del self.meas
        self.meas = meas

    def set_meas_connection(self, enabled):
        if self.meas is None:
            return
        if enabled:
            self.data_ready.connect(self.meas.make_data_connection())
            self.meas.recording_enabled = True
        else:
            self.meas.recording_enabled = False
            with warnings.catch_warnings(action="ignore"):
                self.data_ready.disconnect()

    def start_loop(self):
        log.debug("Starting loop thread")
        self.loop.start_thread()
        self.loop.set_enabled(True)
        self.set_meas_connection(True)

    def stop_loop(self):
        log.debug("Stopping loop thread")
        self.set_meas_connection(False)
        self.loop.set_enabled(False)
        self.loop.set_output(0.0)
        self.loop.stop_thread()

    def start_heating(self):
        if self.meas:
            self.meas.clear()
        self.loop.heater.set_enabled(True)
        log.debug("Heating started")

    def stop_heating(self):
        self.reset_heating()
        if self.meas:
            self.meas.snapshot_emf()
        self.loop.heater.set_enabled(False)
        log.debug("Heating stopped")

    def reset_heating(self):
        log.debug("Heating reset")
        self.loop.heater.reset()

    def set_speed(self, value: int):
        self.loop.heater.set_speed(value=value)
        log.debug(f"Heat speed changed to {value}")
