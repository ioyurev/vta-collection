from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

from PySide6.QtCore import QMetaObject
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from vta_collection.config import Config


class ConfigEditor(QDialog):
    def __init__(
        self, config_instance: "Config", ignore_fields: list[str] = [], parent=None
    ):
        super().__init__(parent)
        self.config_instance = config_instance
        self.fields: Dict[str, Any] = {}
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
            widget = self.create_widget(field_type, default_value)
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

    def create_widget(self, field_type: type, default_value: Any):
        """Создает виджет в зависимости от типа поля"""
        if field_type == bool:
            checkbox = QCheckBox()
            checkbox.setChecked(default_value)
            return checkbox

        elif field_type in (int, float):
            spinbox = QSpinBox() if field_type == int else QDoubleSpinBox()
            # spinbox.setDecimals(2 if field_type == float else 0)
            spinbox.setMinimum(-1000000)
            spinbox.setMaximum(1000000)
            spinbox.setValue(default_value)
            return spinbox

        elif field_type == str:
            line_edit = QLineEdit(str(default_value))
            return line_edit

        elif field_type == Path:
            layout = QVBoxLayout()
            line_edit = QLineEdit(str(default_value))
            line_edit.setReadOnly(True)
            btn = QPushButton("Select directory")

            def select_folder():
                path = QFileDialog.getExistingDirectory(self, "Select directory")
                if path:
                    line_edit.setText(path)

            btn.clicked.connect(select_folder)
            layout.addWidget(line_edit)
            layout.addWidget(btn)
            return layout

        return None

    def get_values(self) -> dict:
        """Собирает значения из виджетов в словарь"""
        result = {}
        for field_name, widget in self.fields.items():
            field_info = type(self.config_instance).model_fields[field_name]
            field_type = field_info.annotation

            if field_type == bool:
                result[field_name] = widget.isChecked()

            elif field_type in (int, float):
                result[field_name] = widget.value()

            elif field_type == str:
                result[field_name] = widget.text()

            elif field_type == Path:
                # Для Path берем значение из QLineEdit
                result[field_name] = Path(widget.itemAt(0).widget().text())

        return result

    def apply_config(self):
        new_values = self.get_values()
        for key, value in new_values.items():
            setattr(self.config_instance, key, value)
        self.config_instance.update()


# Пример использования
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    from vta_collection.config import config  # Импортируем вашу модель Config

    app = QApplication([])

    # Создаем и показываем редактор
    editor = ConfigEditor(config_instance=config)
    editor.exec()
