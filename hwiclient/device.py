from abc import ABC, abstractmethod
from .utils import HwiUtils


class DeviceAddress():

    def __init__(self, unencoded: str):

        if unencoded.startswith('['):
            unencoded = unencoded.removeprefix('[')
            assert unencoded.endswith(']')
            unencoded = unencoded.removesuffix(']')

        self._unencoded = unencoded

    @property
    def unencoded(self) -> str:
        return self._unencoded

    @property
    def unencoded_with_brackets(self) -> str:
        return '[' + self._unencoded + ']'

    @property
    def encoded(self) -> str:
        if self.unencoded.count(':') == 2:
            return HwiUtils.encode_keypad_address(self.unencoded)
        else:
            return HwiUtils.encode_zone_address(self.unencoded)
        
    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, self.__class__):
            return False
        return self.unencoded == __o.unencoded

    def __ne__(self, __o: object) -> bool:
        return not self.__eq__(__o)

    def __repr__(self) -> str:
        return f"<DeviceAddress: {self.unencoded}>"

class Device(ABC):
    def __init__(self, name: str, room: str, address: DeviceAddress) -> None:
        self._name = name
        self._room = room
        self._address = address

    @property
    def name(self) -> str:
        return self._name

    @property
    def room(self) -> str:
        return self._room

    @property
    def address(self) -> DeviceAddress:
        return self._address


class OutputDevice(Device, ABC):
    pass


class InputDevice(Device, ABC):
    pass


class DeviceType(ABC):

    def __init__(self):
        pass

    @property
    @abstractmethod
    def type_id(self) -> str:
        pass
    
    def __repr__(self) -> str:
        return f"<DeviceType: {self.type_id}>"


class OutputDeviceType(DeviceType, ABC):
    pass


class Actions(ABC):
    def __init__(self, target) -> None:
        self._target = target


class Requests(ABC):
    def __init__(self, target) -> None:
        self._target = target
