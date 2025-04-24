from enum import Enum
from typing import NamedTuple


class IRC(Enum):
    C00 = "00"
    C01 = "01"
    C02 = "02"
    C03 = "03"
    C04 = "04"
    C05 = "05"
    C06 = "06"
    C07 = "07"
    C0E = "0E"
    C0F = "0F"
    C10 = "10"
    C11 = "11"
    C12 = "12"
    C13 = "13"
    C14 = "14"

    def description(self):
        return INPUTRANGE_CODES[self]


INPUTRANGE_CODES: dict[IRC, str] = {
    IRC.C00: "± 15 mV",
    IRC.C01: "± 50 mV",
    IRC.C02: "± 100 mV",
    IRC.C03: "± 500 mV",
    IRC.C04: "± 1 V",
    IRC.C05: "± 2.5 V",
    IRC.C06: "20 mA",
    IRC.C07: "4~20mA",
    IRC.C0E: "Type J Thermocouple 0 - 760 °C",
    IRC.C0F: "Type K Thermocouple 0 - 1370 °C",
    IRC.C10: "Type T Thermocouple 100 - 400 °C",
    IRC.C11: "Type E Thermocouple 0 - 1000 °C",
    IRC.C12: "Type R Thermocouple 500 - 1750 °C",
    IRC.C13: "Type S Thermocouple 500 - 1750 °C",
    IRC.C14: "Type B Thermocouple 500 - 1800 °C",
}


class BC(Enum):
    C03 = "03"
    C04 = "04"
    C05 = "05"
    C06 = "06"
    C07 = "07"
    C08 = "08"

    def description(self):
        return BAUDRATE_CODES[self]


BAUDRATE_CODES: dict[BC, int] = {
    BC.C03: 1200,
    BC.C04: 2400,
    BC.C05: 4800,
    BC.C06: 9600,
    BC.C07: 19200,
    BC.C08: 38400,
}


class ITC(Enum):
    C0 = "0"
    C1 = "1"

    def description(self):
        return INTEGRATIONTIME_CODES[self]


INTEGRATIONTIME_CODES: dict[ITC, str] = {
    ITC.C0: "50 ms (Operation under 60 Hz power)",
    ITC.C1: "60 ms (Operation under 50 Hz power)",
}


class CC(Enum):
    C0 = "0"
    C1 = "1"

    def description(self):
        return CHECKSUM_CODES[self]


CHECKSUM_CODES: dict[CC, str] = {
    CC.C0: "Disabled",
    CC.C1: "Enabled",
}


class DFC(Enum):
    C00 = "00"
    C01 = "01"
    C10 = "10"
    C11 = "11"

    def description(self):
        return DATAFORMAT_CODES[self]


DATAFORMAT_CODES: dict[DFC, str] = {
    DFC.C00: "Engineering units",
    DFC.C01: "% of FSR",
    DFC.C10: "two's complement of hexadecimal",
    DFC.C11: "Ohms (for 4013 and 4015)",
}


class Codes:
    InputRange = IRC
    Baudrate = BC
    IntegrationTime = ITC
    Checksum = CC
    DataFormat = DFC


class Adam4011Config(NamedTuple):
    address: str
    new_address: str
    input_range: IRC
    baudrate: BC
    integration_time: ITC
    checksum: CC
    data_format: DFC

    def to_set_cmd(self):
        cmd_template = "%AANNTTCCFF"
        ff = list("00000000")

        cmd = (
            cmd_template.replace("AA", self.address)
            .replace("NN", self.new_address)
            .replace("TT", self.input_range.value)
            .replace("CC", self.baudrate.value)
        )

        # Формирование битовых флагов
        ff[0:2] = list(self.data_format.value)[::-1]
        ff[6] = self.checksum.value
        ff[7] = self.integration_time.value
        ff = int("".join(ff[::-1]), 2)
        cmd = cmd.replace("FF", f"{ff:02X}")

        return bytes(cmd, encoding="ascii")

    @staticmethod
    def from_str(string: str):
        is_set_cmd = string.startswith("%")
        string = string[1:]
        codes = [string[i : i + 2] for i in range(0, len(string), 2)]

        if is_set_cmd:
            address_str, new_address_str, input_range_code, baudrate_code, bits = codes
        else:
            address_str, input_range_code, baudrate_code, bits = codes
            new_address_str = address_str

        address = int(address_str, 16)
        new_address = int(new_address_str, 16)
        bits = format(int(bits, 16), "08b")[::-1]
        checksum_bit = bits[6]
        integration_time_bit = bits[7]
        dataformat_bits = bits[1] + bits[0]

        return Adam4011Config(
            address=f"{address:02d}",
            new_address=f"{new_address:02d}",
            input_range=IRC(input_range_code),
            baudrate=BC(baudrate_code),
            integration_time=ITC(integration_time_bit),
            checksum=CC(checksum_bit),
            data_format=DFC(dataformat_bits),
        )

    def __str__(self):
        return f"""AdamConfig(
    address = {self.address},
    new_address = {self.new_address},
    input_range = {self.input_range.value}: {self.input_range.description()},
    baudrate = {self.baudrate.value}: {self.baudrate.description()},
    integration_time = {self.integration_time.value}: {self.integration_time.description()},
    checksum = {self.checksum.value}: {self.checksum.description()},
    dataformat = {self.data_format.value}: {self.data_format.description()}
    )"""


if __name__ == "__main__":
    cfg = Adam4011Config.from_str("!010206C3")  # #!AATTCCFF '%AANNTTCCFF'
    print(cfg)
    print(cfg.to_set_cmd())
