from typing import List

import numpy as np

from vta_collection.standard import Standard


def calculate_coefficients(
    standards: List[Standard], calibration_type: str
) -> List[float]:
    """Рассчитать коэффициенты калибровки из стандартов"""
    if len(standards) < 2:
        raise ValueError("Для расчета коэффициентов требуется минимум 2 стандарта")

    if calibration_type not in ("linear", "quadratic"):
        raise ValueError("Тип калибровки должен быть 'linear' или 'quadratic'")

    # Собираем данные
    t_exp = np.array([s.t_exp for s in standards])
    delta_t = np.array([s.t_theor - s.t_exp for s in standards])

    if calibration_type == "linear":
        # delta_t = a * t_exp + b
        coeffs = np.polyfit(t_exp, delta_t, 1)
        return [float(coeffs[0]), float(coeffs[1]), 0.0]
    else:  # quadratic
        # delta_t = a * t_exp^2 + b * t_exp + c
        coeffs = np.polyfit(t_exp, delta_t, 2)
        return [float(coeffs[0]), float(coeffs[1]), float(coeffs[2])]
