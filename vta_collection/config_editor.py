from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

from PySide6.QtCore import QMetaObject
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from serial.tools.list_ports import comports

if TYPE_CHECKING:
    from vta_collection.config import Config


class ConfigEditor(QDialog):
    def __init__(
        self, config_instance: "Config", ignore_fields: list[str] = [], parent=None
    ):
        super().__init__(parent)
        self.config_instance = config_instance
        self.fields: Dict[
            str, ComPortPicker | QDoubleSpinBox | QLineEdit | QCheckBox | PathPicker
        ] = {}
        self.ignore_fields = ignore_fields
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Configuration")
        self.setMinimumWidth(400)

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Создаем поля для каждого атрибута модели
        for field_name, field_info in type(self.config_instance).model_fields.items():
            if field_name in self.ignore_fields:
                continue  # Пропускаем игнорируемые поля
            field_type = field_info.annotation
            default_value = getattr(self.config_instance, field_name)

            # Создаем соответствующий виджет
            widget = self.create_widget(field_name, field_type, default_value)
            if widget:
                self.fields[field_name] = widget
                form_layout.addRow(field_name, widget)

        # Добавляем кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

        QMetaObject.connectSlotsByName(self)
        self.accepted.connect(self.apply_config)

    def create_widget(self, field_name: str, field_type: type, default_value: Any):
        """Создает виджет в зависимости от типа поля и его имени"""
        # Специальная обработка для поля comport
        if field_name == "comport" and field_type is str:
            return ComPortPicker(default_value)

        if field_type is bool:
            checkbox = QCheckBox()
            checkbox.setChecked(default_value)
            return checkbox

        elif field_type in (int, float):
            spinbox = QSpinBox() if field_type is int else QDoubleSpinBox()
            spinbox.setMinimum(-1000000)
            spinbox.setMaximum(1000000)
            spinbox.setValue(default_value)
            return spinbox

        elif field_type is str:
            line_edit = QLineEdit(str(default_value))
            return line_edit

        elif field_type == Path:
            return PathPicker(str(default_value))

        return None

    def get_values(self) -> dict:
        """Собирает значения из виджетов в словарь"""
        result = {}
        for field_name, widget in self.fields.items():
            field_info = type(self.config_instance).model_fields[field_name]
            field_type = field_info.annotation

            if isinstance(widget, (ComPortPicker, PathPicker)):
                result[field_name] = widget.value()
            elif field_type is bool:
                result[field_name] = widget.isChecked()
            elif field_type in (int, float):
                result[field_name] = widget.value()
            elif field_type is str:
                result[field_name] = widget.text()

        return result

    def apply_config(self):
        new_values = self.get_values()
        for key, value in new_values.items():
            setattr(self.config_instance, key, value)
        self.config_instance.update()


class ComPortPicker(QWidget):
    """Кастомный виджет для выбора COM-порта"""

    def __init__(self, default_port: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.combo = QComboBox()
        layout.addWidget(self.combo, 1)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh_ports)
        layout.addWidget(self.btn_refresh)

        self.refresh_ports()
        self.set_current_port(default_port)

    def refresh_ports(self):
        """Обновляет список доступных COM-портов"""
        current = self.combo.currentText()
        self.combo.clear()

        ports = [port.device for port in comports()]
        self.combo.addItems(ports)

        # Восстанавливаем предыдущий выбор, если он доступен
        if current in ports:
            self.combo.setCurrentText(current)

    def set_current_port(self, port: str):
        """Устанавливает текущий порт, если он доступен"""
        if port and port in [self.combo.itemText(i) for i in range(self.combo.count())]:
            self.combo.setCurrentText(port)

    def value(self) -> str:
        """Возвращает выбранный COM-порт"""
        return self.combo.currentText()


class PathPicker(QWidget):
    """Кастомный виджет для выбора пути (файла или директории)"""

    def __init__(
        self,
        default_path: str = "",
        file_mode: bool = False,
        file_filter: str = "All Files (*)",
        parent=None,
    ):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        layout.addWidget(self.line_edit, 1)

        self.btn_browse = QPushButton("Browse")
        self.btn_browse.clicked.connect(self.browse)
        layout.addWidget(self.btn_browse)

        self.file_mode = file_mode
        self.file_filter = file_filter

        if default_path:
            self.set_path(default_path)

    def browse(self):
        """Открывает диалоговое окно выбора пути"""
        if self.file_mode:
            path, _ = QFileDialog.getOpenFileName(
                self, "Select File", self.line_edit.text(), self.file_filter
            )
        else:
            path = QFileDialog.getExistingDirectory(
                self, "Select Directory", self.line_edit.text()
            )

        if path:
            self.set_path(path)

    def set_path(self, path: str):
        """Устанавливает путь в виджет"""
        self.line_edit.setText(path)

    def value(self) -> str:
        """Возвращает выбранный путь"""
        return self.line_edit.text()


# Пример использования
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    from vta_collection.config import config  # Импортируем вашу модель Config

    app = QApplication([])

    # Создаем и показываем редактор
    editor = ConfigEditor(config_instance=config)
    editor.exec()
