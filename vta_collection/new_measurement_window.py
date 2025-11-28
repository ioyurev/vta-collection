from loguru import logger as log
from PySide6 import QtCore, QtWidgets

from vta_collection.calibration import Calibration
from vta_collection.calibration_manager import get_calibration_manager
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
        self.cb_cal_enabled.setChecked(config.calibration_enabled)

        # Заполняем комбобокс доступными калибровками
        self.cb_calibration_select.currentTextChanged.connect(
            self.on_calibration_selected
        )
        self.refresh_calibrations_list()

    def refresh_calibrations_list(self):
        """Обновить список доступных калибровок в комбобоксе"""
        self.cb_calibration_select.clear()
        calibration_manager = get_calibration_manager()
        calibration_names = calibration_manager.get_calibration_names()
        self.cb_calibration_select.addItems(calibration_names)
        # Выбираем активную калибровку, если она есть и доступна
        if calibration_manager.active_calibration_name:
            index = self.cb_calibration_select.findText(
                calibration_manager.active_calibration_name
            )
            if index >= 0:
                self.cb_calibration_select.setCurrentIndex(index)
            else:
                # Если активная калибровка недоступна, сбрасываем её
                calibration_manager.active_calibration = None
                calibration_manager.active_calibration_name = None

    def on_calibration_selected(self, name):
        """Обработка выбора калибровки из списка"""
        if name:
            calibration_manager = get_calibration_manager()
            calibration = calibration_manager.load_calibration(name)
            if calibration:
                self.cal = calibration
                self.update_polynom()
                # Обновляем статус калибровки
                self.update_calibration_status("valid")
            else:
                # Калибровка недоступна
                self.cal = Calibration()  # Сброс к стандартной калибровке
                self.update_polynom()
                self.update_calibration_status("invalid")
        else:
            # Нет выбранной калибровки
            self.update_calibration_status("none")

    def update_calibration_status(self, status: str):
        """Обновить визуальный статус калибровки"""
        palette = self.label_calibration.palette()
        if status == "valid":
            # Зеленый цвет для валидной калибровки
            palette.setColor(
                self.label_calibration.foregroundRole(), QtCore.Qt.GlobalColor.green
            )
        elif status == "invalid":
            # Красный цвет для невалидной калибровки
            palette.setColor(
                self.label_calibration.foregroundRole(), QtCore.Qt.GlobalColor.red
            )
        else:
            # Стандартный цвет
            palette.setColor(
                self.label_calibration.foregroundRole(),
                self.label_calibration.palette().color(
                    self.label_calibration.foregroundRole()
                ),
            )
        self.label_calibration.setPalette(palette)

    def update_polynom(self):
        # Обновляем отображение формулы выбранной калибровки
        self.label_calibration.setText(self.cal.to_formule_str())

    def accept(self):
        if self.cb_cal_enabled.isChecked():
            # Используем выбранную калибровку из комбобокса
            selected_calibration_name = self.cb_calibration_select.currentText()
            if selected_calibration_name:
                # Загружаем выбранную калибровку
                calibration_manager = get_calibration_manager()
                cal = calibration_manager.load_calibration(selected_calibration_name)
            else:
                # Если калибровка не выбрана, используем None
                cal = None
        else:
            cal = None

        config.operator = self.le_operator.text()
        config.calibration_enabled = self.cb_cal_enabled.isChecked()
        config.update()
        meas = Measurement(
            metadata=Metadata(
                sample=self.le_sample.text(),
                operator=self.le_operator.text(),
                calibration_id=cal.name
                if cal is not None and cal.name is not None
                else None,
            ),
            cal=cal,
        )
        log.debug(f"Created measurement: {meas.metadata}, {meas.cal}")
        self.accepted.emit(meas)

        self.close()
