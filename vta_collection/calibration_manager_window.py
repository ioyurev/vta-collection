from PySide6 import QtCore, QtWidgets

from vta_collection.calibration import Calibration
from vta_collection.calibration_manager import get_calibration_manager
from vta_collection.ui.calibration_manager_dialog import Ui_Dialog


class CalibrationManagerWindow(QtWidgets.QDialog, Ui_Dialog):
    # Сигнал для уведомления главного окна об изменении калибровок
    calibration_changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        # Подключаем сигналы
        self.btn_refresh.clicked.connect(self.refresh_calibrations)
        self.btn_delete.clicked.connect(self.delete_calibration)
        self.btn_save.clicked.connect(self.save_calibration)
        self.btn_new.clicked.connect(self.new_calibration)
        self.btn_import.clicked.connect(self.import_calibration)
        self.btn_export.clicked.connect(self.export_calibration)
        self.list_calibrations.itemSelectionChanged.connect(
            self.on_calibration_selected
        )

        # Загружаем список калибровок
        self.refresh_calibrations()

    def refresh_calibrations(self):
        """Обновить список калибровок"""
        self.list_calibrations.clear()
        calibration_manager = get_calibration_manager()
        calibration_names = calibration_manager.get_calibration_names()
        self.list_calibrations.addItems(calibration_names)

    def on_calibration_selected(self):
        """Обработка выбора калибровки из списка"""
        selected_items = self.list_calibrations.selectedItems()
        if selected_items:
            name = selected_items[0].text()
            # Загружаем калибровку из кэша и отображаем её данные
            calibration_manager = get_calibration_manager()
            calibration = calibration_manager.get_cached_calibration(name)
            if calibration:
                self.le_name.setText(calibration.name or "")
                self.le_description.setText(calibration.description)
                self.le_c0.setText(str(calibration.c0))
                self.le_c1.setText(str(calibration.c1))
                self.le_c2.setText(str(calibration.c2))
                self.le_c3.setText(str(calibration.c3))

    def save_calibration(self):
        """Сохранить калибровку"""
        name = self.le_name.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(
                self, "Warning", "Please enter a name for the calibration."
            )
            return

        try:
            c0 = float(self.le_c0.text())
            c1 = float(self.le_c1.text())
            c2 = float(self.le_c2.text())
            c3 = float(self.le_c3.text())
        except ValueError:
            QtWidgets.QMessageBox.warning(
                self, "Warning", "Please enter valid numbers for all coefficients."
            )
            return

        description = self.le_description.text()

        calibration = Calibration(
            c0=c0, c1=c1, c2=c2, c3=c3, name=name, description=description
        )

        try:
            calibration_manager = get_calibration_manager()
            calibration_manager.save_calibration(name, calibration, description)
            QtWidgets.QMessageBox.information(
                self, "Success", f"Calibration '{name}' saved successfully."
            )
            self.refresh_calibrations()
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to save calibration: {str(e)}"
            )

    def new_calibration(self):
        """Создать новую калибровку"""
        self.le_name.setText("")
        self.le_description.setText("")
        self.le_c0.setText("0.0")
        self.le_c1.setText("0.0")
        self.le_c2.setText("0.0")
        self.le_c3.setText("0.0")
        self.list_calibrations.clearSelection()

    def delete_calibration(self):
        """Удалить выбранную калибровку"""
        selected_items = self.list_calibrations.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(
                self, "Warning", "Please select a calibration to delete."
            )
            return

        name = selected_items[0].text()
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm",
            f"Are you sure you want to delete calibration '{name}'?",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                calibration_manager = get_calibration_manager()
                calibration_manager.delete_calibration(name)
                QtWidgets.QMessageBox.information(
                    self, "Success", f"Calibration '{name}' deleted successfully."
                )
                self.refresh_calibrations()
                self.new_calibration()  # Очищаем поля после удаления
                # Отправляем сигнал об изменении калибровок
                self.calibration_changed.emit()
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Error", f"Failed to delete calibration: {str(e)}"
                )

    def import_calibration(self):
        """Импорт калибровки из файла"""
        # Временно: просто показываем сообщение, в будущем можно реализовать полноценный импорт
        QtWidgets.QMessageBox.information(
            self, "Info", "Import functionality not yet implemented."
        )

    def export_calibration(self):
        """Экспорт калибровки в файл"""
        selected_items = self.list_calibrations.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(
                self, "Warning", "Please select a calibration to export."
            )
            return

        # Временно: просто показываем сообщение, в будущем можно реализовать полноценный экспорт
        name = selected_items[0].text()
        QtWidgets.QMessageBox.information(
            self, "Info", f"Export functionality for '{name}' not yet implemented."
        )
