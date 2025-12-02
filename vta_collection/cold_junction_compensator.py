from typing import NamedTuple

from vta_collection.calibration import Calibration
from vta_collection.config import config
from vta_collection.hardware import get_hardware
from vta_collection.thermocouple import get_thermocouple


class CjcData(NamedTuple):
    temperature: float
    e_cold: float


class ColdJunctionCompensator:
    """Компенсатор холодного спая"""

    def __init__(self, calibration: Calibration):
        self.calibration = calibration
        self.cjc_data: CjcData

        # Инициализируем данные компенсации
        self._initialize_compensation()

    def _initialize_compensation(self):
        """Инициализация данных компенсации холодного спая"""
        # Остановливаем основной цикл перед запросом cjc
        from vta_collection.heater.controller import get_heater

        get_heater().stop_loop()

        # Получаем температуру холодного спая
        cjc_temp = (
            get_hardware(auto_find=True).adam4011.get_cjc_temperature()
            if not config.is_test_mode
            else 25.0
        )

        # Вычисляем ЭДС холодного спая методом бисекции
        cjc_emf = self._calculate_emf_by_temperature(cjc_temp)

        self.cjc_data = CjcData(temperature=cjc_temp, e_cold=cjc_emf)

    def _calculate_emf_by_temperature(self, target_temp: float) -> float:
        """Вычисление ЭДС по температуре методом бисекции"""
        # Получаем глобальный экземпляр термопары
        thermocouple = get_thermocouple()

        return thermocouple.temperature_to_emf(target_temp=target_temp)

    def compensate(self, emf: float) -> float:
        """Компенсация холодного спая"""
        # Компенсированная ЭДС = сырая ЭДС + ЭДС холодного спая
        e_hot = emf + self.cjc_data.e_cold
        return e_hot

    def get_cjc_data(self) -> CjcData:
        """Получение данных компенсации холодного спая"""
        return self.cjc_data

    def export_cjc_data(self) -> dict:
        """Экспорт данных холодного спая в формате JSON"""
        return {
            "temperature": self.cjc_data.temperature,
            "e_cold": self.cjc_data.e_cold,
        }
