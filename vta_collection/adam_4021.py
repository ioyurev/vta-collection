from typing import TYPE_CHECKING

from vta_collection.adam_4021_config import Adam4021Config
from vta_collection.adam_base import AdamBase, AdamBaseCommands

if TYPE_CHECKING:
    from vta_collection.adam_4520 import Adam4520API


class Adam4021Commands(AdamBaseCommands):
    def __init__(self, address):
        super().__init__(address)

        self.SET_OUTPUT = b"#AA".replace(b"AA", address)
        self.CURRENT_OUTPUT = b"$AA8".replace(b"AA", address)


class Adam4021(AdamBase):
    model = "4021"
    name: str
    CMD: Adam4021Commands

    def __init__(self, converter: "Adam4520API", address: int = 1):
        super().__init__(converter=converter, address=address)
        self.CMD = Adam4021Commands(self.address)

    def set_output(self, value: float):
        value += 0.001
        cmd = self.CMD.SET_OUTPUT + f"{value:06.3f}".encode()
        answer = self.converter.get_bytes_answer(cmd=cmd)
        return answer

    def meas_output(self):
        return self.converter.get_bytes_answer(self.CMD.CURRENT_OUTPUT)

    def setup(self):
        super().setup()
        self.config = Adam4021Config.from_str(string=self.get_conf_status())
        self.set_output(value=0.0)
