from .device import DeviceAddress
from .dimmer import DimmerDevice, DimmerDeviceType
from .light import LightDimmerType
from .shade import ShadeDimmerType
from .fan import FanDimmerType
from .switch import SwitchDimmerType
from .keypad import Keypad
import yaml
from typing import Optional, Any, Type
from .monitoring import TopicNotifier, MonitoringTopic, TopicSubscriber, MonitoringTopicKey
from .events import DeviceEventSource, DeviceEventKind, DeviceEventKey


class DeviceRepository(TopicSubscriber):

    def __init__(self, homeworks_config: Optional[dict[str, Any]], notifier: TopicNotifier):
        self._keypads: dict[str, Keypad] = {}
        self._dimmers: dict[str, DimmerDevice] = {}
        self._notifier = notifier
        self._notifier.subscribe(self, MonitoringTopic.DIMMER_LEVEL_CHANGED)
        self._event_source = DeviceEventSource()
        if homeworks_config != None:
            self._add_from_yaml_dict(homeworks_config)

    def on_topic_update(self, topic: MonitoringTopic, data: dict):
        if topic == MonitoringTopic.DIMMER_LEVEL_CHANGED:
            address = DeviceAddress(data[MonitoringTopicKey.ADDRESS])
            level = data[MonitoringTopicKey.LEVEL]
            data = {DeviceEventKey.DEVICE_ADDRESS: address,
                    DeviceEventKey.DIMMER_LEVEL: level}
            self._event_source.post(DeviceEventKind.DIMMER_LEVEL_CHANGED, data)

    def add_from_yaml(self, yaml_filepath):
        with open(yaml_filepath, 'r') as file:
            yaml_dict = yaml.safe_load(file)
            self._add_from_yaml_dict(yaml_dict)

    def _make_dimmer_device(self, device_dict: dict, room_name: str, device_type: DimmerDeviceType) -> DimmerDevice:
        return DimmerDevice(zone_number=device_dict['number'], address=DeviceAddress(device_dict['address']),
                            name=device_dict['name'], device_type=device_type, room=room_name)

    def _add_from_yaml_dict(self, yaml_dict: dict[str, Any]):
        for room_name, room in yaml_dict['devices'].items():
            if 'dimmers' in room:
                for light in room['dimmers']:
                    self.add_dimmer(self._make_dimmer_device(
                        light, room_name, LightDimmerType()))
            if 'switches' in room:
                for switch in room['switches']:
                    self.add_dimmer(self._make_dimmer_device(
                        switch, room_name, SwitchDimmerType()))
            if 'fans' in room:
                for fan in room['fans']:
                    fan_speeds = fan.get('speeds', 4)
                    self.add_dimmer(self._make_dimmer_device(
                        fan, room_name, FanDimmerType(fan_speeds)))
            if 'shades' in room:
                for shade in room['shades']:
                    self.add_dimmer(self._make_dimmer_device(
                        shade, room_name, ShadeDimmerType()))

    def add_dimmer(self, dimmer: DimmerDevice) -> None:
        self._event_source.register_listener(dimmer, {
                                             DeviceEventKey.DEVICE_ADDRESS: dimmer.address}, DeviceEventKind.DIMMER_LEVEL_CHANGED)
        self._dimmers[dimmer.address.encoded] = dimmer

    def add_keypad(self, keypad: Keypad) -> None:
        self._event_source.register_listener(keypad, {DeviceEventKey.DEVICE_ADDRESS: keypad.address}, DeviceEventKind.KEYPAD_LED_STATES_CHANGED,
                                             DeviceEventKind.KEYPAD_BUTTON_PRESSED, DeviceEventKind.KEYPAD_BUTTON_RELEASED,
                                             DeviceEventKind.KEYPAD_BUTTON_HELD, DeviceEventKind.KEYPAD_BUTTON_DOUBLE_TAPPED)
        self._keypads[keypad.address.encoded] = keypad

    def get_keypad_named(self, keypad_name: str) -> Optional[Keypad]:
        for keypad_address, keypad in self._keypads.items():
            if keypad.name == keypad_name:
                return keypad
        return None

    def get_keypad_at_address(self, keypad_address: str) -> Optional[Keypad]:
        if keypad_address in self._keypads:
            return self._keypads[keypad_address]
        else:
            return None

    def dimmer_device_at_address(self, address: DeviceAddress) -> Optional[DimmerDevice]:
        if address.encoded in self._dimmers:
            return self._dimmers[address.encoded]
        else:
            return None

    def find_dimmer_device_named(self, zone_name: str, room_name: Optional[str] = None) -> Optional[DimmerDevice]:
        for zone_address, zone in self._dimmers.items():
            if zone.name == zone_name and room_name == None:
                return zone
            elif zone.name == zone_name and zone.room == room_name:
                return zone
        return None

    def all_dimmer_devices(self, room_name: Optional[str] = None) -> list[DimmerDevice]:
        if room_name == None:
            return list(self._dimmers.values())
        return [dimmer for dimmer in self._dimmers.values() if dimmer.room == room_name]

    def all_dimmer_devices_of_type(self, *types: Type[DimmerDeviceType]):
        types_strs = [devtype.type_id() for devtype in types]
        return [dimmer for dimmer in self._dimmers.values() if dimmer.device_type.type_id() in types_strs]

    def add_all_entities(self, add_entities):
        raise NotImplementedError
        # entities = []
        # for keypad_addr, keypad in self._parsed_objects.items():
        #     for btn in keypad.buttons:
        #         entities.append(light.HwiLight(keypad, btn))

        # for shade_addr, shade in self._shade_objects.items():
        #     entities.append(shade)

        # add_entities(entities)
        # pass

    # def __new__(cls):
    #     if cls._instance is None:
    #         cls._instance = super(DeviceRepository, cls).__new__(cls)
    #         # Put any initialization here.
    #     return cls._instance
