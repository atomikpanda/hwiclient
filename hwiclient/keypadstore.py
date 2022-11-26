import hwiclient.models as models
from typing import Optional
class DeviceRepository(object):
    # _instance = None
    
    def __init__(self):
        self._parsed_objects = {}
        self._shade_objects = {}
        self._zone_objects = {}

    def set_parsed_objects(self, objs):
        self._parsed_objects = objs

    def set_zone_objects(self, objs):
        self._zone_objects = objs

    def set_shade_objects(self, objs):
        self._shade_objects = objs

    def get_keypad_named(self, keypad_name: str) -> Optional[models.HwiKeypad]:
        for keypad_address, keypad in self._parsed_objects.items():
            if keypad.name == keypad_name:
                return keypad
        return None

    def get_keypad_at_address(self, keypad_address: str) -> Optional[models.HwiKeypad]:
        if keypad_address in self._parsed_objects:
            return self._parsed_objects[keypad_address]
        else:
            return None

    def get_shade_at_address(self, shade_address) -> Optional[models.HwiShade]:
        if shade_address in self._shade_objects:
            return self._shade_objects[shade_address]
        else:
            return None

    def get_zone_at_address(self, zone_address) -> Optional[models.HwiZone]:
        if zone_address in self._zone_objects:
            return self._zone_objects[zone_address]
        else:
            return None

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
