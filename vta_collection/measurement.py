from datetime import datetime
from io import TextIOWrapper
from pathlib import Path
from typing import NamedTuple, Optional
from zipfile import ZIP_DEFLATED, ZipFile

from loguru import logger as log
from pydantic import BaseModel, Field
from PySide6 import QtCore
from PySide6.QtWidgets import QFileDialog

from vta_collection.calibration import Calibration
from vta_collection.data_connector import DataCon


def save_vtaz_file():
    filename, _ = QFileDialog.getSaveFileName(
        None,
        "Сохранить файл VTA zip",  # Заголовок окна
        "",  # Начальная директория
        "VTA zip Files (*.vtaz)",  # Фильтр файлов
    )

    if filename:
        return Path(filename)
    else:
        return None


class DataPoint(NamedTuple):
    t1: float
    emf: float
    t2: float
    output: float


class Metadata(BaseModel):
    sample: str
    operator: str
    created_at: datetime = Field(default_factory=datetime.now)


class Measurement(QtCore.QObject):
    metadata: Metadata
    dc_emf = DataCon(name="emf", y_label="EMF, mV")
    dc_temp = DataCon(name="temp", y_label="Temperature, ºC")
    dc_output = DataCon(name="output", y_label="Output, V")
    cal: Optional[Calibration] = None
    recording_enabled = False
    data_ready = QtCore.Signal(DataPoint)

    def __init__(self, metadata: Metadata, cal: Calibration | None = None):
        super().__init__()
        self.metadata = metadata
        self.cal = cal

    def set_recording_enabled(self, enabled: bool):
        self.recording_enabled = enabled
        log.debug(f"Recording set to enabled: {enabled}")

    def make_data_connection(self):
        if self.cal is not None:
            cal = self.cal  # костыль для mypy

            def to_data_con(data: DataPoint):
                self.data_ready.emit(data)
                if self.recording_enabled:
                    self.dc_temp.append_datapoint(x=data.t1, y=cal.get_value(data.emf))
                    self.dc_emf.append_datapoint(x=data.t1, y=data.emf)
                    self.dc_output.append_datapoint(x=data.t2, y=data.output)
        else:

            def to_data_con(data: DataPoint):
                self.data_ready.emit(data)
                if self.recording_enabled:
                    self.dc_emf.append_datapoint(x=data.t1, y=data.emf)
                    self.dc_output.append_datapoint(x=data.t2, y=data.output)

        return to_data_con

    def save_dialog(self):
        path = save_vtaz_file()
        if path:
            self._save(path=path)

    def _save(self, path: Path):
        with ZipFile(path, "w", ZIP_DEFLATED) as zipf:
            self.metadata.created_at = datetime.now()
            metadata_json = self.metadata.model_dump_json(indent=2)
            zipf.writestr("metadata.json", metadata_json.encode("utf-8"))
            with zipf.open("data_input.csv", "w") as byte_f:
                text_f = TextIOWrapper(buffer=byte_f, encoding="utf-8")
                self.dc_emf.to_csv(f=text_f)
                text_f.flush()
            if self.cal is not None:
                with zipf.open("calibration.json", "w") as byte_f:
                    text_f = TextIOWrapper(buffer=byte_f, encoding="utf-8")
                    self.cal.to_file(f=text_f)
                    text_f.flush()

    def reset(self):
        self.dc_emf.clear()
        self.dc_temp.clear()
        self.dc_output.clear()
