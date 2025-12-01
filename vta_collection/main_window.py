# from vta_collection.config import config
import warnings
from collections import deque

from loguru import logger as log
from pglive.sources.live_plot_widget import LivePlotWidget
from PySide6 import QtCore, QtWidgets

from vta_collection.about_window import AboutWindow
from vta_collection.calibration_manager_window import CalibrationManagerWindow
from vta_collection.config import CONFIG_EDITOR_IGNORE_FIELDS, config
from vta_collection.config_editor import ConfigEditor
from vta_collection.measurement import DataPoint, Measurement
from vta_collection.ui.main_window import Ui_MainWindow


def clear_layout(layout: QtWidgets.QVBoxLayout):
    # """Рекурсивно удаляет все виджеты и дочерние макеты из QLayout."""
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        widget.deleteLater()
        del item
    log.debug("Layout cleared")


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    out_connection: QtCore.QMetaObject.Connection | None = None
    w_emf: LivePlotWidget
    w_temp: LivePlotWidget
    w_out: LivePlotWidget

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.btn_start.clicked.connect(self.start_loop)
        self.btn_stop.clicked.connect(self.stop_loop)
        self.btn_stop_heat.clicked.connect(self.stop_heating)
        self.sb_speed.setValue(config.default_speed)
        self.about_window = AboutWindow(parent=self)
        self.action_about.triggered.connect(self.about_window.show)
        self.config_editor = ConfigEditor(
            config_instance=config,
            ignore_fields=CONFIG_EDITOR_IGNORE_FIELDS,
            parent=self,
        )
        self.action_config.triggered.connect(self.config_editor.show)

        # Добавляем функциональность для работы с калибровками
        self.calibration_manager_window = CalibrationManagerWindow(parent=self)
        self.action_manage_calibrations.triggered.connect(
            self.calibration_manager_window.show
        )

    def new_meas(self):
        self.action_new.setEnabled(False)
        self.action_save.setEnabled(False)
        self.action_close.setEnabled(True)
        self.btn_start.setEnabled(True)
        self.sb_speed.setValue(config.default_speed)

    def start_loop(self):
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_stop_heat.setEnabled(True)

    def stop_loop(self):
        self.btn_stop.setEnabled(False)
        self.action_new.setEnabled(True)
        self.action_save.setEnabled(True)

    def stop_heating(self):
        self.sb_speed.setValue(0)

    def set_live_plot(self, meas: Measurement):
        self.plot_layout.addWidget(self.w_temp)
        self.label_temp.setVisible(True)
        self.label_temp_value.setVisible(True)
        self.label_calibration.setVisible(True)
        self.label_calibration.setText(f"<b>{meas.cal.to_formule_str()}</b>")

    def clear_plot_widgets(self):
        clear_layout(self.plot_layout)
        # Explicitly delete widgets to prevent memory leaks
        for attr in ["w_emf", "w_temp", "w_out"]:
            widget = getattr(self, attr, None)
            if widget:
                widget.deleteLater()
                delattr(self, attr)

    def set_meas(self, meas: Measurement):
        window_size = 25
        intervals: deque = deque(maxlen=window_size)
        last_time_closure = 0.0

        def sampling_rate(data: DataPoint):
            nonlocal last_time_closure
            try:
                # Skip the first interval because last_time_closure is 0.0 initially
                if last_time_closure != 0.0:
                    current_interval = data.t1 - last_time_closure
                    intervals.append(current_interval)
                last_time_closure = data.t1

                # If we have intervals, compute the average
                if intervals:
                    average_interval = sum(intervals) / len(intervals)
                    sample_rate = 1 / average_interval
                    self.label_sampling_rate.setText(f"{sample_rate:.1f}")
            except ZeroDivisionError:
                pass

        def update_display_cal(data: DataPoint):
            self.label_input.setText(f"{data.emf:.3f}")
            self.label_output_value.setText(
                f"{data.output:.3f}"
            )  # Updated to use the new label name
            # Используем TemperatureChain для расчета температуры
            temp = meas.temp_chain.get_value(data.emf)
            self.label_temp_value.setText(f"{temp:.1f}")

            sampling_rate(data=data)

        self.clear_plot_widgets()

        # Обновляем информацию о холодном спае
        cjc_data = meas.compensator.get_cjc_data()
        if cjc_data:
            self.label_cjc_temp_value.setText(f"{cjc_data.temperature:.1f}")
            self.label_cjc_emf_value.setText(f"{cjc_data.e_cold:.3f}")
        else:
            self.label_cjc_temp_value.setText("N/A")
            self.label_cjc_emf_value.setText("N/A")

        # Обновляем отображение активной калибровки
        self.label_calibration.setText(meas.cal.to_formule_str())

        self.w_emf = meas.dc_emf.widget
        self.w_temp = meas.dc_temp.widget
        self.w_out = meas.dc_output.widget

        self.action_save.triggered.disconnect()
        self.action_save.triggered.connect(meas.save_dialog)
        with warnings.catch_warnings(action="ignore"):
            self.btn_output_display.clicked.disconnect()
        self.btn_output_display.clicked.connect(self.w_out.show)
        with warnings.catch_warnings(action="ignore"):
            meas.data_ready.disconnect()
        meas.data_ready.connect(update_display_cal)

        self.label_operator.setText(f"Operator: <b>{meas.metadata.operator}</b>")
        self.label_sample.setText(f"Sample: <b>{meas.metadata.sample}</b>")

        self.set_live_plot(meas=meas)

    # def closeEvent(self, event):
    #     self.w_out.close()
    #     return super().closeEvent(event)
