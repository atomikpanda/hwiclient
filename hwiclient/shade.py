
from __future__ import annotations
from datetime import timedelta
from .dimmer import DimmerDevice, DimmerDeviceType
from .commands.hub import HubActionCommand
from .commands.dimmer import FadeDimmer

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .hub import Hub

class ShadeDimmerType(DimmerDeviceType):
    @property
    def type_id(self) -> str:
        return "QED SHADE"

    @property
    def is_dimmable(self) -> bool:
        return True

    def set_level_command(self, dimmer: DimmerDevice, level: float) -> HubActionCommand:
        return SetShadePosition(dimmer, level)
    
    def open_shade(self, dimmer: DimmerDevice) -> HubActionCommand:
        return OpenShade(dimmer)
    
    def close_shade(self, dimmer: DimmerDevice) -> HubActionCommand:
        return CloseShade(dimmer)


class SetShadePosition(HubActionCommand):
    """Sets the current position of cover where 0 means closed and 100 is fully open."""

    def __init__(self, shade: DimmerDevice, position: float):
        assert type(shade.device_type) == ShadeDimmerType
        self._fadedimmer = FadeDimmer(
            position, timedelta(), timedelta(), shade.address)

    def _perform_command(self, hub: Hub):
        self._fadedimmer._perform_command(hub)

class OpenShade(SetShadePosition):
    def __init__(self, shade: DimmerDevice):
        super().__init__(shade, position=100.0)

class CloseShade(SetShadePosition):
    def __init__(self, shade: DimmerDevice):
        super().__init__(shade, position = 0)

