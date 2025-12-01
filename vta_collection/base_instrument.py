from loguru import logger as log

from vta_collection.config import config
from vta_collection.serial_base import SerialWorker


class BaseInstrument(SerialWorker):
    modelname: str

    def __init__(
        self,
        baudrate,
        bytesize,
        parity,
        stopbits,
        timeout=None,
        dsrdtr=False,
        rtscts=False,
    ):
        super().__init__(
            baudrate=baudrate,
            timeout=timeout,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            dsrdtr=dsrdtr,
            rtscts=rtscts,
        )
        self.found = False

        # В тестовом режиме переопределяем метод send_command
        if config.is_test_mode:
            self.send_command = self._test_mode_send_command

    def _test_mode_send_command(self, cmd: bytes, logging_answer: bool = False) -> str:
        log.debug(f"{self.modelname}: Test mode - would send command: {cmd!r}")
        raise Exception(
            f"Hardware communication disabled in test mode. Would send: {cmd!r}"
        )

    def send_command(self, cmd: bytes, logging_answer: bool = False) -> str:
        log.info(f"{self.modelname}: Send command: {cmd!r}")
        answer = self.get_str_answer(cmd=cmd)
        if logging_answer:
            log.info(f"{self.modelname}: Answer: {answer}")
        return answer

    def get_bytes_answer(self, cmd: bytes):
        self.write_serial(cmd=cmd)
        return self.read_serial()

    def get_str_answer(self, cmd: bytes):
        self.write_serial(cmd=cmd)
        return self.read_serial_str()
