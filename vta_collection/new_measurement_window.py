from loguru import logger as log
from PySide6 import QtCore, QtWidgets

from vta_collection.calibration import Calibration
from vta_collection.config import config
from vta_collection.measurement import Measurement, Metadata
from vta_collection.ui.new_measurement import Ui_Dialog


class NewMeasurementWindow(QtWidgets.QDialog, Ui_Dialog):
    cal = Calibration()
    accepted = QtCore.Signal(Measurement)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.le_operator.setText(config.operator)
        self.cb_cal_enabled.checkStateChanged.connect(self.set_stuff_enabled)
        self.cb_cal_enabled.setChecked(config.calibration_enabled)
        self.le_c0.setText(str(config.c0))
        self.le_c1.setText(str(config.c1))
        self.le_c2.setText(str(config.c2))
        self.le_c3.setText(str(config.c3))

        self.le_c0.textChanged.connect(self.update_polynom)
        self.le_c1.textChanged.connect(self.update_polynom)
        self.le_c2.textChanged.connect(self.update_polynom)
        self.le_c3.textChanged.connect(self.update_polynom)
        self.update_polynom()

    def update_polynom(self):
        try:
            self.cal.c0 = float(self.le_c0.text())
            self.cal.c1 = float(self.le_c1.text())
            self.cal.c2 = float(self.le_c2.text())
            self.cal.c3 = float(self.le_c3.text())
        except Exception as e:
            log.warning(e)
        self.label_calibration.setText(self.cal.to_formule_str())

    def set_stuff_enabled(self):
        enabled = self.cb_cal_enabled.isChecked()
        self.le_c0.setEnabled(enabled)
        self.le_c1.setEnabled(enabled)
        self.le_c2.setEnabled(enabled)
        self.le_c3.setEnabled(enabled)

    def accept(self):
        if self.cb_cal_enabled.isChecked():
            cal = self.cal
            config.c0 = cal.c0
            config.c1 = cal.c1
            config.c2 = cal.c2
            config.c3 = cal.c3
        else:
            cal = None

        config.operator = self.le_operator.text()
        config.calibration_enabled = self.cb_cal_enabled.isChecked()
        config.update()
        meas = Measurement(
            metadata=Metadata(
                sample=self.le_sample.text(),
                operator=self.le_operator.text(),
            ),
            cal=cal,
        )
        log.debug(f"Created measurement: {meas.metadata}, {meas.cal}")
        self.accepted.emit(meas)

        self.close()
