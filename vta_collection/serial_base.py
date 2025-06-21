import serial
import serial.tools.list_ports
from loguru import logger as log


def get_serial_ports():
    return [port.device for port in serial.tools.list_ports.comports()]


class SerialWorker:
    endchar = b"\n"

    def __init__(self, baudrate, bytesize, parity, stopbits, timeout, dsrdtr, rtscts):
        # super().__init__()
        self.ser = serial.Serial(
            baudrate=baudrate,
            timeout=timeout,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            dsrdtr=dsrdtr,
            rtscts=rtscts,
        )
        self._is_running = False

    def open_serial(self, port: str):
        if not self.ser.is_open:
            log.info(f"Opening serial on {port} port...")
            self.ser.port = port
            self.ser.open()

    def close_serial(self):
        if self.ser.is_open:
            self.ser.close()
            log.info(f"Serial on {self.ser.port} port closed")

    def read_serial_str(self):
        return self.read_serial().decode().strip()

    def read_serial(self):
        # while True:
        #     in_waiting = self.ser.in_waiting
        #     if in_waiting > 0:
        #         data = self.ser.read(in_waiting)
        #         return data
        #     else:
        #         break
        # return self.ser.readline()
        return self.ser.read_until(expected=self.endchar)

    def write_serial(self, cmd: bytes):
        self.ser.reset_input_buffer()
        self.ser.write(cmd + self.endchar)
