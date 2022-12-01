import xml.etree.ElementTree as ET
from typing import Any, Optional, Tuple, TYPE_CHECKING


import yaml
import logging
_LOGGER = logging.getLogger(__name__)


class HwiYamlParser(object):
    
    def __init__(self) -> None:
        pass
    
    # def parse_yaml(self, yaml_dict) -> dict[str, Any]:
    #     raise DeprecationWarning
    #     try:
    #         keypads = yaml_dict["keypads"]

    #         parsed_objects: dict[str, Any] = {}
    #         for keypad_name, keypad in keypads.items():
    #             keypad_builder = models.KeypadBuilder()
    #             keypad_builder.set_name(keypad_name)
    #             keypad_builder.set_address(keypad["address"])

    #             if "buttons" in keypad:  # and keypad_name == "Master Bedroom 1":
    #                 raw_buttons = keypad["buttons"]
    #                 buttons = []
    #                 for i, button in enumerate(raw_buttons):
    #                     raw_zones = []
    #                     button_builder = ButtonBuilder()
    #                     button_builder.set_name(button["name"])
    #                     button_builder.set_number(button["number"])

    #                     if "zones" in button:
    #                         raw_zones = button["zones"]

    #                     if raw_zones != None:
    #                         for raw_zone in raw_zones:
    #                             # FIXME: get device repository from method args instead
    #                             zone = reposDeviceRepository().get_zone_at_address(
    #                                 utils.HwiUtils.encode_zone_address(raw_zone["address"]))
    #                             if zone == None:
    #                                 zone = self._parse_zone(raw_zone)
    #                                 repos.DeviceRepository()._dimmers[utils.HwiUtils.encode_zone_address(
    #                                     raw_zone["address"])] = zone

    #                             button_builder.append_zone(zone)
    #                             pass
    #                     keypad_builder.append_button(button_builder)

    #                 parsed_objects[utils.HwiUtils.encode_keypad_address(
    #                     keypad['address'])] = keypad_builder.build()
    #             pass

    #         return parsed_objects

    #     except yaml.YAMLError as e:
    #         _LOGGER.error(e)
    #         raise e

    # def new_parse_yaml(self, yaml_dict):
    #     pass
                

    # def _parse_zone(self, raw_zone: dict) -> DimmerDevice:
    #     number = raw_zone["number"]
    #     addr = raw_zone["address"]

    #     return DimmerDevice(zone_number=number, address=DeviceAddress(addr), device_type=self._parse_zone_type(raw_zone))

    # def _parse_zone_type(self, raw_zone: dict) -> DeviceType:
    #     type_id = raw_zone["type"]
    #     type_obj = None
    #     if type_id == "DIMMER":
    #         type_obj = LightDimmerType()
    #     elif type_id == "FAN":
    #         fan_speeds = raw_zone["fan_speeds"]
    #         type_obj = FanDeviceType(fan_speeds=fan_speeds)
    #     elif type_id == "SWITCH":
    #         type_obj = SwitchDimmerType()
    #     elif type_id == "QED SHADE":
    #         type_obj = ShadeDimmerType()
    #     else:
    #         raise ValueError(f"zone type id `{type_id}`: not handled!")

    #     assert type_obj is not None
    #     return type_obj

    # def parse_file(self, filepath) -> dict[str, Any]:
    #     with open(filepath, 'r') as file:
    #         return self.parse_yaml(yaml.safe_load(file))


def find_text(element: ET.Element, tag_name: str) -> Optional[str]:
    result = element.find(tag_name)
    if result is None:
        return None
    else:
        return result.text


