from typing import Callable


def bisection_method(
    func: Callable[[float], float],
    target_value: float,
    left: float,
    right: float,
    tolerance: float = 1e-4,
    max_iterations: int = 100,
) -> float:
    """Универсальная функция для метода бисекции"""
    for _ in range(max_iterations):
        mid = (left + right) / 2
        current_value = func(mid)

        if abs(current_value - target_value) < tolerance:
            return mid

        if current_value < target_value:
            left = mid
        else:
            right = mid

    raise ValueError(
        f"Метод бисекции не сошелся за {max_iterations} итераций для целевого значения {target_value}"
    )
