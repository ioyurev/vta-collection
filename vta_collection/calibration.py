import math
from typing import Dict

import numpy as np
from loguru import logger as log
from numpy.polynomial.polynomial import polyval
from pydantic import BaseModel, field_validator

from vta_collection.calibration_utils import calculate_coefficients
from vta_collection.serializable import SerializableMixin
from vta_collection.standard import Standard


class Calibration(BaseModel, SerializableMixin):
    calibration_type: str = "linear"  # "linear" или "quadratic"
    coefficients: list[float] = [0.0, 0.0, 0.0]  # [a, b, c] для коррекции температуры
    name: str = ""
    description: str = ""
    standards: list[Standard] = []  # Стандарты для расчета коэфициентов

    @field_validator("calibration_type")
    @classmethod
    def validate_calibration_type(cls, v: str) -> str:
        if v not in ("linear", "quadratic"):
            raise ValueError("Тип калибровки должен быть 'linear' или 'quadratic'")
        return v

    @field_validator("coefficients")
    @classmethod
    def validate_coefficients(cls, v: list[float]) -> list[float]:
        if not v:
            raise ValueError("Коэффициенты не могут быть пустыми")

        for coeff in v:
            if math.isnan(coeff) or math.isinf(coeff):
                raise ValueError("Коэффициент не может быть NaN или бесконечностью")

        # Дополняем нулями до нужной длины
        while len(v) < 3:
            v.append(0.0)

        return v

    def get_value(self, t_exp: float) -> float:
        """Получить скорректированную температуру

        Args:
            t_exp: Экспериментальная температура в °C

        Returns:
            Скорректированная температура в °C
        """
        # Используем polyval для вычисления полинома
        # Коэффициенты в polyval идут в порядке: [c0, c1, c2, ...] для полинома c0 + c1*x + c2*x^2 + ...
        if self.calibration_type == "linear":
            if len(self.coefficients) < 2:
                raise ValueError(
                    "Недостаточно коэффициентов для линейной калибровки (требуется минимум 2)"
                )
            # Разворачиваем коэффициенты для линейного случая: [b, a] для ax + b
            poly_coeffs = self.coefficients[1::-1]  # [coefficients[1], coefficients[0]]
        else:  # quadratic
            if len(self.coefficients) < 3:
                raise ValueError(
                    "Недостаточно коэффициентов для квадратичной калибровки (требуется минимум 3)"
                )
            # Разворачиваем коэфициенты для квадратичного случая: [c, b, a] для ax^2 + bx + c
            poly_coeffs = self.coefficients[
                2::-1
            ]  # [coefficients[2], coefficients[1], coefficients[0]]

        delta_t = float(polyval(t_exp, poly_coeffs))
        return t_exp + delta_t

    def to_formule_str(self) -> str:
        """Получить строковое представление формулы калибровки"""
        if self.calibration_type == "linear":
            a, b = self.coefficients[0], self.coefficients[1]
            return f"Tскор = Tэксп + ({a:.3f}) * Tэксп + ({b:.3f})"
        else:
            a, b, c = self.coefficients[0], self.coefficients[1], self.coefficients[2]
            return f"Tскор = Tэксп + ({a:.3f}) * Tэксп² + ({b:.3f}) * Tэксп + ({c:.3f})"

    def update_from_standards(self):
        """Обновить коэффициенты на основе стандартов"""
        log.debug(
            f"Расчет коэфициентов для калибровки '{self.name}', тип: {self.calibration_type}, стандарты: {self.standards}"
        )
        self.coefficients = calculate_coefficients(
            self.standards, self.calibration_type
        )
        log.debug(f"Коэффициенты рассчитаны: {self.coefficients}")

    def calculate_statistics(self) -> Dict[str, float]:
        """Рассчитать статистику калибровки"""
        if len(self.standards) < 2:
            raise ValueError("Для расчета статистики требуется минимум 2 стандарта")

        # Получаем экспериментальные и теоретические температуры
        t_exp = np.array([s.t_exp for s in self.standards])
        t_theor = np.array([s.t_theor for s in self.standards])

        # Рассчитываем разницу (t_theor - t_exp) для каждого стандарта
        delta_t_actual = t_theor - t_exp

        # Рассчитываем подогнанную разницу по калибровочной кривой с использованием polyval
        if self.calibration_type == "linear":
            # Разворачиваем коэффициенты для линейного случая: [b, a] для ax + b
            poly_coeffs = self.coefficients[1::-1]  # [coefficients[1], coefficients[0]]
        else:  # quadratic
            # Разворачиваем коэффициенты для квадратичного случая: [c, b, a] для ax^2 + bx + c
            poly_coeffs = self.coefficients[
                2::-1
            ]  # [coefficients[2], coefficients[1], coefficients[0]]

        # Векторизованное вычисление с использованием polyval
        delta_t_fit = polyval(t_exp, poly_coeffs)

        # Рассчитываем остатки: разница между фактической и подогнанной разницей
        residuals = delta_t_actual - delta_t_fit

        # Сумма квадратов остатков
        SS_res = np.sum(residuals**2)

        # Общая сумма квадратов
        delta_t_mean = np.mean(delta_t_actual)
        SS_tot = np.sum((delta_t_actual - delta_t_mean) ** 2)

        # Количество точек и параметров
        n = len(self.standards)
        p = (
            2 if self.calibration_type == "linear" else 3
        )  # линейная: 2 параметра, квадратичная: 3 параметра

        # Стандартная ошибка калибровки (SEC)
        if n > p:
            SEC = np.sqrt(SS_res / (n - p))
        else:
            SEC = 0.0

        # Коэффициент детерминации R²
        if SS_tot != 0:
            R_squared = 1 - (SS_res / SS_tot)
        else:
            R_squared = 1.0

        # Расширенная неопределенность (k = 2)
        expanded_uncertainty = 2 * SEC

        # Максимальная абсолютная погрешность
        max_abs_error = np.max(np.abs(residuals)) if len(residuals) > 0 else 0.0

        return {
            "R_squared": float(R_squared),
            "SEC": float(SEC),
            "expanded_uncertainty": float(expanded_uncertainty),
            "max_abs_error": float(max_abs_error),
            "SS_res": float(SS_res),
            "SS_tot": float(SS_tot),
            "residuals": residuals.tolist(),
            "delta_t_actual": delta_t_actual.tolist(),
            "delta_t_fit": delta_t_fit.tolist(),
            "n_points": n,
            "n_params": p,
        }


class ZeroCalibration(Calibration):
    """Специальная калибровка, которая не применяет коррекцию (возвращает исходное значение)"""

    def __init__(self):
        super().__init__(
            calibration_type="linear",
            coefficients=[0.0, 0.0, 0.0],  # Нулевые коэффициенты - без коррекции
            name="ZeroCalibration",
            description="Нулевая калибровка (без коррекции)",
            standards=[],
        )

    def get_value(self, t_exp: float) -> float:
        """Возвращает неизмененную температуру (без коррекции)"""
        return t_exp

    def to_formule_str(self) -> str:
        """Получить строковое представление формулы калибровки"""
        return "Tскор = Tэксп (без калибровки)"
