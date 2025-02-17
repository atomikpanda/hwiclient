from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from .commands.dimmer import FadeDimmer, StopDimmer
from .commands.hub import SessionActionCommand
from .dimmer import DimmerActions, DimmerDevice, DimmerDeviceType

if TYPE_CHECKING:
    from .hub import Hub


class ShadeDimmerType(DimmerDeviceType):
    @classmethod
    def type_id(cls) -> str:
        return "QED SHADE"

    @property
    def is_dimmable(self) -> bool:
        return True

    def actions(self, device: DimmerDevice) -> DimmerActions:
        return ShadeActions(device)


class ShadeActions(DimmerActions):
    def set_position(self, position: float) -> SessionActionCommand:
        return SetShadePosition(self._target, position)

    def open_shade(self) -> SessionActionCommand:
        return OpenShade(self._target)

    def close_shade(self) -> SessionActionCommand:
        return CloseShade(self._target)

    def stop_shade(self) -> SessionActionCommand:
        return StopDimmer(self._target.address)


class SetShadePosition(SessionActionCommand):
    """Sets the current position of cover where 0 means closed and 100 is fully open."""

    def __init__(self, shade: DimmerDevice, position: float):
        assert shade.device_type.type_id() == ShadeDimmerType.type_id()
        self._fadedimmer = FadeDimmer(position, timedelta(), timedelta(), shade.address)

    async def _perform_command(self, hub: Hub):
        await self._fadedimmer._perform_command(hub)


class OpenShade(SetShadePosition):
    def __init__(self, shade: DimmerDevice):
        super().__init__(shade, position=100.0)


class CloseShade(SetShadePosition):
    def __init__(self, shade: DimmerDevice):
        super().__init__(shade, position=0)
