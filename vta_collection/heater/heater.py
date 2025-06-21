from typing import TYPE_CHECKING

from vta_collection.config import config

if TYPE_CHECKING:
    from vta_collection.heater.loop import AbstractLoop


class Heater:
    def __init__(self, loop: "AbstractLoop"):
        self.loop = loop
        self.output = 0.0
        self.t0 = 0.0
        self.enabled = False
        self.heat_speed = config.default_speed / 1000  # [mV/s]

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def set_speed(self, value: int):
        self.heat_speed = value / 1000

    def heatup(self, last_t: float):
        if self.enabled:
            self.output += self.heat_speed * (last_t - self.t0)
            self.t0 = last_t
            self.loop.set_output(value=self.output)

    def reset(self):
        self.output = 0.0
