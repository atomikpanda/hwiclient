from __future__ import annotations
from .events import DeviceEventSource, DeviceEventKey, DeviceEventKind, EventListener
from enum import IntEnum

from .device import Device, DeviceAddress
from .dimmer import DimmerDeviceGroup, DimmerDevice
from abc import ABC, abstractmethod, abstractproperty
import logging
from typing import Optional
from dataclasses import dataclass
from .device import InputDevice
from .commands.hub import HubRequestCommand
from .commands.keypad import RequestKeypadLedStates, KeypadButtonPress
from collections.abc import Sequence
from .utils import HwiUtils
_LOGGER = logging.getLogger(__name__)


class KeypadLedState(IntEnum):
    OFF = 0
    ON = 1
    FLASH_1 = 2
    FLASH_2 = 3


class KeypadLedStates(Sequence):
    def __init__(self, states_str: str = "000000000000000000000000"):
        if len(states_str) != 24:
            raise ValueError("LED states string must be 24 characters long")

        self._states = []
        for index, char in enumerate(states_str):
            if char == '0' or char == '1' or char == '2' or char == '3':
                self._states.append(KeypadLedState(int(char)))
            else:
                raise ValueError('invalid keypad led state char')

        if len(self._states) != 24:
            raise ValueError("Invalid keypad led state string")

    def __getitem__(self, index) -> KeypadLedState:
        return self._states[index]

    def __len__(self):
        return len(self._states)


# Note button 23 and 24 are usually the dimmer arrows


class KeypadButton(EventListener):

    def __init__(self, name: str, number: int, device_group: DimmerDeviceGroup, keypad: Keypad):
        self._name = name
        self._number = number
        self._device_group = device_group
        self._keypad = keypad

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
    def is_led_on(self) -> bool:
        return self.keypad.is_led_on(self.number)

    def on_event(self, kind: str, data: dict):
        if kind == DeviceEventKind.KEYPAD_LED_STATES_CHANGED:
            if self.is_led_on:
                _LOGGER.warning(self._name + " is on")
            else:
                _LOGGER.warning(self._name + " is off")

    def debug_description(self):
        description = "[Button name: "+self._name+", number: " + \
            str(self.number)+", is_on: " + str(self.is_led_on) + "]"
        return description


class Keypad(InputDevice, EventListener):

    def __init__(self, address: DeviceAddress, name: str, room: str, buttons: list[ButtonBuilder]):
        super().__init__(address=address, name=name, room=room)
        self._led_states: KeypadLedStates = KeypadLedStates()
        self._buttons_by_number: dict[int, KeypadButton] = {}
        self._event_source = DeviceEventSource()
        for builder in buttons:
            builder.set_keypad(self)
            btn = builder.build()
            self._event_source.register_listener(btn, {DeviceEventKey.BUTTON_NUMBER: btn.number},
                                                 DeviceEventKind.KEYPAD_BUTTON_PRESSED,
                                                 DeviceEventKind.KEYPAD_BUTTON_DOUBLE_TAPPED,
                                                 DeviceEventKind.KEYPAD_BUTTON_HELD,
                                                 DeviceEventKind.KEYPAD_BUTTON_RELEASED)
            self._event_source.register_listener(
                btn, None, DeviceEventKind.KEYPAD_LED_STATES_CHANGED)
            self._buttons_by_number[btn.number] = btn

    @property
    def buttons(self) -> list[KeypadButton]:
        return list(self._buttons_by_number.values())

    @property
    def led_states(self) -> KeypadLedStates:
        return self._led_states

    @property
    def event_source(self) -> DeviceEventSource:
        return self._event_source

    def request_led_states(self) -> HubRequestCommand:
        return RequestKeypadLedStates(self.address)

    def is_led_on(self, button_number: int) -> bool:
        button_idx = button_number - 1
        if button_idx >= 0 and button_idx < len(self.led_states):
            return self.led_states[button_idx] == KeypadLedState.ON
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

    def on_event(self, kind: str, data: dict):
        if kind == DeviceEventKind.KEYPAD_LED_STATES_CHANGED:
            old_states = self._led_states
            self._led_states = data[DeviceEventKey.KEYPAD_LED_STATES]
            # SUPER HELPFUL FOR DEBUGGING
            _LOGGER.warning(self.debug_description())
        # forward to keypad's event source
        self._event_source.post(DeviceEventKind(str), data)


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
        assert self._name != None
        assert self._number != None
        assert self._keypad != None
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
        assert self._name != None
        assert self._address != None
        assert self._room != None
        return Keypad(name=self._name, address=self._address, buttons=self._buttons, room=self._room)
