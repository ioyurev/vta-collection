from typing import Optional

import numpy as np

from vta_collection.config import config
from vta_collection.math_utils import bisection_method


class Thermocouple:
    """Термопара для преобразования ЭДС в температуру по полиномиальной формуле"""

    def __init__(self, coefficients: list[float]):
        """
        Инициализация термопары с коэффициентами полинома.

        Args:
            coefficients: Список коэффициентов [c0, c1, c2, ..., c8]
                         для формулы T(E) = c0 + c1*E + c2*E² + ... + c8*E⁸
                         Коэффициенты упорядочены от c0 (константа) до c8 (старшая степень)
        """
        self.coefficients = coefficients
        self.poly_coeffs = self.coefficients[::-1]

    def emf_to_temperature(self, emf: float) -> float:
        """
        Преобразование ЭДС в температуру по полиномиальной формуле.
        Использует numpy.polyval для эффективного вычисления полинома.

        Args:
            emf: ЭДС в мВ

        Returns:
            Температура в °C
        """
        # numpy.polyval ожидает коэффициенты от старшей степени к константе
        # Поэтому переворачиваем список коэффициентов

        return float(np.polyval(self.poly_coeffs, emf))

    def temperature_to_emf(self, target_temp: float) -> float:
        """
        Вычисление ЭДС по температуре методом бисекции.

        Args:
            target_temp: Целевая температура в °C

        Returns:
            ЭДС в мВ

        Raises:
            ValueError: Если метод не сошелся за максимальное число итераций
        """
        # Диапазон поиска для термопары A-1
        left = -1.0  # -1 мВ
        right = 5.0  # 5 мВ

        # Точность вычисления
        tolerance = 1e-4

        # Используем универсальную функцию бисекции
        def temp_func(emf: float) -> float:
            return self.emf_to_temperature(emf)

        return bisection_method(
            func=temp_func,
            target_value=target_temp,
            left=left,
            right=right,
            tolerance=tolerance,
            max_iterations=100,
        )


_thermocouple: Optional[Thermocouple] = None


def get_thermocouple() -> Thermocouple:
    """Получить экземпляр Thermocouple (singleton)"""
    global _thermocouple
    if _thermocouple is None:
        _thermocouple = Thermocouple(config.thermocouple_coefficients)
    return _thermocouple
