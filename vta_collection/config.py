import json
import os
import sys
from pathlib import Path

from loguru import logger as log
from pydantic import BaseModel


def set_appdata_folder() -> Path:
    app_folder = "vta-collection"
    if sys.platform.startswith("linux"):
        appdata_folder = os.environ.get(
            "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
        )
    else:
        appdata_folder = os.getenv("APPDATA")
        if appdata_folder is None:
            raise RuntimeError("Not found appdata folder")
    appdata_path = Path(os.path.join(appdata_folder, app_folder))
    if not os.path.exists(appdata_path):
        os.makedirs(appdata_path)
    return Path(appdata_path)


class Config(BaseModel):
    operator: str = "Operator"
    c0: float = 0.0
    c1: float = 0.0
    c2: float = 0.0
    c3: float = 0.0
    calibration_enabled: bool = False
    is_test_mode: bool = False
    default_speed: int = 5
    adam4011_address: int = 1
    adam4021_address: int = 3

    @classmethod
    def from_file(cls, path: Path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
                config = cls(**data)
        except Exception as e:
            log.error(e)
            log.warning("Using default config.")
            config = Config()
        log.debug(f"Loaded config: {config}")
        return config

    def to_file(self, path: Path):
        with open(path, "w") as f:
            data = self.model_dump()
            json.dump(data, f, indent=2)

    def update(self):
        self.to_file(path=CONFIG_PATH)


appdata_path = set_appdata_folder()
CONFIG_PATH = appdata_path / "config.json"
config = Config.from_file(CONFIG_PATH)
