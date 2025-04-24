import csv
from io import TextIOWrapper

# from pglive.kwargs import LeadingLine, Orientation
from pglive.sources.data_connector import DataConnector
from pglive.sources.live_plot import LiveLinePlot
from pglive.sources.live_plot_widget import LivePlotWidget

# from pyqtgraph import mkPen
from PySide6 import QtCore


class DataCon(QtCore.QObject):
    widget: LivePlotWidget

    def __init__(
        self,
        name: str,
        y_label: str | None = None,
        x_label: str = "time, s",
        line_color: str = "white",
        text_color: str = "black",
    ):  # , lead_line_enabled: bool = False
        self.name = name
        self.x_label = x_label
        self.y_label = y_label
        self.llp = LiveLinePlot(name=name, pen=line_color)
        # if lead_line_enabled:
        #     self.llp.set_leading_line(LeadingLine.VERTICAL, pen=mkPen(line_color), text_axis=LeadingLine.AXIS_Y, text_color=text_color,
        #                 text_orientation=Orientation.HORIZONTAL)
        self.dc = DataConnector(plot=self.llp)

    def make_widget(self, parent=None):
        self.widget = LivePlotWidget(parent=parent)
        self.add_to_widget(widget=self.widget)
        return self.widget

    def add_to_widget(self, widget: LivePlotWidget, title: str | None = None):
        widget.addItem(self.llp)
        plot_item = widget.getPlotItem()
        if self.y_label is not None:
            plot_item.setLabel(axis="left", text=self.y_label)
        plot_item.setLabel(axis="bottom", text=self.x_label)
        if title is not None:
            plot_item.setTitle(title=title)
        pass

    def to_csv(self, f: TextIOWrapper):
        writer = csv.writer(f, lineterminator=";\r\n")
        writer.writerow((self.x_label, self.y_label))
        writer.writerows(zip(self.dc.x, self.dc.y))

    def append_datapoint(self, x: int | float, y: int | float):
        self.dc.cb_append_data_point(y, x)

    def append_dataarray(self, x: list[float | int], y: list[float | int]):
        self.dc.cb_append_data_array(y, x)

    def clear(self):
        self.dc.clear()
        self.llp.clear()
