import re
from bisect import bisect_left


def take_closest(myList, myNumber):
    """
    Assumes myList is sorted. Returns closest value to myNumber.

    If two numbers are equally close, return the smallest number.
    """
    pos = bisect_left(myList, myNumber)
    if pos == 0:
        return myList[0]
    if pos == len(myList):
        return myList[-1]
    before = myList[pos - 1]
    after = myList[pos]
    if after - myNumber < myNumber - before:
        return after
    else:
        return before
    
class HwiUtils(object):

    @staticmethod
    def calculate_zones_brightness_percent(zones):
        num_zones = len(zones)
        max_percent = 0
        for zone in zones:
            if zone.zone_type == "DIMMER" or zone.zone_type == "FAN":
                max_percent = max(max_percent, zone.brightness_percent)

        return max_percent

    @staticmethod
    def brightness_to_percent(brightness):
        bri_max = 255
        bri_min = 0
        percent = ((brightness - bri_min) * 100) / (bri_max - bri_min)
        return percent

    @staticmethod
    def percent_to_brightness(percent):
        bri_max = 255
        bri_min = 0
        return (percent * (bri_max - bri_min) / 100) + bri_min

    @staticmethod
    def keypad_address_components(keypad_addr):
        return re.findall("0?(\\d{1,2}):0?(\\d{1,2}):0?(\\d{1,2})", keypad_addr)[0]

    @staticmethod
    def shade_address_components(shade_addr):
        return re.findall("0?(\\d{1,2}):0?(\\d{1,2}):0?(\\d{1,2}):0?(\\d{1,2})", shade_addr)[0]

    @staticmethod
    def zone_address_components(zone_addr):
        comp = re.findall(
            "0?(\\d{1,2}):0?(\\d{1,2}):0?(\\d{1,2}):0?(\\d{1,2}):0?(\\d{1,2})", zone_addr)
        if len(comp) == 0:
            return HwiUtils.shade_address_components(zone_addr)
        else:
            return comp[0]

    @staticmethod
    def _remove_prefix(text, prefix):
        return text[text.startswith(prefix) and len(prefix):]

    @staticmethod
    def encode_keypad_address(keypad_addr):
        components = HwiUtils.keypad_address_components(keypad_addr)
        return "keypad_" + ("_".join(components))

    @staticmethod
    def encode_shade_address(shade_addr):
        components = HwiUtils.shade_address_components(shade_addr)
        return "shade_" + ("_".join(components))

    @staticmethod
    def encode_zone_address(zone_addr):
        components = HwiUtils.zone_address_components(zone_addr)
        return "zone_" + ("_".join(components))

    @staticmethod
    def encode_keypad_button(button):
        return HwiUtils.encode_keypad_address(button.keypad.address) + "_btn_" + str(button.number)

    @staticmethod
    def decode_keypad_address(encoded_keypad_addr):
        removed = HwiUtils._remove_prefix(encoded_keypad_addr, "keypad_")
        return "[" + (":".join(removed.split("_"))) + "]"

    @staticmethod
    def decode_shade_address(encoded_shade_addr):
        removed = HwiUtils._remove_prefix(encoded_shade_addr, "shade_")
        return "[" + (":".join(removed.split("_"))) + "]"

    @staticmethod
    def decode_zone_address(encoded_zone_addr):
        removed = HwiUtils._remove_prefix(encoded_zone_addr, "zone_")
        return "[" + (":".join(removed.split("_"))) + "]"

    @staticmethod
    def safe_fan_brightness(num_speeds_excluding_zero, brightness_percent):
        increment = 100.0/float(num_speeds_excluding_zero)
        safe_speeds = []
        for i in range(0, int(num_speeds_excluding_zero) + 1):
            safe_speeds.append(increment * i)

        return take_closest(safe_speeds, brightness_percent)

    @staticmethod
    def safe_fan_brightness_legacy(brightness_percent):

        if brightness_percent < 20:
            return 0  # off
        elif brightness_percent >= 20 and brightness_percent < 40:
            return 25  # low
        elif brightness_percent >= 40 and brightness_percent < 60:
            return 50  # med
        elif brightness_percent >= 60 and brightness_percent < 80:
            return 75  # med high
        elif brightness_percent >= 80 and brightness_percent <= 110:
            return 100  # high
        else:
            return 0
