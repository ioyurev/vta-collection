from typing import TYPE_CHECKING

from vta_collection.adam_4011_config import Adam4011Config

if TYPE_CHECKING:
    from vta_collection.adam_4520 import Adam4520API


class AdamBaseCommands:
    def __init__(self, address: bytes):
        self.GET_CONF_STATUS = b"$AA2".replace(b"AA", address)
        self.GET_FIRM_VER = b"$AAF".replace(b"AA", address)
        self.GET_NAME = b"$AAM".replace(b"AA", address)
        self.GET_DATA = b"#AA".replace(b"AA", address)
        self.GET_SYNC_DATA = b"$AA4".replace(b"AA", address)
        self.SPAN_CALIBRATION = b"$AA0".replace(b"AA", address)
        self.OFFSET_CALIBRATION = b"$AA1".replace(b"AA", address)
        self.CJC_STATUS = b"$AA3".replace(b"AA", address)

        self.SET_CONF_STATUS = b"%AANNTTCCFF".replace(b"AA", address)
        self.CJC_CALIBRATION = b"$AA9SNNNN".replace(b"AA", address)


class AdamBase:
    model: str
    CMD: AdamBaseCommands

    def __init__(self, converter: "Adam4520API", address: int = 1):
        self.converter = converter
        self.address = f"{address:02d}".encode("ascii")

    def check_identity(self) -> bool:
        return self.model in self.get_name()

    def get_conf_status(self):
        return self.converter.send_command(
            cmd=self.CMD.GET_CONF_STATUS, logging_answer=True
        )

    def get_name(self):
        return self.converter.send_command(cmd=self.CMD.GET_NAME, logging_answer=True)

    def setup(self):
        self.config = Adam4011Config.from_str(string=self.get_conf_status())
        self.name = self.get_name()
