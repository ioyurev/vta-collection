from typing import Optional

import numpy as np
import pyqtgraph as pg
from loguru import logger as log
from numpy.polynomial.polynomial import polyval
from PySide6 import QtCore, QtWidgets

from vta_collection.calibration import Calibration
from vta_collection.standard import Standard
from vta_collection.ui.calibration_editor_dialog import Ui_Dialog


class CalibrationEditorWindow(QtWidgets.QDialog, Ui_Dialog):
    """Окно редактирования стандартов калибровки"""

    # Сигналы для уведомления о создании/редактировании калибровки
    calibration_created = QtCore.Signal(Calibration)
    calibration_edited = QtCore.Signal(Calibration)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        # Инициализируем переменные
        self.calibration: Optional[Calibration] = None
        self.edit_mode = False  # Флаг режима редактирования
        log.debug("Создано окно редактора калибровки")

        # Подключаем сигналы
        self.btn_add_standard.clicked.connect(self.add_standard)
        self.btn_remove_standard.clicked.connect(self.remove_standard)
        self.btn_create.clicked.connect(self.create_calibration)
        self.btn_close.clicked.connect(self.reject)
        self.cb_calibration_type.currentTextChanged.connect(self.update_formula)
        self.cb_calibration_type.currentTextChanged.connect(self.update_plot)
        self.table_standards.itemChanged.connect(self.update_plot)

        # Инициализируем график
        self.init_plot()

        # Инициализируем таблицу
        self.table_standards.setColumnCount(3)
        self.table_standards.setHorizontalHeaderLabels(
            ["Name", "T theoretical", "T experimental"]
        )
        self.table_standards.horizontalHeader().setStretchLastSection(True)

        # Текущая калибровка
        self.calibration: Optional[Calibration] = None

    def set_calibration(self, calibration: Calibration):
        """Установить калибровку для редактирования"""
        self.calibration = calibration
        self.edit_mode = calibration is not None  # Устанавливаем флаг режима

        log.debug(
            f"Установка калибровки в редактор: {'редактирование' if self.edit_mode else 'создание'}, имя: {calibration.name if calibration else 'None'}, стандарты: {calibration.standards if calibration else []}"
        )

        # Устанавливаем заголовок окна в зависимости от режима
        if calibration:
            self.setWindowTitle("Edit Calibration")
        else:
            self.setWindowTitle("Create Calibration")

        if calibration:
            # Заполняем основные поля существующей калибровки
            if calibration.name:
                self.le_name.setText(calibration.name)
            self.cb_calibration_type.setCurrentText(calibration.calibration_type)
            if calibration.description:
                self.le_description.setText(calibration.description)

            # Заполняем таблицу стандартами
            self.table_standards.setRowCount(0)
            for standard in calibration.standards:
                self._add_row_to_table(standard)
        else:
            # Очищаем поля для новой калибровки
            self.le_name.setText("")
            self.cb_calibration_type.setCurrentText("linear")
            self.le_description.setText("")
            self.table_standards.setRowCount(0)

        # Обновляем формулу и график
        self.update_formula()
        self.update_plot()

    def _add_row_to_table(self, standard: Standard):
        """Добавить строку в таблицу"""
        row = self.table_standards.rowCount()
        self.table_standards.insertRow(row)

        # Name
        item_name = QtWidgets.QTableWidgetItem(standard.name)
        self.table_standards.setItem(row, 0, item_name)

        # T theoretical
        item_t_theor = QtWidgets.QTableWidgetItem(str(standard.t_theor))
        self.table_standards.setItem(row, 1, item_t_theor)

        # T experimental
        item_t_exp = QtWidgets.QTableWidgetItem(str(standard.t_exp))
        self.table_standards.setItem(row, 2, item_t_exp)

    def add_standard(self):
        """Добавить новый стандарт"""
        # Создаем пустой стандарт
        standard = Standard(name="New Standard", t_theor=0.0, t_exp=0.0)
        self._add_row_to_table(standard)
        self.update_plot()

    def remove_standard(self):
        """Удалить выбранный стандарт"""
        selected_rows = set()
        for item in self.table_standards.selectedItems():
            selected_rows.add(item.row())

        # Удаляем строки снизу вверх, чтобы индексы не сбивались
        for row in sorted(selected_rows, reverse=True):
            self.table_standards.removeRow(row)
        self.update_plot()

    def get_calibration_from_ui(self) -> Calibration:
        """Получить калибровку из UI"""
        # Собираем стандарты из таблицы
        standards = []
        for row in range(self.table_standards.rowCount()):
            item_name = self.table_standards.item(row, 0)
            item_t_theoretical = self.table_standards.item(row, 1)
            item_t_experimental = self.table_standards.item(row, 2)

            if (
                item_name is None
                or item_t_theoretical is None
                or item_t_experimental is None
            ):
                raise ValueError(f"Empty values in row {row + 1}")

            name = item_name.text().strip()
            try:
                t_theoretical = float(item_t_theoretical.text())
                t_experimental = float(item_t_experimental.text())

                standard = Standard(
                    name=name,
                    t_theor=t_theoretical,
                    t_exp=t_experimental,
                )
                standards.append(standard)
            except ValueError:
                raise ValueError(f"Invalid values in row {row + 1}")

        # Создаем калибровку
        calibration = Calibration(
            name=self.le_name.text().strip(),
            calibration_type=self.cb_calibration_type.currentText(),
            description=self.le_description.text().strip(),
            standards=standards,
        )

        # Рассчитываем коэффициенты
        calibration.update_from_standards()

        return calibration

    def init_plot(self):
        """Инициализировать графики pyqtgraph"""
        # Создаем основной график калибровки
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel("left", "T theoretical - T experimental", units="°C")
        self.plot_widget.setLabel("bottom", "T experimental", units="°C")
        self.plot_widget.setTitle("Calibration Error Graph")

        # Создаем график остатков
        self.residuals_plot_widget = pg.PlotWidget()
        self.residuals_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.residuals_plot_widget.setLabel("left", "Residuals", units="°C")
        self.residuals_plot_widget.setLabel("bottom", "T experimental", units="°C")
        self.residuals_plot_widget.setTitle("Residuals Graph")

        # Добавляем графики в layout (создаем вертикальный layout для обоих графиков)
        self.plot_layout = QtWidgets.QVBoxLayout()
        self.plot_layout.addWidget(self.plot_widget)
        self.plot_layout.addWidget(self.residuals_plot_widget)
        self.verticalLayout_plot.addLayout(self.plot_layout)

        # Инициализируем элементы основного графика
        self.scatter_plot = pg.ScatterPlotItem(
            pen=pg.mkPen(color=(255, 0, 0), width=2),
            brush=pg.mkBrush(255, 0, 0, 100),
            size=10,
            symbol="o",
        )
        self.plot_widget.addItem(self.scatter_plot)

        self.curve_plot = pg.PlotCurveItem(pen=pg.mkPen(color=(0, 0, 255), width=2))
        self.plot_widget.addItem(self.curve_plot)

        # Инициализируем элементы графика остатков
        self.residuals_scatter_plot = pg.ScatterPlotItem(
            pen=pg.mkPen(color=(0, 128, 0), width=2),
            brush=pg.mkBrush(0, 128, 0, 100),
            size=10,
            symbol="o",
        )
        self.residuals_plot_widget.addItem(self.residuals_scatter_plot)

        # Добавляем линии для стандартной ошибки и расширенной неопределенности
        self.sec_line = pg.InfiniteLine(
            angle=0, pen=pg.mkPen("r", style=QtCore.Qt.PenStyle.DashLine)
        )
        self.residuals_plot_widget.addItem(self.sec_line)
        self.neg_sec_line = pg.InfiniteLine(
            angle=0, pen=pg.mkPen("r", style=QtCore.Qt.PenStyle.DashLine)
        )
        self.residuals_plot_widget.addItem(self.neg_sec_line)

        self.uncertainty_line = pg.InfiniteLine(
            angle=0, pen=pg.mkPen("orange", style=QtCore.Qt.PenStyle.DotLine)
        )
        self.residuals_plot_widget.addItem(self.uncertainty_line)
        self.neg_uncertainty_line = pg.InfiniteLine(
            angle=0, pen=pg.mkPen("orange", style=QtCore.Qt.PenStyle.DotLine)
        )
        self.residuals_plot_widget.addItem(self.neg_uncertainty_line)

        # Добавляем линию y=0
        self.zero_line = pg.InfiniteLine(angle=0, pen=pg.mkPen("k", width=1))
        self.residuals_plot_widget.addItem(self.zero_line)

    def update_plot(self):
        """Обновить график калибровки и остатков"""
        try:
            calibration = self.get_calibration_from_ui()
            standards = calibration.standards

            if len(standards) < 2:
                # Недостаточно данных для построения графика
                self.scatter_plot.setData([], [])
                self.curve_plot.setData([], [])
                self.residuals_scatter_plot.setData([], [])
                return

            # Преобразуем данные в numpy массивы для более эффективной обработки
            t_theor = np.array([s.t_theor for s in standards])
            t_exp = np.array([s.t_exp for s in standards])

            # Обновляем scatter plot (точки стандартов): Tэксп по оси X, (Tтеор - Tэксп) по оси Y
            delta_t = t_theor - t_exp
            self.scatter_plot.setData(t_exp, delta_t)

            # Данные для кривой калибровки: зависимость (Tтеор - Tэксп) от Tэксп
            if calibration.calibration_type == "linear":
                # Используем polyval для линейной калибровки: коэффициенты [b, a] для ax + b
                poly_coeffs = calibration.coefficients[
                    1::-1
                ]  # [coefficients[1], coefficients[0]]
            else:  # quadratic
                # Используем polyval для квадратичной калибровки: коэффициенты [c, b, a] для ax^2 + bx + c
                poly_coeffs = calibration.coefficients[
                    2::-1
                ]  # [coefficients[2], coefficients[1], coefficients[0]]

            # Диапазон для построения кривой по Tэксп с использованием numpy
            x_min, x_max = t_exp.min(), t_exp.max()
            x_range = np.linspace(x_min, x_max, 1000)

            # Векторизованное вычисление разницы с использованием polyval
            y_range = polyval(x_range, poly_coeffs)

            # Обновляем curve plot (калибровочная кривая)
            self.curve_plot.setData(x_range, y_range)

            # Рассчитываем статистику и обновляем график остатков
            stats = calibration.calculate_statistics()
            if stats:
                # Обновляем график остатков
                residuals = stats.get("residuals", [])
                if residuals:
                    self.residuals_scatter_plot.setData(t_exp, residuals)

                # Обновляем линии стандартной ошибки и неопределенности
                SEC = stats.get("SEC", 0.0)
                expanded_uncertainty = stats.get("expanded_uncertainty", 0.0)

                self.sec_line.setValue(SEC)
                self.neg_sec_line.setValue(-SEC)
                self.uncertainty_line.setValue(expanded_uncertainty)
                self.neg_uncertainty_line.setValue(-expanded_uncertainty)

                # Обновляем заголовок графика остатков с информацией о статистике
                R_squared = stats.get("R_squared", 0.0)
                self.residuals_plot_widget.setTitle(
                    f"Residuals Graph (R² = {R_squared:.4f}, SEC = {SEC:.2f}°C)"
                )

            # Настройка масштаба
            self.plot_widget.autoRange()
            self.residuals_plot_widget.autoRange()

            # Обновляем отображение статистики
            self.update_statistics_display(calibration, stats)

        except ValueError:
            # Если данные некорректны, очищаем графики
            self.scatter_plot.setData([], [])
            self.curve_plot.setData([], [])
            self.residuals_scatter_plot.setData([], [])
            # Очищаем статистику
            self.text_statistics.setPlainText(
                "Calibration statistics will be displayed here..."
            )

    def update_statistics_display(self, calibration: Calibration, stats: dict):
        """Обновить отображение статистики калибровки"""
        if not stats:
            self.text_statistics.setPlainText(
                "Calibration statistics will be displayed here..."
            )
            return

        # Простое отображение основных статистических параметров
        R_squared = stats.get("R_squared", 0.0)
        SEC = stats.get("SEC", 0.0)
        expanded_uncertainty = stats.get("expanded_uncertainty", 0.0)
        max_abs_error = stats.get("max_abs_error", 0.0)
        n_points = stats.get("n_points", 0)

        stats_text = f"""КАЛИБРОВКА: СТАТИСТИЧЕСКИЙ АНАЛИЗ
===============================
Тип калибровки: {calibration.calibration_type.upper()}
Количество точек: {n_points}

ПАРАМЕТРЫ:
R² (коэффициент детерминации): {R_squared:.4f}
SEC (стандартная ошибка): {SEC:.4f} °C
Расширенная неопределенность: ±{expanded_uncertainty:.4f} °C
Максимальная абсолютная ошибка: {max_abs_error:.4f} °C"""

        self.text_statistics.setPlainText(stats_text)

    def update_formula(self):
        """Обновить отображение формулы"""
        try:
            calibration = self.get_calibration_from_ui()
            formula = calibration.to_formule_str()
            self.label_formula.setText(formula)
            # Обновляем график при изменении формулы
            self.update_plot()
        except ValueError:
            # Если данные некорректны, показываем базовую формулу
            self.label_formula.setText("Tскор = Tэксп")

    def create_calibration(self):
        """Создать калибровку"""
        try:
            calibration = self.get_calibration_from_ui()
            log.debug(
                f"Создание калибровки: {calibration.name}, тип: {calibration.calibration_type}, стандарты: {calibration.standards}, коэффициенты: {calibration.coefficients}"
            )

            # Проверяем, что достаточно стандартов
            if len(calibration.standards) < 2:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Need at least 2 standards for calibration."
                )
                return

            # Проверяем, что коэффициенты рассчитались
            if all(abs(c) < 1e-10 for c in calibration.coefficients):
                QtWidgets.QMessageBox.warning(
                    self,
                    "Warning",
                    "Calibration coefficients are zero. Check your standards.",
                )
                return

            # Сохраняем калибровку и излучаем соответствующий сигнал
            self.calibration = calibration

            if self.edit_mode:
                # Редактирование существующей калибровки
                log.debug(f"Изменение калибровки: {calibration.name}")
                self.calibration_edited.emit(calibration)
            else:
                # Создание новой калибровки
                log.debug(f"Создание новой калибровки: {calibration.name}")
                self.calibration_created.emit(calibration)

            # Обновляем график после создания/редактирования калибровки
            self.update_plot()
            self.accept()

        except ValueError as e:
            log.debug(f"Ошибка при создании калибровки: {str(e)}")
            QtWidgets.QMessageBox.warning(self, "Warning", f"Invalid data: {str(e)}")
