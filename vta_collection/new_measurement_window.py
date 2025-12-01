from loguru import logger as log
from PySide6 import QtCore, QtWidgets

from vta_collection.calibration import Calibration, ZeroCalibration
from vta_collection.calibration_manager import get_calibration_manager
from vta_collection.config import config
from vta_collection.measurement import Measurement, Metadata
from vta_collection.ui.new_measurement_dialog import Ui_Dialog


class NewMeasurementWindow(QtWidgets.QDialog, Ui_Dialog):
    cal: Calibration
    accepted = QtCore.Signal(Measurement)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.le_operator.setText(config.operator)
        self.cb_cal_enabled.setChecked(config.calibration_enabled)

        # Заполняем комбобокс доступными калибровками
        self.refresh_calibrations_list()

    def refresh_calibrations_list(self):
        """Обновить список доступных калибровок в комбобоксе"""
        self.cb_calibration_select.clear()
        calibration_manager = get_calibration_manager()
        calibration_names = calibration_manager.get_calibration_names()
        self.cb_calibration_select.addItems(calibration_names)

        # Выбираем последнюю использованную калибровку из config
        if config.last_selected_calibration:
            index = self.cb_calibration_select.findText(
                config.last_selected_calibration
            )
            if index >= 0:
                self.cb_calibration_select.setCurrentIndex(index)

    def accept(self):
        if self.cb_cal_enabled.isChecked():
            # Используем выбранную калибровку из комбобокса
            selected_calibration_name = self.cb_calibration_select.currentText()
            if selected_calibration_name:
                # Загружаем выбранную калибровку
                calibration_manager = get_calibration_manager()
                cal = calibration_manager.load_calibration(selected_calibration_name)
            else:
                # Если калибровка не выбрана, используем ZeroCalibration
                cal = ZeroCalibration()
        else:
            # Когда калибровка отключена, используем ZeroCalibration
            cal = ZeroCalibration()

        config.operator = self.le_operator.text()
        config.calibration_enabled = self.cb_cal_enabled.isChecked()
        if self.cb_cal_enabled.isChecked():
            config.last_selected_calibration = self.cb_calibration_select.currentText()
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
