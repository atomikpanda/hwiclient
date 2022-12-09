from abc import ABC
from .hub import SessionActionCommand, SessionRequestCommand
from typing import TYPE_CHECKING


from ..device import DeviceAddress
from .sender import CommandSender


class KeypadButtonCommand(SessionActionCommand, ABC):

    def __init__(self, command_name: str, address: DeviceAddress, button: int):
        self._command_name = command_name
        self._address = address
        self._button_number = button
        if button < 1 or button > 24:
            raise ValueError("Invalid button number: %d" % button)

    def _perform_command(self, sender: CommandSender):
        sender.send_command(self._command_name, self._address.unencoded_with_brackets, str(
            self._button_number))


class KeypadButtonPress(KeypadButtonCommand):
    """Simulates the press action of a keypad button. 
    This does not simulate a true keypad button press that might include an immediate release."""

    def __init__(self, address: DeviceAddress, button: int):
        super().__init__(command_name="KBP", address=address, button=button)


class KeypadButtonRelease(KeypadButtonCommand):
    """Simulates the press action of a keypad button.
    This does not simulate a true keypad button press that might include an immediate release."""

    def __init__(self, address: DeviceAddress, button: int):
        super().__init__(command_name="KBP", address=address, button=button)


class KeypadButtonHold(KeypadButtonCommand):
    """Simulates the hold action of a keypad button. 
    This does not simulate a true keypad button hold that will include a preceeding press"""

    def __init__(self, address: DeviceAddress, button: int):
        super().__init__(command_name="KBH", address=address, button=button)


class KeypadButtonDoubleTap(KeypadButtonCommand):
    """Simulates the double tap action of a keypad button. 
    This does not simulate a true keypad button double tap that is preceeded by a press and release, and followed by a release"""

    def __init__(self, address: DeviceAddress, button: int):
        super().__init__(command_name="KBDT", address=address, button=button)


class RequestKeypadLedStates(SessionRequestCommand):
    """Queries the system for the state of the LEDs on a specified keypad. 
    24 led digits will be returned regardless of the number of physical leds on the keypad."""

    def __init__(self, keypad_address: DeviceAddress):
        self._keypad_address = keypad_address

    def _perform_command(self, sender: CommandSender):
        sender.send_command("RKLS", self._keypad_address.unencoded_with_brackets)
