from __future__ import annotations
from . import models
from . import hub
from . import utils
HwiUtils = hub.HwiUtils
Hub = hub.Hub


class HubCommand(object):
    def __init__(self):
        pass

    def execute(self, hub: Hub):
        raise NotImplementedError


class ButtonPress(HubCommand):
    def __init__(self, button: models.HwiButton):
        super().__init__()
        self._button = button

    def execute(self, hub: Hub):
        hub.sender.send_keypad_button_press(
            self._button.keypad.address, self._button.number)


class SetZoneBrightness(HubCommand):
    def __init__(self, zone: models.HwiZone, brightness_percent: float):
        super().__init__()
        self._zone = zone
        self._brightness_percent = brightness_percent

    def execute(self, hub: Hub):
        hub.sender.send_dim_light(dimmer_address=self._zone.address,
                                  level=self._brightness_percent)
        
class SetFanBrightness(SetZoneBrightness):
    def __init__(self, zone: models.HwiZone, fan_speeds: int, brightness_percent: float):
        super().__init__(zone, HwiUtils.safe_fan_brightness(fan_speeds, brightness_percent))
        
class ReadDimmerLevel(HubCommand):
    def __init__(self, zone: models.HwiZone):
        self._zone = zone
        
    def execute(self, hub: Hub):
        hub.sender.send_read_dimmer_level(self._zone.address)
        
class ReadKeypadLedStatus(HubCommand):
    def __init__(self, keypad: models.HwiKeypad):
        self._keypad = keypad
    
    def execute(self, hub: Hub):
        hub.sender.send_read_keypad_led_status(self._keypad.address)

class SetShadePosition(HubCommand):
    # The current position of cover where 0 means closed and 100 is fully open.
    def __init__(self, shade: models.HwiShade, position: int):
        super().__init__()
        self._shade = shade
        self._position = position
        
    def execute(self, hub: Hub):
        hub.sender.send_fade_shade_dim(self._shade.address, level = self._position)
    
class OpenShade(SetShadePosition):
    def __init__(self, shade: models.HwiShade):
        self._shade = shade
        self._position = 100


class CloseShade(SetShadePosition):
    def __init__(self, shade: models.HwiShade):
        self._shade = shade
        self._position = 0

class Sequence(HubCommand):
    def __init__(self, commands: list[HubCommand]):
        super().__init__()
        self._commands = commands
    
    def execute(self, hub: Hub):
        for cmd in self._commands:
            cmd.execute(hub)