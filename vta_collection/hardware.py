from typing import Optional

from vta_collection.adam_4011 import Adam4011
from vta_collection.adam_4021 import Adam4021
from vta_collection.adam_4520 import Adam4520
from vta_collection.config import config
from vta_collection.serial_base import get_serial_ports


def validate_com_port():
    ports = get_serial_ports()
    if config.comport not in ports:
        raise Exception(
            f"COM port '{config.comport}' is not available. Available ports: {ports}"
        )


class Hardware:
    def __init__(self) -> None:
        self.found = False
        self.adam4520 = Adam4520()
        self.adam4011 = Adam4011(
            converter=self.adam4520, address=config.adam4011_address
        )
        self.adam4021 = Adam4021(
            converter=self.adam4520, address=config.adam4021_address
        )
        self.adam4520.modules = (self.adam4011, self.adam4021)

    def find(self):
        if not config.is_test_mode:
            if not self.adam4520.found:
                validate_com_port()
                self.adam4520.find_on_port(port=config.comport)
                self.found = True


_hardware: Optional[Hardware] = None


def get_hardware(auto_find: bool = False) -> Hardware:
    """Получить экземпляр Hardware (singleton)"""
    global _hardware
    if _hardware is None:
        _hardware = Hardware()
    if auto_find and not _hardware.found:
        _hardware.find()
    return _hardware
