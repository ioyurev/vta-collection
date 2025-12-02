from vta_collection.calibration import Calibration
from vta_collection.cold_junction_compensator import ColdJunctionCompensator
from vta_collection.thermocouple import get_thermocouple


class TemperatureChain:
    """Цепочка обработки температурных данных - только физические расчеты"""

    def __init__(self, cal: Calibration, compensator: ColdJunctionCompensator):
        # Получаем глобальный экземпляр термопары
        thermocouple = get_thermocouple()
        # Определяем функцию расчета один раз при инициализации
        self._calculate = lambda x: cal.get_value(thermocouple.emf_to_temperature(
            compensator.compensate(x))
        )

    def get_value(self, emf: float) -> float:
        """Получить значение (температуру в °C или ЭДС в mV)"""
        try:
            return self._calculate(emf)
        except Exception as e:
            raise ValueError(
                f"Ошибка при вычислении температуры для ЭДС {emf} мВ: {str(e)}"
            )
