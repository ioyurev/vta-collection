from typing import TYPE_CHECKING

from vta_collection.adam_4011_config import Adam4011Config
from vta_collection.adam_base import AdamBase, AdamBaseCommands

if TYPE_CHECKING:
    from vta_collection.adam_4520 import Adam4520API


class Adam4011Commands(AdamBaseCommands):
    def __init__(self, address: bytes):
        super().__init__(address=address)

        self.GET_INPUT = b"#AA".replace(b"AA", address)
        self.GET_SYNC_DATA = b"$AA4".replace(b"AA", address)
        self.SPAN_CALIBRATION = b"$AA0".replace(b"AA", address)
        self.OFFSET_CALIBRATION = b"$AA1".replace(b"AA", address)
        self.CJC_STATUS = b"$AA3".replace(b"AA", address)

        self.CJC_CALIBRATION = b"$AA9SNNNN".replace(b"AA", address)


class Adam4011(AdamBase):
    model = "4011"
    name: str
    config: Adam4011Config

    def __init__(self, converter: "Adam4520API", address: int = 1):
        super().__init__(converter=converter, address=address)
        self.CMD = Adam4011Commands(self.address)

    def get_sync_data(self):
        return self.converter.get_bytes_answer(self.CMD.GET_SYNC_DATA)

    def get_sync_data_f(self):
        return self.parse_sync_data(self.get_sync_data())

    def get_cjc_status(self):
        return self.converter.send_command(cmd=self.CMD.CJC_STATUS)

    def get_data(self):
        return self.parse_data(data=self.get_data_bytes())

    def get_data_bytes(self):
        return self.converter.get_bytes_answer(cmd=self.CMD.GET_DATA)

    def parse_data(self, data: bytes):
        return float(data.decode("ascii").strip()[2:])

    def parse_sync_data(self, data: bytes):
        return float(data.decode("ascii").strip()[5:])
