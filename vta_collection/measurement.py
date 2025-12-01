import json
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
from vta_collection.cold_junction_compensator import ColdJunctionCompensator
from vta_collection.config import config
from vta_collection.data_connector import DataCon
from vta_collection.temperature_chain import TemperatureChain


def prompt_save_path(initial_path: Path):
    filename, _ = QFileDialog.getSaveFileName(
        None,
        "Save VTA zip file",
        str(initial_path),
        "VTA zip Files (*.vtaz)",
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
    vtaz_version: str = "1.0"  # Версия формата .vtaz файла
    created_at: datetime = Field(default_factory=datetime.now)


class Measurement(QtCore.QObject):
    metadata: Metadata
    cal: Calibration
    data_ready = QtCore.Signal(DataPoint)
    recording_enabled = False
    start_time: Optional[float] = None

    def __init__(self, metadata: Metadata, cal: Calibration):
        super().__init__()
        self.metadata = metadata
        self.cal = cal
        self.dc_emf = DataCon(name="emf", y_label="EMF, mV", parent=self)
        self.dc_temp = DataCon(name="temp", y_label="Temperature, ºC", parent=self)
        self.dc_output = DataCon(name="output", y_label="Output, V", parent=self)

        # Создаем компенсатор холодного спая
        self.compensator = ColdJunctionCompensator(calibration=cal)

        # Создаем цепочку обработки данных
        self.temp_chain = TemperatureChain(cal=cal, compensator=self.compensator)

    def snapshot_emf(self):
        self.dc_emf.save_data()

    def make_data_connection(self):
        def to_data_con(data: DataPoint):
            if not self.recording_enabled:
                return
            if self.start_time is None:
                self.start_time = data.t1
            rel_t1 = data.t1 - self.start_time
            rel_t2 = data.t2 - self.start_time
            self.data_ready.emit(data)

            # Используем TemperatureChain для получения значения
            temp_or_emf = self.temp_chain.get_value(data.emf)
            self.dc_temp.append_datapoint(x=rel_t1, y=temp_or_emf)
            self.dc_emf.append_datapoint(x=rel_t1, y=data.emf)
            self.dc_output.append_datapoint(x=rel_t2, y=data.output)

        return to_data_con

    def save_dialog(self):
        initial_path = (
            Path(config.last_save_dir)
            / f"{config.last_save_measurement_index:03} {self.metadata.sample}"
        )
        path = prompt_save_path(initial_path=initial_path)
        if path:
            self._export_to_zip(path=path)
            config.last_save_measurement_index += 1
            config.last_save_dir = path.parent
            config.update()

    def _export_to_zip(self, path: Path):
        with ZipFile(path, "w", ZIP_DEFLATED) as zipf:
            self.metadata.created_at = datetime.now()
            metadata_json = self.metadata.model_dump_json(indent=2)
            zipf.writestr("metadata.json", metadata_json.encode("utf-8"))
            with zipf.open("data_input.csv", "w") as byte_f:
                text_f = TextIOWrapper(buffer=byte_f, encoding="utf-8")
                if self.dc_emf.saved_data is not None:
                    self.dc_emf.saved_data.to_csv(f=text_f)
                else:
                    raise Exception("No data to save")
                text_f.flush()
            with zipf.open("calibration.json", "w") as byte_f:
                text_f = TextIOWrapper(buffer=byte_f, encoding="utf-8")
                self.cal.to_file(f=text_f)
                text_f.flush()
            # Сохраняем коэффициенты термопары в отдельный файл
            thermocouple_data = {
                "thermocouple_coefficients": config.thermocouple_coefficients
            }
            zipf.writestr(
                "thermocouple.json",
                json.dumps(thermocouple_data, indent=2, ensure_ascii=False).encode(
                    "utf-8"
                ),
            )
            # Сохраняем данные холодного спая
            cjc_data = self.compensator.export_cjc_data()
            zipf.writestr(
                "cjc.json",
                json.dumps(cjc_data, indent=2, ensure_ascii=False).encode("utf-8"),
            )
        log.debug(f"Measurement saved at {path}")

    def clear(self):
        self.dc_emf.clear()
        self.dc_temp.clear()
        self.dc_output.clear()
        self.start_time = None
