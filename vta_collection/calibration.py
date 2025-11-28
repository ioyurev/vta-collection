import json
from dataclasses import dataclass
from io import TextIOWrapper
from typing import Optional

from vta_collection.config import config


@dataclass
class Calibration:
    c0: float = config.c0
    c1: float = config.c1
    c2: float = config.c2
    c3: float = config.c3
    name: Optional[str] = None
    description: str = ""

    def get_value(self, x: float):
        return self.c3 * x**3 + self.c2 * x**2 + self.c1 * x + self.c0

    def to_formule_str(self):
        return f"T(E) = {self.c0} + {self.c1} * E + {self.c2} * E² + {self.c3} * E³"

    def to_file(self, f: TextIOWrapper):
        content = {
            "name": self.name,
            "description": self.description,
            "c0": self.c0,
            "c1": self.c1,
            "c2": self.c2,
            "c3": self.c3,
        }
        json.dump(obj=content, fp=f)
