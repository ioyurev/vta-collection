import csv
from io import TextIOWrapper
from math import inf

# from pglive.kwargs import LeadingLine, Orientation
from pglive.sources.data_connector import DataConnector
from pglive.sources.live_plot import LiveLinePlot
from pglive.sources.live_plot_widget import LivePlotWidget

# from pyqtgraph import mkPen
from PySide6 import QtCore


class DataCon(QtCore.QObject):
    def __init__(
        self,
        name: str,
        y_label: str | None = None,
        x_label: str = "time, s",
        line_color: str = "white",
        max_points: float = inf,
        parent=None,
    ):
        self.name = name
        self.x_label = x_label
        self.y_label = y_label
        self.llp = LiveLinePlot(name=name, pen=line_color)
        self.dc = DataConnector(plot=self.llp, max_points=max_points)
        self.widget = LivePlotWidget()
        self.widget.addItem(self.llp)
        plot_item = self.widget.getPlotItem()
        plot_item.setLabel(axis="left", text=self.y_label)
        plot_item.setLabel(axis="bottom", text=self.x_label)

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
