from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from ..models import Time
from .hub import SessionActionCommand, SessionRequestCommand


class FadeDimmer(SessionActionCommand):
    """Fades one or more system dimmers to a target intensity using a specified fade time and after a specified delay time."""

    if TYPE_CHECKING:
        from ..device import DeviceAddress
        from .sender import CommandSender

    def __init__(
        self,
        intensity: float,
        fade_time: timedelta,
        delay_time: timedelta,
        *dimmer_addresses: DeviceAddress,
    ):
        """FADEDIM, <intensity>, <fade time>, <delay time>, <address 1>, ..., <address n>"""
        super().__init__()
        self._intensity = intensity
        self._fade_time = fade_time
        self._delay_time = delay_time
        self._dimmer_adresses = dimmer_addresses
        if len(self._dimmer_adresses) <= 0:
            raise ValueError("At least one dimmer address is required")

        if len(self._dimmer_adresses) > 10:
            raise ValueError("Exceeded max limit of 10 dimmer addresses")

        if not (self._intensity >= 0 and self._intensity <= 100):
            raise ValueError("intensity must be between 0 and 100")

    async def _perform_command(self, sender: CommandSender):
        args = [
            str(self._intensity),
            Time(self._fade_time).formatted_hour_min_sec,
            Time(self._delay_time).formatted_hour_min_sec,
        ]
        for addr in self._dimmer_adresses:
            args.append(addr.unencoded_with_brackets)

        await sender.send_raw_command("FADEDIM", *args)


class RequestDimmerLevel(SessionRequestCommand):
    """Requests the current or target level for any zone in the system"""

    if TYPE_CHECKING:
        from ..device import DeviceAddress
        from .sender import CommandSender

    def __init__(self, address: DeviceAddress):
        """RDL, <address>"""
        self._address = address

    async def _perform_command(self, sender: CommandSender):
        await sender.send_raw_command("RDL", self._address.unencoded_with_brackets)


class StopDimmer(SessionActionCommand):
    """Stops raising/lowering one or more system dimmers"""

    if TYPE_CHECKING:
        from ..device import DeviceAddress
        from .sender import CommandSender

    def __init__(self, *dimmer_addresses: DeviceAddress):
        """STOPDIM, <address 1>, ..., <address n>"""
        super().__init__()
        self._dimmer_adresses = dimmer_addresses
        if len(self._dimmer_adresses) <= 0:
            raise ValueError("At least one dimmer address is required")

        if len(self._dimmer_adresses) > 10:
            raise ValueError("Exceeded max limit of 10 dimmer addresses")

    async def _perform_command(self, sender: CommandSender):
        args = []
        for addr in self._dimmer_adresses:
            args.append(addr.unencoded_with_brackets)

        await sender.send_raw_command("STOPDIM", *args)
