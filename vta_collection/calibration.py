import json
from dataclasses import dataclass
from io import TextIOWrapper

from vta_collection.config import config


@dataclass
class Calibration:
    c0: float = config.c0
    c1: float = config.c1
    c2: float = config.c2
    c3: float = config.c3

    def get_value(s, x: float):
        return s.c3 * x**3 + s.c2 * x**2 + s.c1 * x + s.c0

    def to_formule_str(s):
        return f"T(E) = {s.c0} + {s.c1} * E + {s.c2} * E² + {s.c3} * E³"

    def to_file(self, f: TextIOWrapper):
        content = {
            "c0": self.c0,
            "c1": self.c1,
            "c2": self.c2,
            "c3": self.c3,
        }
        json.dump(obj=content, fp=f)
