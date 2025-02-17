from __future__ import annotations

from datetime import timedelta

from .commands.dimmer import FadeDimmer, RequestDimmerLevel, StopDimmer
from .commands.hub import (
    HubCommand,
    Sequence,
    SessionActionCommand,
    SessionRequestCommand,
)
from .device import *
from .events import DeviceEventKey, DeviceEventKind, DeviceEventSource, EventListener


class DimmerDeviceType(OutputDeviceType, ABC):
    @property
    @abstractmethod
    def is_dimmable(self) -> bool:
        """Whether or not the actual device is just a switch."""
        pass

    def actions(self, device: DimmerDevice) -> DimmerActions:
        return DimmerActions(device)

    def requests(self, device: DimmerDevice) -> DimmerRequests:
        return DimmerRequests(device)


class DimmerActions(Actions):
    def set_level(
        self,
        level: float,
        fade_time: timedelta = timedelta(),
        delay_time: timedelta = timedelta(),
    ) -> SessionActionCommand:
        return FadeDimmer(level, fade_time, delay_time, self._target.address)

    def turn_off(self, fade_time: timedelta = timedelta()) -> SessionActionCommand:
        return FadeDimmer(0, fade_time, timedelta(), self._target.address)

    def turn_on(self) -> SessionActionCommand:
        return FadeDimmer(100, timedelta(), timedelta(), self._target.address)

    def stop_dim(self) -> SessionActionCommand:
        return StopDimmer(self._target.address)


class DimmerRequests(Requests):
    def level(self) -> SessionRequestCommand:
        return RequestDimmerLevel(self._target.address)


class DimmerDevice(OutputDevice, EventListener):
    def __init__(
        self,
        name: str,
        zone_number: str,
        address: DeviceAddress,
        device_type: DimmerDeviceType,
        room: str,
    ):
        super().__init__(name=name, room=room, address=address)
        self._zone_number = zone_number
        self._device_type = device_type
        self._level: float = 0
        self._event_source = DeviceEventSource()

    def __repr__(self) -> str:
        return f"<DimmerDevice(name={self.name}, room={self.room} level={self.level}, address={self.address}, type={self.device_type})>"

    @property
    def zone_number(self) -> str:
        return self._zone_number

    @property
    def device_type(self) -> DimmerDeviceType:
        return self._device_type

    @property
    def is_dimmable(self) -> bool:
        """Whether or not the actual device is a dimmer or switch."""
        return self._device_type.is_dimmable

    @property
    def level(self) -> float:
        return self._level

    @property
    def action(self) -> DimmerActions:
        return self._device_type.actions(self)

    @property
    def request(self) -> DimmerRequests:
        return self._device_type.requests(self)

    @property
    def event_source(self) -> DeviceEventSource:
        return self._event_source

    def on_event(self, kind: str, data: dict):
        if kind == DeviceEventKind.DIMMER_LEVEL_CHANGED:
            self._level = data[DeviceEventKey.DIMMER_LEVEL]

        # post to event_source
        data[DeviceEventKey.DEVICE] = self
        self._event_source.post(DeviceEventKind(kind), data)


class DimmerDeviceGroup(EventListener):
    def __init__(self, devices: list[DimmerDevice]):
        self._level: float = 0
        self._devices = devices
        self._event_source = DeviceEventSource()

        for device in self.devices:
            device.event_source.register_listener(self, None)

        self._has_dimmer = self._at_least_one_device_is_dimmable()

    @property
    def has_dimmer(self) -> bool:
        return self._has_dimmer

    @property
    def devices(self) -> list[DimmerDevice]:
        return self._devices

    @property
    def level(self) -> float:
        return self._level

    def _calculate_group_level(self) -> float:
        max_percent = 0
        for device in self._devices:
            if device.is_dimmable:
                max_percent = max(max_percent, device.level)

        return max_percent

    def _at_least_one_device_is_dimmable(self) -> bool:
        return any(device.is_dimmable for device in self._devices)

    def request_all_levels(self) -> HubCommand:
        return Sequence([z.request.level() for z in self._devices])

    def set_level(self, level: float) -> HubCommand:
        cmds: list[HubCommand] = []

        for device in self.devices:
            device._level = level
            cmds.append(device.action.set_level(level))

        self._level = self._calculate_group_level()
        return Sequence(cmds)

    @property
    def event_source(self) -> DeviceEventSource:
        return self._event_source

    def on_event(self, kind: str, data: dict):
        if kind == DeviceEventKind.DIMMER_LEVEL_CHANGED:
            # recalculate brightness for the whole group
            old_level = self._level
            new_level = self._calculate_group_level()
            self._level = new_level
            if new_level != old_level:
                self._event_source.post(
                    DeviceEventKind.DEVICE_GROUP_DIMMER_LEVEL_CHANGED,
                    {
                        DeviceEventKey.DEVICE_GROUP: self,
                        DeviceEventKey.DIMMER_LEVEL: new_level,
                    },
                )

        # forward events to group's event_source
        self._event_source.post(DeviceEventKind(kind), data)
