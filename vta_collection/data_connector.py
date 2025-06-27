import csv
from io import TextIOWrapper
from math import inf
from typing import List, NamedTuple

# from pglive.kwargs import LeadingLine, Orientation
from pglive.sources.data_connector import DataConnector
from pglive.sources.live_plot import LiveLinePlot
from pglive.sources.live_plot_widget import LivePlotWidget

# from pyqtgraph import mkPen
from PySide6 import QtCore


class DataPack(NamedTuple):
    x_label: str
    y_label: str
    x: List
    y: List

    def to_csv(self, f: TextIOWrapper):
        writer = csv.writer(f, lineterminator=";\r\n")
        writer.writerow((self.x_label, self.y_label))
        writer.writerows(zip(self.x, self.y))


class DataCon(QtCore.QObject):
    saved_data: None | DataPack = None

    def __init__(
        self,
        name: str,
        y_label: str = "",
        x_label: str = "time, s",
        line_color: str = "white",
        max_points: float = inf,
        parent=None,
    ):
        super().__init__(parent)
        self.name = name
        self.x_label = x_label
        self.y_label = y_label
        self.llp = LiveLinePlot(name=name, pen=line_color)
        self.dc = DataConnector(
            plot=self.llp,
            max_points=max_points,
            plot_rate=5,
        )
        self.widget = LivePlotWidget()
        self.widget.addItem(self.llp)
        plot_item = self.widget.getPlotItem()
        plot_item.setLabel(axis="left", text=self.y_label)
        plot_item.setLabel(axis="bottom", text=self.x_label)

    def save_data(self) -> None:
        self.saved_data = DataPack(
            x_label=self.x_label,
            y_label=self.y_label,
            x=self.dc.x.copy(),
            y=self.dc.y.copy(),
        )

    def append_datapoint(self, x: int | float, y: int | float) -> None:
        self.dc.cb_append_data_point(y, x)

    def append_dataarray(self, x: list[float | int], y: list[float | int]) -> None:
        self.dc.cb_append_data_array(y, x)

    def clear(self) -> None:
        self.dc.clear()
        self.llp.clear()


if __name__ == "__main__":
    """Example usage of DataCon class"""
    import random
    import sys
    import time
    from threading import Thread

    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

    class ExampleWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("DataCon Example")
            self.resize(800, 600)

            # Create data connector
            self.data_con = DataCon(
                name="Example Plot", y_label="Value", x_label="Time (s)"
            )

            # Setup UI
            central_widget = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(self.data_con.widget)
            central_widget.setLayout(layout)
            self.setCentralWidget(central_widget)

            # Start data generation thread
            self.running = True
            self.thread = Thread(target=self.generate_data)
            self.thread.start()

        def generate_data(self):
            """Generate random data points"""
            x = 0
            while self.running:
                y = random.uniform(0, 100)
                self.data_con.append_datapoint(x, y)
                x += 0.1
                time.sleep(0.1)

        def closeEvent(self, event):
            self.running = False
            self.thread.join()
            event.accept()

    # Run the example
    app = QApplication(sys.argv)
    window = ExampleWindow()
    window.show()
    sys.exit(app.exec())
