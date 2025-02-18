import re


class HwiUtils(object):
    @staticmethod
    def calculate_zones_brightness_percent(zones):
        # num_zones = len(zones)
        max_percent = 0
        for zone in zones:
            if zone.is_dimmable:
                max_percent = max(max_percent, zone.level)

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
        return re.findall(
            "0?(\\d{1,2}):0?(\\d{1,2}):0?(\\d{1,2}):0?(\\d{1,2})", shade_addr
        )[0]

    @staticmethod
    def zone_address_components(zone_addr):
        comp = re.findall(
            "0?(\\d{1,2}):0?(\\d{1,2}):0?(\\d{1,2}):0?(\\d{1,2}):0?(\\d{1,2})",
            zone_addr,
        )
        if len(comp) == 0:
            return HwiUtils.shade_address_components(zone_addr)
        else:
            return comp[0]

    @staticmethod
    def _remove_prefix(text, prefix):
        return text[text.startswith(prefix) and len(prefix) :]

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
        return (
            HwiUtils.encode_keypad_address(button.keypad.address)
            + "_btn_"
            + str(button.number)
        )

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
