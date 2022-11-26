from __future__ import annotations
from typing import Optional
from . import utils
from . import commands
HwiUtils = utils.HwiUtils
import logging
_LOGGER = logging.getLogger(__name__)

class HwiShade(object):
    def __init__(self, address: str, name: str):
        self._address = address
        self._name = name
    
    @property
    def address(self) -> str:
        return self._address

    @property
    def name(self) -> str:
        return self._name

class HwiZone(object):

    def __init__(self, zone_number: int, zone_address: str, zone_type: str):
        self._zone_number = zone_number
        self._zone_address = zone_address
        self._zone_type = zone_type
        self._brightness_percent = 0
        self._listeners = []
        pass

    @property
    def number(self) -> int:
        return self._zone_number

    @property
    def address(self) -> str:
        return self._zone_address

    @property
    def zone_type(self) -> str:
        return self._zone_type

    def add_brightness_listener(self, listener):
        self._listeners.append(listener)

    @property
    def brightness_percent(self) -> float:
        return self._brightness_percent

    def on_brightness_changed(self, new_brightness_percent):
        # _LOGGER.warning("zone OK ")
        # _LOGGER.warning("zone is notifying its listeners count: " + str(len(self._listeners)))
        # _LOGGER.warning("zone AFTER ")
        self._brightness_percent = new_brightness_percent
        for listener in self._listeners:
            listener.on_brightness_changed(self)
        pass


# Note button 23 and 24 are usually the dimmer arrows
class HwiButton(object):
    # def press(self):
    #     hub.sender.press_button(self)
    #     commands.ButtonPress(self)

    # def turn_on(self) -> commands.HubCommand:
    #     if self.is_led_on == False:
    #         hub.sender.press_button(self)
    #         return commands.ButtonPress(self)

    # def turn_off(self):
    #     if self.is_led_on == True:
    #         hub.sender.press_button(self)

    def set_brightness(self, brightness_percent: float) -> commands.HubCommand:
        commands_list: list[commands.HubCommand] = []
        
        for zone in self.zones:
            zone._brightness_percent = brightness_percent
            if zone.zone_type == "FAN":
                fan_speeds = 4
                # Patio Fan
                if self._keypad.address == "[1:6:4]" and self._number == 4:
                    fan_speeds = 6

                commands_list.append(commands.SetFanBrightness(zone, fan_speeds, brightness_percent))

            elif zone.zone_type != "SWITCH":
                commands_list.append(commands.SetZoneBrightness(zone, brightness_percent))
            elif zone.zone_type == "SWITCH":
                if brightness_percent > 0:
                    commands_list.append(commands.SetZoneBrightness(zone, 100))
                else:
                    commands_list.append(commands.SetZoneBrightness(zone, 0))

        
        self._brightness = self.recalculate_brightness()
        return commands.Sequence(commands_list)

    def update_brightness(self) -> commands.HubCommand:
        cmds = []
        for zone in self.zones:
            cmds.append(commands.ReadDimmerLevel(zone))
        return commands.Sequence(cmds)

    def __init__(self, number: int, name: str, zones: list[HwiZone], keypad: HwiKeypad):
        self._keypad = keypad
        self._number = number
        self._name = name
        self._zones = zones
        self._has_dimmer = False
        self._brightness = 0
        self._led_changed_listener = None
        self._brightness_changed_listener = None

        for zone in self.zones:
            zone.add_brightness_listener(self)

        self._has_dimmer = self._at_least_one_zone_is_dimmable()

        pass

    def _at_least_one_zone_is_dimmable(self) -> bool:
        for zone in self.zones:
            if zone.zone_type == "DIMMER" or zone.zone_type == "FAN":
                return True
        return False

    @property
    def has_dimmer(self) -> bool:
        return self._has_dimmer

    @property
    def brightness(self) -> float:
        return self._brightness

    @property
    def keypad(self) -> HwiKeypad:
        return self._keypad

    @property
    def name(self) -> str:
        return self._name

    @property
    def zones(self) -> list[HwiZone]:
        return self._zones

    @keypad.setter
    def keypad(self, keypad: HwiKeypad):
        self._keypad = keypad
        pass

    @property
    def led_changed_listener(self):
        return self._led_changed_listener

    @led_changed_listener.setter
    def led_changed_listener(self, listener):
        self._led_changed_listener = listener
        pass

    @property
    def brightness_changed_listener(self):
        return self._brightness_changed_listener

    @brightness_changed_listener.setter
    def brightness_changed_listener(self, listener):
        self._brightness_changed_listener = listener
        pass

    @property
    def is_led_on(self) -> bool:
        return self.keypad.is_led_on(self.number)

    def on_led_changed(self, is_on: bool):
        if self.led_changed_listener != None:
            self.led_changed_listener.on_led_changed(is_on)
        if is_on:
            _LOGGER.warning(self._name + " is on")
        else:
            _LOGGER.warning(self._name + " is off")
        pass

    # Brightness in a zone that this button controls was changed.
    def on_brightness_changed(self, zone):
        self._brightness = self.recalculate_brightness()
        if self.brightness_changed_listener != None:
            self.brightness_changed_listener.on_brightness_changed(
                self._brightness)
        pass

    def recalculate_brightness(self) -> float:
        return HwiUtils.percent_to_brightness(HwiUtils.calculate_zones_brightness_percent(self._zones))

    @property
    def number(self) -> int:
        return self._number

    def debug_description(self):
        description = "[Button name: "+self._name+", number: " + \
            str(self.number)+", is_on: " + str(self.is_led_on) + "]"
        return description


