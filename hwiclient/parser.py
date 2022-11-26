from hwiclient import utils
from hwiclient import keypadstore
from hwiclient import models
from typing import Any

import yaml
import logging
_LOGGER = logging.getLogger(__name__)


class HwiYamlParser(object):
    def parse_yaml(self, yaml_dict) -> dict[str, Any]:
        try:
            keypads = yaml_dict["keypads"]

            parsed_objects: dict[str, Any] = {}
            for keypad_name, keypad in keypads.items():
                keypad_builder = models.HwiKeypadBuilder()
                keypad_builder.set_name(keypad_name)
                keypad_builder.set_address(keypad["address"])

                if "buttons" in keypad:  # and keypad_name == "Master Bedroom 1":
                    raw_buttons = keypad["buttons"]
                    buttons = []
                    for i, button in enumerate(raw_buttons):
                        raw_zones = []
                        button_builder = models.HwiButtonBuilder()
                        button_builder.set_name(button["name"])
                        button_builder.set_number(button["number"])

                        if "zones" in button:
                            raw_zones = button["zones"]

                        if raw_zones != None:
                            for raw_zone in raw_zones:

                                zone = keypadstore.DeviceRepository().get_zone_at_address(
                                    utils.HwiUtils.encode_zone_address(raw_zone["address"]))
                                if zone == None:
                                    zone = models.HwiZone(
                                        raw_zone["number"], raw_zone["address"], raw_zone["type"])
                                    keypadstore.DeviceRepository()._zone_objects[utils.HwiUtils.encode_zone_address(
                                        raw_zone["address"])] = zone

                                button_builder.append_zone(zone)
                                pass
                        keypad_builder.append_button(button_builder)

                    parsed_objects[utils.HwiUtils.encode_keypad_address(
                        keypad['address'])] = keypad_builder.build()
                    buttons = []
                pass

            return parsed_objects

        except yaml.YAMLError as e:
            _LOGGER.error(e)
            raise e

    def parse_file(self, filepath) -> dict[str, Any]:
        with open(filepath, 'r') as file:
            return self.parse_yaml(yaml.safe_load(file))

# TODO: write XML parser import xml.dom.minidom
# https://www.guru99.com/manipulating-xml-with-python.html
