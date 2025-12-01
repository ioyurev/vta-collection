import sys

# from loguru import logger as log
from PySide6 import QtWidgets

from vta_collection.config import config
from vta_collection.hardware import get_hardware
from vta_collection.heater.controller import HeaterController
from vta_collection.helpers import set_excepthook
from vta_collection.main_window import MainWindow
from vta_collection.measurement import Measurement
from vta_collection.new_measurement_window import NewMeasurementWindow
from vta_collection.serial_base import get_serial_ports

# from vta_collection.serial_base import get_serial_ports
from vta_collection.ui import resources_rc  # noqa: F401

# def find_adam(ports: list[str], device: Adam4520):
#     if not device.found:
#         log.debug("Trying to find ADAM")
#         found = False
#         for port in ports:
#             found = device.find_on_port(port=port)
#             if found:
#                 break
#         if not found:
#             raise Exception(f"{device.modelname} not found")
#         device.modules_check_identity()


def close_splash():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        import pyi_splash  # type: ignore

        pyi_splash.close()


def validate_com_port():
    ports = get_serial_ports()
    if config.comport not in ports:
        raise Exception(
            f"COM port '{config.comport}' is not available. Available ports: {ports}"
        )


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    set_excepthook()

    w = MainWindow()
    adam4520 = get_hardware().adam4520
    h = HeaterController(parent=app)

    def set_meas(meas: Measurement):
        if not config.is_test_mode:
            if not adam4520.found:
                validate_com_port()
                adam4520.find_on_port(port=config.comport)
            # find_adam(ports=get_serial_ports()[::-1], device=adam4520)
        w.new_meas()
        w.set_meas(meas=meas)
        h.set_meas(meas=meas)
        h.start_loop()

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
    close_splash()
    app.aboutToQuit.connect(h.stop_loop)
    sys.exit(app.exec())
