from datetime import timedelta
from .dimmer import DimmerDeviceType, DimmerDevice
from .commands.dimmer import FadeDimmer
from .commands.hub import SessionActionCommand

class SwitchDimmerType(DimmerDeviceType):
    @classmethod
    def type_id(cls) -> str:
        return "SWITCH"

    @property
    def is_dimmable(self) -> bool:
        return False

    def set_level_command(self, dimmer: DimmerDevice, level: float) -> SessionActionCommand:
        if level > 0:
            return FadeDimmer(100, timedelta(), timedelta(), dimmer.address)
        else:
            return FadeDimmer(0, timedelta(), timedelta(), dimmer.address)
