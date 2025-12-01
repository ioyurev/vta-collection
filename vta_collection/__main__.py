import sys

# from loguru import logger as log
from PySide6 import QtWidgets

from vta_collection.heater.controller import HeaterController
from vta_collection.helpers import set_excepthook
from vta_collection.main_window import MainWindow
from vta_collection.measurement import Measurement
from vta_collection.new_measurement_window import NewMeasurementWindow
from vta_collection.ui import resources_rc  # noqa: F401


def close_splash():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        import pyi_splash  # type: ignore

        pyi_splash.close()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    set_excepthook()

    w = MainWindow()
    h = HeaterController(parent=app)

    def set_meas(meas: Measurement):
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
