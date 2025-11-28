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
from vta_collection.config import config
from vta_collection.data_connector import DataCon


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
    calibration_id: Optional[str] = None  # ID выбранной калибровки
    created_at: datetime = Field(default_factory=datetime.now)


class Measurement(QtCore.QObject):
    metadata: Metadata
    cal: Optional[Calibration] = None
    data_ready = QtCore.Signal(DataPoint)
    recording_enabled = False
    start_time: Optional[float] = None

    def __init__(self, metadata: Metadata, cal: Calibration | None = None):
        super().__init__()
        self.metadata = metadata
        self.cal = cal
        self.dc_emf = DataCon(name="emf", y_label="EMF, mV", parent=self)
        self.dc_temp = DataCon(name="temp", y_label="Temperature, ºC", parent=self)
        self.dc_output = DataCon(name="output", y_label="Output, V", parent=self)

    def snapshot_emf(self):
        self.dc_emf.save_data()

    def make_data_connection(self):
        if self.cal is not None:
            cal = self.cal  # костыль для mypy

            def to_data_con(data: DataPoint):
                if not self.recording_enabled:
                    return
                if self.start_time is None:
                    self.start_time = data.t1
                rel_t1 = data.t1 - self.start_time
                rel_t2 = data.t2 - self.start_time
                self.data_ready.emit(data)
                self.dc_temp.append_datapoint(x=rel_t1, y=cal.get_value(data.emf))
                self.dc_emf.append_datapoint(x=rel_t1, y=data.emf)
                self.dc_output.append_datapoint(x=rel_t2, y=data.output)
        else:

            def to_data_con(data: DataPoint):
                if not self.recording_enabled:
                    return
                if self.start_time is None:
                    self.start_time = data.t1
                rel_t1 = data.t1 - self.start_time
                rel_t2 = data.t2 - self.start_time
                self.data_ready.emit(data)
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
            config.last_save_dir = str(path.parent)
            config.update()

    def _export_to_zip(self, path: Path):
        with ZipFile(path, "w", ZIP_DEFLATED) as zipf:
            # Устанавливаем ID калибровки в metadata перед сохранением
            if self.cal is not None and self.cal.name is not None:
                self.metadata.calibration_id = self.cal.name
            else:
                self.metadata.calibration_id = None

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
            if self.cal is not None:
                # Сохраняем информацию о калибровке
                with zipf.open("calibration.json", "w") as byte_f:
                    text_f = TextIOWrapper(buffer=byte_f, encoding="utf-8")
                    self.cal.to_file(f=text_f)
                    text_f.flush()
        log.debug(f"Measurement saved at {path}")

    def clear(self):
        self.dc_emf.clear()
        self.dc_temp.clear()
        self.dc_output.clear()
        self.start_time = None

    @classmethod
    def load_from_zip(cls, path: Path, metadata: Metadata) -> "Measurement":
        """Загрузить измерение из ZIP-архива"""
        with ZipFile(path, "r") as zipf:
            # Загружаем калибровку, если она есть
            cal = None
            try:
                with zipf.open("calibration.json") as byte_f:
                    text_f = TextIOWrapper(buffer=byte_f, encoding="utf-8")
                    import json

                    cal_data = json.load(text_f)
                    # Валидируем коэффициенты перед созданием калибровки
                    c0 = cal_data.get("c0", 0.0)
                    c1 = cal_data.get("c1", 0.0)
                    c2 = cal_data.get("c2", 0.0)
                    c3 = cal_data.get("c3", 0.0)

                    import math

                    coefficients = [c0, c1, c2, c3]
                    for i, coeff in enumerate(coefficients):
                        if math.isnan(coeff) or math.isinf(coeff):
                            log.error(
                                f"Некорректный коэффициент c{i} в калибровке из архива: {coeff}"
                            )
                            raise ValueError(f"Invalid coefficient c{i}: {coeff}")

                    cal = Calibration(
                        c0=c0,
                        c1=c1,
                        c2=c2,
                        c3=c3,
                        name=cal_data.get("name"),
                        description=cal_data.get("description", ""),
                    )
            except KeyError:
                # Калибровка не найдена в архиве, пробуем загрузить по ID из metadata
                log.info(
                    "Calibration not found in archive, trying to load by ID from metadata"
                )
                if metadata.calibration_id is not None:
                    # Импортируем CalibrationManager для загрузки калибровки по ID
                    from vta_collection.calibration_manager import (
                        get_calibration_manager,
                    )

                    calibration_manager = get_calibration_manager()

                    cal = calibration_manager.get_cached_calibration(
                        metadata.calibration_id
                    )
                    if cal is None:
                        log.warning(
                            f"Calibration with ID '{metadata.calibration_id}' not found in calibration manager"
                        )
            except ValueError as e:
                log.error(f"Invalid calibration data in archive: {e}")
                # Пробуем загрузить по ID из metadata как fallback
                if metadata.calibration_id is not None:
                    from vta_collection.calibration_manager import (
                        get_calibration_manager,
                    )

                    calibration_manager = get_calibration_manager()
                    cal = calibration_manager.get_cached_calibration(
                        metadata.calibration_id
                    )
                    if cal is None:
                        log.warning(
                            f"Fallback calibration with ID '{metadata.calibration_id}' also not found"
                        )
            except Exception as e:
                log.error(f"Error loading calibration: {e}")

        # Создаем новое измерение с загруженными данными
        measurement = cls(metadata=metadata, cal=cal)
        return measurement
