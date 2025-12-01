from typing import Optional

from vta_collection.adam_4011 import Adam4011
from vta_collection.adam_4021 import Adam4021
from vta_collection.adam_4520 import Adam4520
from vta_collection.config import config


class Hardware:
    def __init__(self) -> None:
        self.adam4520 = Adam4520()
        self.adam4011 = Adam4011(
            converter=self.adam4520, address=config.adam4011_address
        )
        self.adam4021 = Adam4021(
            converter=self.adam4520, address=config.adam4021_address
        )
        self.adam4520.modules = (self.adam4011, self.adam4021)


_hardware: Optional[Hardware] = None


def get_hardware() -> Hardware:
    """Получить экземпляр Hardware (singleton)"""
    global _hardware
    if _hardware is None:
        _hardware = Hardware()
    return _hardware
