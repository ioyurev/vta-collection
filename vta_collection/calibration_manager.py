import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger as log
from PySide6 import QtCore

from vta_collection.calibration import Calibration


class CalibrationManager(QtCore.QObject):
    """
    Менеджер для управления несколькими калибровками.
    Позволяет загружать, сохранять и переключаться между различными калибровками.
    """

    # Сигналы для уведомления об изменениях
    calibration_added = QtCore.Signal(str)
    calibration_removed = QtCore.Signal(str)
    calibration_updated = QtCore.Signal(str)
    active_calibration_changed = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        self.calibrations: Dict[str, Calibration] = {}
        self._calibration_cache: Dict[str, Calibration] = {}  # Кэш для оптимизации
        self.active_calibration: Optional[Calibration] = None
        self.active_calibration_name: Optional[str] = None
        self.calibrations_dir = self._get_calibrations_dir()
        self._ensure_calibrations_dir()
        self.load_all_calibrations()

    def _get_calibrations_dir(self) -> Path:
        """Получить директорию для хранения калибровок"""
        app_folder = "vta-collection"
        if os.name == "nt":  # Windows
            appdata_folder = os.getenv("APPDATA")
            if appdata_folder is None:
                raise RuntimeError("Не найдена папка AppData")
        else:  # Unix-like systems
            appdata_folder = os.environ.get(
                "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
            )

        appdata_path = Path(os.path.join(appdata_folder, app_folder))
        return appdata_path / "calibrations"

    def _ensure_calibrations_dir(self):
        """Создать директорию для калибровок, если она не существует"""
        if not self.calibrations_dir.exists():
            self.calibrations_dir.mkdir(parents=True, exist_ok=True)

    def _validate_calibration_name(self, name: str) -> bool:
        """Проверить валидность имени калибровки"""
        import re

        if not name or len(name) > 100:
            return False
        # Проверяем, что имя содержит только безопасные символы
        if not re.match(r"^[a-zA-Z0-9_-]+$", name):
            return False
        return True

    def _validate_calibration_coefficients(self, calibration: Calibration) -> bool:
        """Проверить валидность коэффициентов калибровки"""
        import math

        coefficients = [calibration.c0, calibration.c1, calibration.c2, calibration.c3]
        for coeff in coefficients:
            if math.isnan(coeff) or math.isinf(coeff):
                return False
        return True

    def save_calibration(
        self, name: str, calibration: Calibration, description: str = ""
    ):
        """Сохранить калибровку в файл"""
        # Валидация имени
        if not self._validate_calibration_name(name):
            raise ValueError(f"Некорректное имя калибровки: {name}")

        # Валидация коэффициентов
        if not self._validate_calibration_coefficients(calibration):
            raise ValueError("Некорректные коэффициенты калибровки")

        try:
            cal_data = {
                "name": name,
                "description": description,
                "c0": calibration.c0,
                "c1": calibration.c1,
                "c2": calibration.c2,
                "c3": calibration.c3,
            }

            file_path = self.calibrations_dir / f"{name}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(cal_data, f, indent=2, ensure_ascii=False)

            self.calibrations[name] = calibration
            # Обновляем кэш
            self._calibration_cache[name] = calibration
            log.info(f"Калибровка '{name}' сохранена")
            self.calibration_added.emit(name)
        except Exception as e:
            log.error(f"Ошибка при сохранении калибровки '{name}': {e}")
            raise

    def get_cached_calibration(self, name: str) -> Optional[Calibration]:
        """Получить калибровку из кэша или загрузить если не в кэше"""
        if name in self._calibration_cache:
            return self._calibration_cache[name]

        calibration = self.load_calibration(name)
        if calibration:
            self._calibration_cache[name] = calibration
        return calibration

    def load_calibration(self, name: str) -> Optional[Calibration]:
        """Загрузить калибровку из файла"""
        try:
            file_path = self.calibrations_dir / f"{name}.json"
            if not file_path.exists():
                log.warning(f"Файл калибровки '{name}' не найден")
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                cal_data = json.load(f)

            # Валидация данных из файла
            c0 = cal_data.get("c0", 0.0)
            c1 = cal_data.get("c1", 0.0)
            c2 = cal_data.get("c2", 0.0)
            c3 = cal_data.get("c3", 0.0)

            # Проверяем валидность коэффициентов
            import math

            coefficients = [c0, c1, c2, c3]
            for i, coeff in enumerate(coefficients):
                if math.isnan(coeff) or math.isinf(coeff):
                    log.error(
                        f"Некорректный коэффициент c{i} в калибровке '{name}': {coeff}"
                    )
                    return None

            calibration = Calibration(
                c0=c0,
                c1=c1,
                c2=c2,
                c3=c3,
                name=cal_data.get("name"),
                description=cal_data.get("description", ""),
            )

            self.calibrations[name] = calibration
            # Добавляем в кэш
            self._calibration_cache[name] = calibration
            return calibration
        except Exception as e:
            log.error(f"Ошибка при загрузке калибровки '{name}': {e}")
            return None

    def load_all_calibrations(self):
        """Загрузить все доступные калибровки из директории"""
        self.calibrations.clear()
        try:
            for file_path in self.calibrations_dir.glob("*.json"):
                name = file_path.stem
                self.load_calibration(name)
            log.info(f"Загружено {len(self.calibrations)} калибровок")
        except Exception as e:
            log.error(f"Ошибка при загрузке калибровок: {e}")

    def delete_calibration(self, name: str):
        """Удалить калибровку"""
        try:
            if name in self.calibrations:
                del self.calibrations[name]

            # Удаляем из кэша
            if name in self._calibration_cache:
                del self._calibration_cache[name]

            file_path = self.calibrations_dir / f"{name}.json"
            if file_path.exists():
                file_path.unlink()

            if self.active_calibration_name == name:
                self.active_calibration = None
                self.active_calibration_name = None

            log.info(f"Калибровка '{name}' удалена")
            self.calibration_removed.emit(name)
        except Exception as e:
            log.error(f"Ошибка при удалении калибровки '{name}': {e}")
            raise

    def get_calibration_names(self) -> List[str]:
        """Получить список имен всех доступных калибровок"""
        return list(self.calibrations.keys())

    def set_active_calibration(self, name: str) -> bool:
        """Установить активную калибровку по имени"""
        if name in self.calibrations:
            self.active_calibration = self.calibrations[name]
            self.active_calibration_name = name
            log.info(f"Активная калибровка установлена на '{name}'")
            return True
        else:
            log.warning(f"Калибровка '{name}' не найдена")
            return False

    def get_active_calibration(self) -> Optional[Calibration]:
        """Получить активную калибровку"""
        return self.active_calibration

    def get_calibration_description(self, name: str) -> str:
        """Получить описание калибровки (извлекается из файла)"""
        try:
            file_path = self.calibrations_dir / f"{name}.json"
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    cal_data = json.load(f)
                return cal_data.get("description", "")
        except Exception as e:
            log.error(f"Ошибка при получении описания калибровки '{name}': {e}")

        return ""


# Глобальный экземпляр менеджера калибровок
_calibration_manager_instance: Optional[CalibrationManager] = None


def get_calibration_manager() -> CalibrationManager:
    """Получить экземпляр CalibrationManager (singleton)"""
    global _calibration_manager_instance
    if _calibration_manager_instance is None:
        _calibration_manager_instance = CalibrationManager()
    return _calibration_manager_instance
