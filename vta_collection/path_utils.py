import os
import sys
from pathlib import Path


def get_appdata_path(app_name: str = "vta-collection") -> Path:
    """Получить путь к данным приложения"""
    if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
        # Linux и macOS
        appdata_folder = os.environ.get(
            "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
        )
    else:
        # Windows
        appdata_folder = os.getenv("APPDATA")
        if appdata_folder is None:
            raise RuntimeError("AppData folder not found")

    appdata_path = Path(os.path.join(appdata_folder, app_name))
    appdata_path.mkdir(parents=True, exist_ok=True)
    return appdata_path
