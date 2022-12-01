from __future__ import annotations
from datetime import timedelta
from typing import TYPE_CHECKING
from .device import *
from .commands.dimmer import RequestDimmerLevel, FadeDimmer
from .commands.hub import SessionActionCommand, SessionRequestCommand, Sequence, HubCommand

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
    def set_level(self, level: float) -> SessionActionCommand:
        return FadeDimmer(level, timedelta(), timedelta(), self._target.address)
    
    def turn_off(self) -> SessionActionCommand:
        return FadeDimmer(0, timedelta(), timedelta(), self._target.address)
    
    def turn_on(self) -> SessionActionCommand:
        return FadeDimmer(100, timedelta(), timedelta(), self._target.address)


class DimmerRequests(Requests):
    def level(self) -> SessionRequestCommand:
        return RequestDimmerLevel(self._target.address)


class DimmerDevice(OutputDevice):

    def __init__(self, name: str, zone_number: str, address: DeviceAddress, device_type: DimmerDeviceType, room: str):
        super().__init__(name=name, room=room, address=address)
        self._zone_number = zone_number
        self._device_type = device_type
        self._level = 0
        self._listeners = []

    @property
    def number(self) -> str:
        return self._zone_number

    @property
    def device_type(self) -> DimmerDeviceType:
        return self._device_type

    @property
    def is_dimmable(self) -> bool:
        """Whether or not the actual device is a dimmer or switch."""
        return self._device_type.is_dimmable

    def add_level_listener(self, listener):
        self._listeners.append(listener)

    @property
    def level(self) -> float:
        return self._level

    @property
    def action(self) -> DimmerActions:
        return self._device_type.actions(self)

    @property
    def request(self) -> DimmerRequests:
        return self._device_type.requests(self)

    def on_level_changed(self, new_level):
        # _LOGGER.warning("zone OK ")
        # _LOGGER.warning("zone is notifying its listeners count: " + str(len(self._listeners)))
        # _LOGGER.warning("zone AFTER ")
        self._level = new_level
        for listener in self._listeners:
            listener.on_brightness_changed(self)
        pass


class DimmerDeviceGroup(object):
    def __init__(self, devices: list[DimmerDevice]):
        self._level = 0
        self._devices = devices
        for device in self.devices:
            device.add_level_listener(self)

        self._has_dimmer = self._at_least_one_device_is_dimmable()
        self._level_changed_listener = None

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

    @property
    def level_changed_listener(self):
        return self._level_changed_listener

    @level_changed_listener.setter
    def level_changed_listener(self, listener):
        self._level_changed_listener = listener

    # Brightness in a zone within this group was changed.
    def on_level_changed(self, zone):
        # recalculate brightness for the whole group
        self._level = self._calculate_group_level()
        if self.level_changed_listener != None:
            self.level_changed_listener.on_level_changed(
                self._level)
        pass

    def request_all_levels(self) -> HubCommand:
        return Sequence([z.request.level() for z in self._devices])

    def set_level(self, level: float) -> HubCommand:
        cmds: list[HubCommand] = []

        for device in self.devices:
            device._level = level
            cmds.append(device.action.set_level(level))

        self._level = self._calculate_group_level()
        return Sequence(cmds)
