import json

from loguru import logger as log
from PySide6 import QtWidgets

from vta_collection.calibration import Calibration
from vta_collection.calibration_editor_window import CalibrationEditorWindow
from vta_collection.calibration_manager import get_calibration_manager
from vta_collection.ui.calibration_manager_dialog import Ui_Dialog


class CalibrationManagerWindow(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        # Подключаем сигналы
        self.btn_refresh.clicked.connect(self.refresh_calibrations)
        self.btn_delete.clicked.connect(self.delete_calibration)
        self.btn_edit.clicked.connect(self.edit_calibration)
        self.btn_new.clicked.connect(self.new_calibration)
        self.btn_import.clicked.connect(self.import_calibration)
        self.btn_export.clicked.connect(self.export_calibration)

        # Загружаем список калибровок
        self.refresh_calibrations()
        log.debug("Создано окно управления калибровками")

    def refresh_calibrations(self):
        """Обновить список калибровок"""
        self.list_calibrations.clear()
        calibration_names = get_calibration_manager().get_calibration_names()
        self.list_calibrations.addItems(calibration_names)

    def edit_calibration(self):
        """Редактировать выбранную калибровку"""
        selected_items = self.list_calibrations.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(
                self, "Warning", "Please select a calibration to edit."
            )
            return

        name = selected_items[0].text()
        log.debug(f"Редактирование калибровки: {name}")
        # Загружаем калибровку из файла
        calibration = get_calibration_manager().load_calibration(name)
        # Открываем CalibrationEditorWindow для редактирования существующей калибровки
        editor = CalibrationEditorWindow(parent=self)
        editor.set_calibration(calibration)
        editor.calibration_edited.connect(self.on_calibration_edited)
        editor.exec()

    def on_calibration_edited(self, calibration: Calibration):
        """Обработка редактирования калибровки"""
        name = calibration.name or ""
        if not name:
            QtWidgets.QMessageBox.warning(
                self, "Warning", "Calibration name is required."
            )
            return

        # Сохраняем калибровку в файл
        get_calibration_manager().save_calibration(calibration)
        QtWidgets.QMessageBox.information(
            self, "Success", f"Calibration '{name}' updated successfully."
        )
        # Перезагружаем список калибровок, чтобы обновить кэш
        self.refresh_calibrations()

    def new_calibration(self):
        """Создать новую калибровку"""
        # Открываем CalibrationEditorWindow для создания новой калибровки
        editor = CalibrationEditorWindow(parent=self)
        editor.calibration_created.connect(self.on_calibration_created)
        editor.exec()

    def on_calibration_created(self, calibration: Calibration):
        """Обработка создания новой калибровки"""
        name = calibration.name or ""
        if not name:
            QtWidgets.QMessageBox.warning(
                self, "Warning", "Calibration name is required."
            )
            return

        get_calibration_manager().save_calibration(calibration)
        QtWidgets.QMessageBox.information(
            self, "Success", f"Calibration '{name}' created successfully."
        )
        self.refresh_calibrations()

    def delete_calibration(self):
        """Удалить выбранную калибровку"""
        selected_items = self.list_calibrations.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(
                self, "Warning", "Please select a calibration to delete."
            )
            return

        name = selected_items[0].text()
        log.debug(f"Удаление калибровки: {name}")
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm",
            f"Are you sure you want to delete calibration '{name}'?",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            get_calibration_manager().delete_calibration(name)
            QtWidgets.QMessageBox.information(
                self, "Success", f"Calibration '{name}' deleted successfully."
            )
            self.refresh_calibrations()

    def import_calibration(self):
        """Импорт калибровки из файла"""
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import Calibration", "", "Calibration Files (*.json);;All Files (*)"
        )

        if not filename:
            return

        try:
            # Загружаем JSON данные из файла
            with open(filename, "r", encoding="utf-8") as f:
                cal_data = json.load(f)

            # Создаем калибровку из данных
            calibration = Calibration.from_dict(cal_data)

            # Проверяем, что калибровка имеет имя
            if not calibration.name:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Calibration file does not contain a valid name."
                )
                return

            # Проверяем, существует ли уже калибровка с таким именем
            calibration_manager = get_calibration_manager()
            if calibration.name in calibration_manager.calibrations:
                reply = QtWidgets.QMessageBox.question(
                    self,
                    "Confirm",
                    f"Calibration '{calibration.name}' already exists. Overwrite?",
                    QtWidgets.QMessageBox.StandardButton.Yes
                    | QtWidgets.QMessageBox.StandardButton.No,
                )
                if reply == QtWidgets.QMessageBox.StandardButton.No:
                    return

            # Сохраняем калибровку
            calibration_manager.save_calibration(calibration)
            QtWidgets.QMessageBox.information(
                self,
                "Success",
                f"Calibration '{calibration.name}' imported successfully.",
            )
            self.refresh_calibrations()

        except json.JSONDecodeError:
            QtWidgets.QMessageBox.critical(
                self, "Error", "Invalid JSON format in calibration file."
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to import calibration: {str(e)}"
            )

    def export_calibration(self):
        """Экспорт калибровки в файл"""
        selected_items = self.list_calibrations.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(
                self, "Warning", "Please select a calibration to export."
            )
            return

        name = selected_items[0].text()

        # Загружаем выбранную калибровку
        calibration_manager = get_calibration_manager()
        calibration = calibration_manager.load_calibration(name)

        if not calibration:
            QtWidgets.QMessageBox.warning(
                self, "Warning", f"Could not load calibration '{name}'."
            )
            return

        # Открываем диалог сохранения файла
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Calibration",
            f"{calibration.name}.json",
            "Calibration Files (*.json);;All Files (*)",
        )

        if not filename:
            return

        try:
            # Сохраняем калибровку в файл
            with open(filename, "w", encoding="utf-8") as f:
                # Используем метод to_file из класса Calibration
                calibration.to_file(f)

            QtWidgets.QMessageBox.information(
                self,
                "Success",
                f"Calibration '{calibration.name}' exported successfully.",
            )

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to export calibration: {str(e)}"
            )
