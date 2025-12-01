from pathlib import Path
from typing import Final

from loguru import logger as log
from pydantic import BaseModel, Field, field_serializer

from vta_collection.path_utils import get_appdata_path
from vta_collection.serializable import SerializableMixin


class Config(BaseModel, SerializableMixin):
    operator: str = "Operator"
    thermocouple_coefficients: list[float] = [
        0.9643027,
        79.495086,
        -4.9990310,
        0.634176,
        -0.047440967,
        0.0021811337,
        -5.8324228e-05,
        8.2433725e-07,
        -4.5928480e-09,
    ]
    calibration_enabled: bool = False
    is_test_mode: bool = False
    default_speed: int = 5
    adam4011_address: int = 1
    adam4021_address: int = 3
    adam_baudrate: int = 9600
    last_save_measurement_index: int = 1
    last_save_dir: Path = Field(default_factory=lambda: Path(".").resolve())
    comport: str = "COM1"
    last_selected_calibration: str = ""

    @field_serializer("last_save_dir")
    def serialize_path(self, value: Path) -> str:
        return str(value)

    @classmethod
    def from_file(cls, path: Path):
        try:
            config = cls.from_json_file(path)
        except Exception as e:
            log.error(e)
            log.warning("Using default config.")
            config = Config()
            config.update()
        log.debug(f"Loaded config: {config}")
        return config

    def update(self):
        self.to_json_file(CONFIG_PATH)
        log.debug("Config file updated")


appdata_path = get_appdata_path()
CONFIG_PATH = appdata_path / "config.json"
config = Config.from_file(CONFIG_PATH)
CONFIG_EDITOR_IGNORE_FIELDS: Final = [
    "operator",
    "calibration_enabled",
]
