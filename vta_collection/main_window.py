# from vta_collection.config import config
import warnings

from loguru import logger as log
from pglive.sources.live_plot_widget import LivePlotWidget
from PySide6 import QtCore, QtWidgets

from vta_collection.about_window import AboutWindow
from vta_collection.calibration import Calibration
from vta_collection.config import CONFIG_EDITOR_IGNORE_FIELDS, config
from vta_collection.config_editor import ConfigEditor
from vta_collection.heater import DataPoint
from vta_collection.measurement import Measurement
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
        self.label_temp.setVisible(False)
        self.label_temp_value.setVisible(False)
        self.label_calibration.setVisible(False)
        self.sb_speed.setValue(config.default_speed)
        self.about_window = AboutWindow(parent=self)
        self.action_about.triggered.connect(self.about_window.show)
        self.config_editor = ConfigEditor(
            config_instance=config,
            ignore_fields=CONFIG_EDITOR_IGNORE_FIELDS,
            parent=self,
        )
        self.action_config.triggered.connect(self.config_editor.show)

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

    def update_cal_polynom(self, cal: Calibration):
        self.label_calibration.setText(cal.to_formule_str())

    def set_live_plot(self, meas: Measurement):
        if meas.cal is not None:
            self.plot_layout.addWidget(self.w_temp)
            self.label_temp.setVisible(True)
            self.label_temp_value.setVisible(True)
            self.label_calibration.setVisible(True)
            self.label_calibration.setText(f"<b>{meas.cal.to_formule_str()}</b>")
        else:
            self.plot_layout.addWidget(self.w_emf)
            self.label_temp.setVisible(False)
            self.label_temp_value.setVisible(False)
            self.label_calibration.setVisible(False)

    def clear_plot_widgets(self):
        clear_layout(self.plot_layout)
        if hasattr(self, "w_emf") and self.w_emf:
            del self.w_emf
        if hasattr(self, "w_temp") and self.w_temp:
            del self.w_temp
        if hasattr(self, "w_out") and self.w_out:
            del self.w_out

    def set_meas(self, meas: Measurement):
        if meas.cal is not None:
            cal = meas.cal

            def update_display(data: DataPoint):
                self.label_input.setText(f"{data.emf:.3f}")
                self.label_output.setText(f"{data.output:.3f}")
                self.label_temp_value.setText(f"{cal.get_value(data.emf):.1f}")
        else:

            def update_display(data: DataPoint):
                self.label_input.setText(f"{data.emf:.3f}")
                self.label_output.setText(f"{data.output:.3f}")

        self.clear_plot_widgets()

        self.w_emf = meas.dc_emf.widget
        self.w_temp = meas.dc_temp.widget
        self.w_out = meas.dc_output.widget

        self.action_save.triggered.disconnect()
        self.action_save.triggered.connect(meas.save_dialog)
        with warnings.catch_warnings(action="ignore"):
            self.btn_output.clicked.disconnect()
        self.btn_output.clicked.connect(self.w_out.show)
        with warnings.catch_warnings(action="ignore"):
            meas.data_ready.disconnect()
        meas.data_ready.connect(update_display)

        self.label_operator.setText(f"Operator: <b>{meas.metadata.operator}</b>")
        self.label_sample.setText(f"Sample: <b>{meas.metadata.sample}</b>")

        self.set_live_plot(meas=meas)

    # def closeEvent(self, event):
    #     self.w_out.close()
    #     return super().closeEvent(event)
