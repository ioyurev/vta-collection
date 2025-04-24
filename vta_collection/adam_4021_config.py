from enum import Enum
from typing import NamedTuple


class ORC(Enum):
    C30 = "30"
    C31 = "31"
    C32 = "32"

    def description(self):
        return INPUTRANGE_CODES[self]


INPUTRANGE_CODES: dict[ORC, str] = {
    ORC.C30: "0 to 20 mA",
    ORC.C31: "4 to 20 mA",
    ORC.C32: "0 to 10 V",
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

    def description(self):
        return DATAFORMAT_CODES[self]


DATAFORMAT_CODES: dict[DFC, str] = {
    DFC.C00: "Engineering units",
    DFC.C01: "% of FSR",
    DFC.C10: "hexadecimal",
}


class SRC(Enum):
    C0000 = "0000"
    C0001 = "0001"
    C0010 = "0010"
    C0011 = "0011"
    C0100 = "0100"
    C0101 = "0101"
    C0110 = "0110"
    C0111 = "0111"
    C1000 = "1000"
    C1001 = "1001"
    C1010 = "1010"
    C1011 = "1011"

    def description(self):
        return SLEW_RATE_CODES[self]


SLEW_RATE_CODES: dict[SRC, str] = {
    SRC.C0000: "Immediate change",
    SRC.C0001: "0.0625 V/sec 0.125 mA/sec",
    SRC.C0010: "0.125 V/sec 0.250 mA/sec",
    SRC.C0011: "0.250 V/sec 0.500 mA/sec",
    SRC.C0100: "0.500 V/sec 1.000 mA/sec",
    SRC.C0101: "1.000 V/sec 2.000 mA/sec",
    SRC.C0110: "2.000 V/sec 4.000 mA/sec",
    SRC.C0111: "4.000 V/sec 8.000 mA/sec",
    SRC.C1000: "8.000 V/sec 16.00 mA/sec",
    SRC.C1001: "16.00 V/sec 32.00 mA/sec",
    SRC.C1010: "32.00 V/sec 64.00 mA/sec",
    SRC.C1011: "64.00 V/sec 128.0 mA/sec",
}


class Codes:
    OutputRange = ORC
    Baudrate = BC
    Checksum = CC
    SlewRate = SRC
    DataFormat = DFC


class Adam4021Config(NamedTuple):
    address: str
    new_address: str
    output_range: ORC
    baudrate: BC
    checksum: CC
    slewrate: SRC
    data_format: DFC

    def to_set_cmd(self):
        cmd_template = "%AANNTTCCFF"
        ff = list("00000000")

        cmd = (
            cmd_template.replace("AA", self.address)
            .replace("NN", self.new_address)
            .replace("TT", self.output_range.value)
            .replace("CC", self.baudrate.value)
        )

        # Формирование битовых флагов
        ff[0:2] = list(self.data_format.value)[::-1]
        ff[2:6] = list(self.slewrate.value)[::-1]
        ff[6] = self.checksum.value
        # ff[7] = self.integration_time.value
        ff = int("".join(ff[::-1]), 2)
        cmd = cmd.replace("FF", f"{ff:02X}")

        return bytes(cmd, encoding="ascii")

    @staticmethod
    def from_str(string: str):
        is_set_cmd = string.startswith("%")
        string = string[1:]
        codes = [string[i : i + 2] for i in range(0, len(string), 2)]

        if is_set_cmd:
            address_str, new_address_str, output_range_code, baudrate_code, bits = codes
        else:
            address_str, output_range_code, baudrate_code, bits = codes
            new_address_str = address_str

        address = int(address_str, 16)
        new_address = int(new_address_str, 16)
        bits = format(int(bits, 16), "08b")[::-1]
        checksum_bit = bits[6]
        slewrate_bits = bits[5] + bits[4] + bits[3] + bits[2]
        dataformat_bits = bits[1] + bits[0]

        return Adam4021Config(
            address=f"{address:02X}",
            new_address=f"{new_address:02X}",
            output_range=ORC(output_range_code),
            baudrate=BC(baudrate_code),
            slewrate=SRC(slewrate_bits),
            checksum=CC(checksum_bit),
            data_format=DFC(dataformat_bits),
        )

    def __str__(self):
        return f"""AdamConfig(
    address = {self.address},
    new_address = {self.new_address},
    output_range = {self.output_range.value}: {self.output_range.description()},
    baudrate = {self.baudrate.value}: {self.baudrate.description()},
    slewrate = {self.slewrate.value}: {self.slewrate.description()},
    checksum = {self.checksum.value}: {self.checksum.description()},
    dataformat = {self.data_format.value}: {self.data_format.description()}
    )"""


if __name__ == "__main__":
    cfg = Adam4021Config.from_str("%310A310610")  # #!AATTCCFF '%AANNTTCCFF'
    print(cfg)
    print(cfg.to_set_cmd())
