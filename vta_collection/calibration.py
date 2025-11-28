import json
import math
from io import TextIOWrapper
from typing import Optional

from pydantic import BaseModel, field_validator

from vta_collection.config import config


class Calibration(BaseModel):
    c0: float = config.c0
    c1: float = config.c1
    c2: float = config.c2
    c3: float = config.c3
    name: Optional[str] = None
    description: str = ""

    @field_validator("c0", "c1", "c2", "c3")
    @classmethod
    def validate_coefficients(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Коэффициент не может быть NaN или бесконечностью")
        return v

    def get_value(self, x: float) -> float:
        return self.c3 * x**3 + self.c2 * x**2 + self.c1 * x + self.c0

    def to_formule_str(self) -> str:
        return f"T(E) = {self.c0} + {self.c1} * E + {self.c2} * E² + {self.c3} * E³"

    def to_file(self, f: TextIOWrapper):
        content = self.model_dump()
        json.dump(obj=content, fp=f)

    @classmethod
    def from_dict(cls, data: dict) -> "Calibration":
        """Создать Calibration из словаря данных с валидацией коэффициентов"""
        return cls.model_validate(data)
