import json
from pathlib import Path
from typing import Any

from loguru import logger as log


class FileManager:
    """Универсальный менеджер файловых операций"""

    @staticmethod
    def save_json(data: Any, file_path: Path) -> None:
        """Сохранение данных в JSON файл с обработкой ошибок"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                log.debug(f"Successfully saved to {file_path}")
        except Exception as e:
            error_message = f"Error saving: {e}"
            log.error(error_message)
            raise Exception(error_message)

    @staticmethod
    def load_json(file_path: Path) -> Any:
        """Загрузка данных из JSON файла с обработкой ошибок"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            log.debug(f"Successfully loaded from {file_path}")
            return data
        except Exception as e:
            error_message = f"Error loading: {e}"
            log.error(error_message)
            raise Exception(error_message)