class HwiKeypad(object):

    def __init__(self, address: str, name: str, buttons: list[HwiButtonBuilder]):
        self._address = address
        self._name = name
        self._led_states = "000000000000000000000000"
        self._buttons_dict = {}
        for builder in buttons:
            builder.set_keypad(self)
            btn = builder.build()
            self._buttons_dict[btn.number] = btn
        pass

    @property
    def address(self) -> str:
        return self._address

    @property
    def name(self) -> str:
        return self._name

    @property
    def buttons(self) -> list[HwiButton]:
        return list(self._buttons_dict.values())

    @property
    def led_states(self) -> str:
        return self._led_states

    def update_led_states(self) -> commands.HubCommand:
        return commands.ReadKeypadLedStatus(keypad=self)

    @led_states.setter
    def led_states(self, states: str):
        old_states = self._led_states
        self._led_states = states
        self._notify_buttons_of_new_led_state(old_states, states)
        pass

    def _notify_buttons_of_new_led_state(self, old_states: str, states: str):
        for i, char in enumerate(old_states):
            if char != states[i]:
                btn = self.button_with_number(i+1)
                if btn != None:
                    btn.on_led_changed(states[i] == "1")
        # SUPER HELPFUL FOR DEBUGGING
        _LOGGER.warning(self.debug_description())

    def is_led_on(self, button_number) -> bool:
        button_idx = button_number - 1
        if button_idx >= 0 and button_idx < len(self.led_states):
            return self.led_states[button_idx] == "1"
        return False

    def button_with_number(self, number) -> Optional[HwiButton]:
        # return self._buttons_dict[str(number)]
        if number in self._buttons_dict:
            return self._buttons_dict[number]
        return None

    def debug_description(self):
        btns = "\r\n"
        for key, btn in self._buttons_dict.items():
            btns += "\t" + btn.debug_description() + "\r\n"

        return "\r\n[Keypad name: "+self.name+", address: "+self.address+", encoded_address: "+HwiUtils.encode_keypad_address(self.address)+", buttons: "+btns+"]\r\n"

    pass


class HwiButtonBuilder(object):
    def __init__(self):
        self._name = None
        self._number = None
        self._zones: list[HwiZone] = []
        
    def set_name(self, name: str):
        self._name = name
        
    def set_number(self, number: int):
        self._number = number
        
    def set_keypad(self, keypad: HwiKeypad):
        self._keypad = keypad
        
    def append_zone(self, zone: HwiZone):
        self._zones.append(zone)
        
    def build(self) -> HwiButton:
        assert self._name is not None
        assert self._number is not None
        assert self._keypad is not None
        return HwiButton(name=self._name, number = self._number, zones=self._zones,keypad=self._keypad)

class HwiKeypadBuilder(object):
    def __init__(self):
        self._name = None
        self._address = None
        self._buttons: list[HwiButtonBuilder] = []
    
    def set_name(self, name: str):
        self._name = name
        
    def set_address(self, address: str):
        self._address = address
        
    def append_button(self, builder: HwiButtonBuilder):
        self._buttons.append(builder)
        
    def build(self) -> HwiKeypad:
        assert self._name is not None
        assert self._address is not None
        return HwiKeypad(name=self._name, address=self._address, buttons =self._buttons)
    