class HwiXmlParser(object):

    def __init__(self, remap: dict):
        self._remap = remap

    def _remap_str(self, input: Optional[str], key: str) -> Optional[str]:
        if not (key in self._remap):
            return input
        if input is None:
            return None
        if input in self._remap[key]:
            return self._remap[key][input]
        return input

    def _remap_room_name(self, room_name: Optional[str]) -> Optional[str]:
        return self._remap_str(room_name, key='room_names')

    def _remap_button_name(self, button_name: Optional[str]) -> Optional[str]:
        return self._remap_str(button_name, key='button_names')

    def _resolve_zone_addr_from_number(self, zone_num: str) -> Optional[str]:
        element = self._root.find(
            f'.//Area/Room/Outputs/Output[ZoneNum="{zone_num}"]')
        if element is None:
            return None
        zone_addr = element.find('Address')
        if zone_addr is None:
            return None
        return zone_addr.text

    def _parse_output(self, output: ET.Element) -> Tuple[str, dict]:
        output_name = find_text(output, 'Name')
        output_type = find_text(output, 'Type')
        output_address = find_text(output, 'Address')
        output_zone_num = find_text(output, 'ZoneNum')
        assert output_type is not None
        # print(f"\t\tOutput: {output_name}, {output_type}")

        device_dict = {'name': output_name,
                       'address': f"{output_address}",
                       'number': f"{output_zone_num}"}
        return (output_type, device_dict)

    def _parse_keypad_button_zone(self, zone_num_tag: ET.Element) -> dict:
        zone_num_text = zone_num_tag.text
        assert zone_num_text is not None
        # Resolve the zone address from the zone number
        zone_addr_text = self._resolve_zone_addr_from_number(
            zone_num_text)
        assert zone_addr_text is not None

        return {'number': zone_num_text, 'address': zone_addr_text}

    def _parse_keypad_button_zones(self, button: ET.Element) -> list[dict]:
        zones = []
        actions = button.find('Actions')
        assert actions is not None
        presets = actions.find('Presets')
        assert presets is not None
        first_preset = presets.find('Preset')
        if first_preset is not None:
            for zone_num_tag in first_preset.findall('Output/ZoneNum'):
                zones.append(self._parse_keypad_button_zone(zone_num_tag))
        return zones

    def _parse_keypad_button(self, button: ET.Element) -> Optional[dict]:
        button_name = self._remap_button_name(find_text(button, 'Name'))
        number_str = find_text(button, 'Number')
        button_type = find_text(button, 'Type')
        if button_type == 'Not Programmed':
            return None

        zones = self._parse_keypad_button_zones(button)

        assert number_str is not None
        number = int(number_str)
        return {'name': button_name, 'number': number, 'zones': zones}

    def _parse_keypad_buttons(self, buttons_tag: ET.Element) -> list[dict]:
        buttons = []
        for button in buttons_tag.iter('Button'):
            parsed_btn = self._parse_keypad_button(button)
            if parsed_btn is not None:
                buttons.append(parsed_btn)
        return buttons

    def _parse_keypad_device(self, dev: ET.Element, control_station_name: str) -> dict:

        keypad_address = find_text(dev, 'Address')
        keypad_dict = {
            'name': control_station_name, 'address': keypad_address, 'buttons': []}
        buttons_tag = dev.find('Buttons')
        assert buttons_tag is not None
        buttons = self._parse_keypad_buttons(buttons_tag)
        keypad_dict['buttons'] += buttons
        return keypad_dict

    def _parse_control_station(self, input: ET.Element) -> Optional[Tuple[str, dict]]:
        control_station_name = find_text(input, 'Name')
        assert control_station_name is not None
        control_station_devices = input.find('Devices')
        assert control_station_devices is not None
        dev = control_station_devices.find('Device')
        assert dev is not None
        dev_type = find_text(dev, 'Type')
        # dev_type 'DIMMER/SWITCH' is basic wall dimmer switch
        if dev_type == 'KEYPAD':
            return (dev_type, self._parse_keypad_device(dev, control_station_name))
        else:
            _LOGGER.warning(
                f'Skipped unsupported device type {dev_type} found in ControlStation: {control_station_name}')
            return None

    def parse_file(self, xml_file) -> dict:
        tree = ET.parse(xml_file)
        self._root = tree.getroot()

        devices = {}
        for area in self._root.iter('Area'):
            area_name = find_text(area, 'Name')
            # print(f"Area: {area_name}")
            for room in area.iter('Room'):
                room_devices = {'dimmers': [], 'fans': [],
                                'shades': [], 'switches': [], 'keypads': []}
                room_name = self._remap_room_name(find_text(room, 'Name'))

                # print(f"\tRoom: {room_name}")
                outputs = room.find('Outputs')
                if outputs is not None:
                    for output in outputs.iter('Output'):
                        output_type, device_dict = self._parse_output(output)
                        if output_type == 'DIMMER':
                            room_devices['dimmers'].append(device_dict)
                        elif output_type == 'SWITCH':
                            room_devices['switches'].append(device_dict)
                        elif output_type == 'FAN':
                            room_devices['fans'].append(device_dict)
                        elif output_type == 'QED SHADE':
                            room_devices['shades'].append(device_dict)
                        else:
                            raise ValueError(
                                f'Unknown output type: {output_type}')

                inputs = room.find('Inputs')
                if inputs is not None:
                    for input in inputs.iter('ControlStation'):
                        dev_tuple = self._parse_control_station(input)
                        if dev_tuple is None:
                            continue
                        dev_type, dev_dict = dev_tuple
                        if dev_type == "KEYPAD":
                            room_devices['keypads'].append(dev_dict)

                if room_name in devices:
                    dict_to_merge = {
                        k: v for k, v in room_devices.items() if len(v) != 0}
                    dict_orig = devices[room_name]
                    for key, value in dict_to_merge.items():
                        if key not in dict_orig:
                            dict_orig[key] = value
                        else:
                            dict_orig[key] += value
                    devices[room_name] = dict_orig
                else:
                    devices[room_name] = {
                        k: v for k, v in room_devices.items() if len(v) != 0}

        return {'devices': devices}
