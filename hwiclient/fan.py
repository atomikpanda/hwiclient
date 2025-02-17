from bisect import bisect_left
from datetime import timedelta

from .commands.dimmer import FadeDimmer
from .commands.hub import HubCommand
from .dimmer import DimmerDevice, DimmerDeviceType


class FanDimmerType(DimmerDeviceType):
    def __init__(self, fan_speeds: int):
        # fan_speeds = 4
        # Patio Fan
        # fan_speeds = 6
        self._fan_speeds = fan_speeds

    @classmethod
    def type_id(cls) -> str:
        return "FAN"

    @property
    def fan_speeds(self) -> int:
        return self._fan_speeds

    @property
    def is_dimmable(self) -> bool:
        return True

    def set_level_command(self, dimmer: DimmerDevice, level: float) -> HubCommand:
        return SetFanLevel(dimmer, self._fan_speeds, level)


class SetFanLevel(FadeDimmer):
    def __init__(self, dimmer: DimmerDevice, fan_speeds: int, level: float):
        assert dimmer.device_type.type_id() == FanDimmerType.type_id()
        super().__init__(
            self._safe_fan_level(fan_speeds, level),
            timedelta(),
            timedelta(),
            dimmer.address,
        )

    def _safe_fan_level(self, num_speeds_excluding_zero: int, level: float):
        increment = 100.0 / float(num_speeds_excluding_zero)
        safe_speeds = []
        for i in range(0, int(num_speeds_excluding_zero) + 1):
            safe_speeds.append(increment * i)

        return self._take_closest(safe_speeds, level)

    def _take_closest(self, brackets: list[float], number: float):
        """
        Assumes brackets is sorted. Returns closest value to number.

        If two numbers are equally close, return the smallest number.
        """
        pos = bisect_left(brackets, number)
        if pos == 0:
            return brackets[0]
        if pos == len(brackets):
            return brackets[-1]
        before = brackets[pos - 1]
        after = brackets[pos]
        if after - number < number - before:
            return after
        else:
            return before

    # def _safe_fan_brightness_legacy(brightness_percent):

    #     if brightness_percent < 20:
    #         return 0  # off
    #     elif brightness_percent >= 20 and brightness_percent < 40:
    #         return 25  # low
    #     elif brightness_percent >= 40 and brightness_percent < 60:
    #         return 50  # med
    #     elif brightness_percent >= 60 and brightness_percent < 80:
    #         return 75  # med high
    #     elif brightness_percent >= 80 and brightness_percent <= 110:
    #         return 100  # high
    #     else:
    #         return 0
