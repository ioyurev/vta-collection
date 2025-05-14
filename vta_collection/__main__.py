import sys

from loguru import logger as log
from PySide6 import QtWidgets

from vta_collection.adam_4011 import Adam4011
from vta_collection.adam_4021 import Adam4021
from vta_collection.adam_4520 import Adam4520
from vta_collection.config import config
from vta_collection.heater import Heater
from vta_collection.helpers import set_excepthook
from vta_collection.main_window import MainWindow
from vta_collection.measurement import Measurement
from vta_collection.new_measurement_window import NewMeasurementWindow
from vta_collection.serial_base import get_serial_ports
from vta_collection.ui import resources_rc  # noqa: F401


def find_adam(ports: list[str], device: Adam4520):
    if not device.found:
        log.debug("Trying to find ADAM")
        found = False
        for port in ports:
            found = device.find_on_port(port=port)
            if found:
                break
        if not found:
            raise Exception(f"{device.modelname} not found")
        device.modules_check_identity()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    set_excepthook()

    w = MainWindow()

    adam4520 = Adam4520()
    adam4011 = Adam4011(converter=adam4520, address=config.adam4011_address)
    adam4021 = Adam4021(converter=adam4520, address=config.adam4021_address)
    adam4520.modules = (adam4011, adam4021)

    h = Heater(adam4011=adam4011, adam4021=adam4021, parent=app)

    def set_meas(meas: Measurement):
        if not config.is_test_mode:
            find_adam(ports=get_serial_ports()[::-1], device=adam4520)
        w.new_meas()
        w.set_meas(meas=meas)
        h.set_meas(meas=meas)
        if not h._is_running:
            h.start()

    def new_meas():
        nmw = NewMeasurementWindow(parent=w)
        nmw.accepted.connect(set_meas)
        nmw.show()

    w.action_new.triggered.connect(new_meas)
    w.btn_start.clicked.connect(h.start_heating)
    w.btn_stop.clicked.connect(h.stop_heating)
    w.btn_stop_heat.clicked.connect(h.reset_heating)
    w.sb_speed.valueChanged.connect(h.set_speed)

    w.show()
    app.aboutToQuit.connect(h.stop_thread)
    sys.exit(app.exec())
