import serial
from loguru import logger as log

from vta_collection.adam_4011 import Adam4011
from vta_collection.adam_4021 import Adam4021
from vta_collection.base_instrument import BaseInstrument
from vta_collection.config import config


class ModulesNotFound(Exception):
    pass


class Adam4520API(BaseInstrument):
    modelname = "4520"
    endchar = b"\r"
    modules: tuple[Adam4011, Adam4021]

    def __init__(self, timeout: float | None):
        if timeout is None:
            timeout = 0.1
        super().__init__(
            baudrate=config.adam_baudrate,
            timeout=timeout,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            rtscts=False,
            dsrdtr=True,
        )

    def find_on_port(self, port: str):
        self.open_serial(port=port)
        self.found = self.modules_check_identity()
        if not self.found:
            self.close_serial()
            raise ModulesNotFound(f"{self.modelname}: not found {self.modules}")
        else:
            log.info(f"{self.modelname}: found {self.modules}")

        return self.found

    def modules_check_identity(self):
        return all(mod.check_identity() for mod in self.modules)

    def modules_get_conf(self):
        return tuple(mod.config for mod in self.modules)

    def modules_setup(self):
        for mod in self.modules:
            mod.setup()


class Adam4520(Adam4520API):
    def __init__(self, timeout: float | None = None):
        super().__init__(timeout=timeout)

    def setup(self):
        self.modules_setup()
        log.info(f"{self.modelname} is set for work")


# if __name__ == '__main__':
#     app = QApplication()
#     adam = Adam4520()
#     adam.find_on_port('COM4')
#     # adam.setup()
#     # adam.data_ready.connect(print)
#     # adam.data_ready.connect(Adam4520.parse_data)
#     app.exec()
