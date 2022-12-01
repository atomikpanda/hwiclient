from __future__ import annotations
from .device import Device, DeviceAddress
from .dimmer import DimmerDeviceGroup, DimmerDevice
from abc import ABC, abstractmethod, abstractproperty
import logging
from typing import Optional
from dataclasses import dataclass
from .device import InputDevice
from .commands.hub import HubRequestCommand
from .commands.keypad import RequestKeypadLedStates

from .utils import HwiUtils
_LOGGER = logging.getLogger(__name__)


# Note button 23 and 24 are usually the dimmer arrows


class KeypadButton(object):

    def __init__(self, name: str, number: int, device_group: DimmerDeviceGroup, keypad: Keypad):
        self._name = name
        self._number = number
        self._device_group = device_group
        self._keypad = keypad
        self._led_changed_listener = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def number(self) -> int:
        return self._number

    @property
    def device_group(self) -> DimmerDeviceGroup:
        return self._device_group

    @property
    def keypad(self) -> Keypad:
        return self._keypad

    @property
    def led_changed_listener(self):
        return self._led_changed_listener

    @led_changed_listener.setter
    def led_changed_listener(self, listener):
        self._led_changed_listener = listener

    @property
    def is_led_on(self) -> bool:
        return self.keypad.is_led_on(self.number)

    def press(self) -> HubCommand:
        return ButtonPress(self)

    def on_led_changed(self, is_on: bool):
        if self.led_changed_listener != None:
            self.led_changed_listener.on_led_changed(is_on)
        if is_on:
            _LOGGER.warning(self._name + " is on")
        else:
            _LOGGER.warning(self._name + " is off")

    def debug_description(self):
        description = "[Button name: "+self._name+", number: " + \
            str(self.number)+", is_on: " + str(self.is_led_on) + "]"
        return description



class Keypad(InputDevice):

    def __init__(self, address: DeviceAddress, name: str, room: str, buttons: list[ButtonBuilder]):
        super().__init__(address=address, name=name, room=room)
        self._led_states = "000000000000000000000000"
        self._buttons_by_number: dict[int, KeypadButton] = {}
        for builder in buttons:
            builder.set_keypad(self)
            btn = builder.build()
            self._buttons_by_number[btn.number] = btn
        pass

    @property
    def buttons(self) -> list[KeypadButton]:
        return list(self._buttons_by_number.values())

    @property
    def led_states(self) -> str:
        return self._led_states

    def request_led_states(self) -> HubRequestCommand:
        return RequestKeypadLedStates(self.address)

    @led_states.setter
    def led_states(self, states: str):
        old_states = self._led_states
        self._led_states = states
        self._notify_buttons_of_new_led_state(old_states, states)

    def _notify_buttons_of_new_led_state(self, old_states: str, states: str):
        for i, char in enumerate(old_states):
            if char != states[i]:
                btn = self.button_with_number(i+1)
                if btn != None:
                    btn.on_led_changed(states[i] == "1")
        # SUPER HELPFUL FOR DEBUGGING
        _LOGGER.warning(self.debug_description())

    def is_led_on(self, button_number: int) -> bool:
        button_idx = button_number - 1
        if button_idx >= 0 and button_idx < len(self.led_states):
            return self.led_states[button_idx] == "1"
        return False

    def button_with_number(self, number: int) -> Optional[KeypadButton]:
        # return self._buttons_dict[str(number)]
        if number in self._buttons_by_number:
            return self._buttons_by_number[number]
        return None

    def button_with_name(self, name: str) -> Optional[KeypadButton]:
        for btn in self.buttons:
            if btn.name == name:
                return btn
        return None

    def debug_description(self):
        btns = "\r\n"
        for key, btn in self._buttons_by_number.items():
            btns += "\t" + btn.debug_description() + "\r\n"

        return "\r\n[Keypad name: "+self.name+", address: "+self.address.unencoded+", encoded_address: "+self.address.encoded+", buttons: "+btns+"]\r\n"

    pass


class ButtonBuilder(object):
    def __init__(self):
        self._name = None
        self._number = None
        self._zones: list[DimmerDevice] = []

    def set_name(self, name: str):
        self._name = name

    def set_number(self, number: int):
        self._number = number

    def set_keypad(self, keypad: Keypad):
        self._keypad = keypad

    def append_zone(self, zone: DimmerDevice):
        self._zones.append(zone)

    def build(self) -> KeypadButton:
        assert self._name is not None
        assert self._number is not None
        assert self._keypad is not None
        return KeypadButton(name=self._name, number=self._number, device_group=DimmerDeviceGroup(self._zones), keypad=self._keypad)


class KeypadBuilder(object):
    def __init__(self):
        self._name = None
        self._room = None
        self._address = None
        self._buttons: list[ButtonBuilder] = []

    def set_name(self, name: str):
        self._name = name

    def set_room(self, room: str):
        self._room = room

    def set_address(self, address: DeviceAddress):
        self._address = address

    def append_button(self, builder: ButtonBuilder):
        self._buttons.append(builder)

    def build(self) -> Keypad:
        assert self._name is not None
        assert self._address is not None
        assert self._room is not None
        return Keypad(name=self._name, address=self._address, buttons=self._buttons, room=self._room)
