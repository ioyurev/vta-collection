from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger as log
from PySide6 import QtCore

from vta_collection.calibration import Calibration
from vta_collection.file_manager import FileManager
from vta_collection.path_utils import get_appdata_path


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

    def __init__(self) -> None:
        super().__init__()
        self.calibrations: Dict[str, Calibration] = {}
        self.active_calibration: Calibration
        self.active_calibration_name: str
        self.calibrations_dir = self._get_calibrations_dir()
        self._ensure_calibrations_dir()
        self.load_all_calibrations()

    def _get_calibrations_dir(self) -> Path:
        """Получить директорию для хранения калибровок"""
        return get_appdata_path() / "calibrations"

    def _ensure_calibrations_dir(self) -> None:
        """Создать директорию для калибровок, если она не существует"""
        if not self.calibrations_dir.exists():
            self.calibrations_dir.mkdir(parents=True, exist_ok=True)

    def save_calibration(self, calibration: Calibration) -> None:
        """Сохранить калибровку в файл"""
        # Валидация имени
        name = calibration.name
        # Используем встроенный метод сериализации Calibration
        cal_data = calibration.model_dump()
        file_path = self.calibrations_dir / f"{name}.json"
        FileManager.save_json(cal_data, file_path)

        self.calibrations[name] = calibration
        log.debug(
            f"Калибровка '{name}' сохранена со стандартами: {calibration.standards}"
        )
        self.calibration_added.emit(name)

    def load_calibration(self, name: str) -> Calibration:
        """Загрузить калибровку из файла"""
        file_path = self.calibrations_dir / f"{name}.json"
        cal_data = FileManager.load_json(file_path)

        # Создаем калибровку с использованием статического метода
        calibration = Calibration.from_dict(cal_data)

        self.calibrations[name] = calibration
        log.debug(
            f"Калибровка '{name}' загружена со стандартами: {calibration.standards}"
        )
        return calibration

    def load_all_calibrations(self) -> None:
        """Загрузить все доступные калибровки из директории"""
        self.calibrations.clear()
        try:
            for file_path in self.calibrations_dir.glob("*.json"):
                name = file_path.stem
                self.load_calibration(name)
            log.info(f"Загружены калибровки: {self.calibrations}")
        except Exception as e:
            log.error(f"Ошибка при загрузке калибровок: {e}")

    def delete_calibration(self, name: str) -> None:
        """Удалить калибровку"""
        try:
            if name in self.calibrations:
                del self.calibrations[name]

            file_path = self.calibrations_dir / f"{name}.json"
            if file_path.exists():
                file_path.unlink()

            if self.active_calibration_name == name:
                # self.active_calibration = None
                # self.active_calibration_name = None
                raise NotImplementedError()

            log.debug(
                f"Калибровка '{name}' удалена, остались калибровки: {self.calibrations}"
            )
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
            log.debug(
                f"Активная калибровка установлена на '{name}', тип: {self.active_calibration.calibration_type}, коэффициенты: {self.active_calibration.coefficients}"
            )
            return True
        else:
            log.warning(f"Калибровка '{name}' не найдена")
            return False

    def get_active_calibration(self) -> Calibration:
        """Получить активную калибровку"""
        return self.active_calibration

    def get_calibration_description(self, name: str) -> str:
        """Получить описание калибровки (извлекается из файла)"""
        try:
            file_path = self.calibrations_dir / f"{name}.json"
            if file_path.exists():
                cal_data = FileManager.load_json(file_path)
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
