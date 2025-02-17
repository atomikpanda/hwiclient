from hwiclient.utils import HwiUtils
import pytest


def test_brightness_to_percent():
    assert HwiUtils.brightness_to_percent(0) == 0
    assert HwiUtils.brightness_to_percent(255) == 100
    assert HwiUtils.brightness_to_percent(128) == pytest.approx(50, 0.1)


def test_percent_to_brightness():
    assert HwiUtils.percent_to_brightness(0) == 0
    assert HwiUtils.percent_to_brightness(100) == 255
    assert HwiUtils.percent_to_brightness(50) == pytest.approx(128, 0.1)


def test_keypad_address_components():
    keypad_addr = "01:02:03"
    components = HwiUtils.keypad_address_components(keypad_addr)
    assert isinstance(components, tuple)
    assert len(components) == 3
    assert all(isinstance(component, str) for component in components)
    assert components == ("1", "2", "3")

    keypad_addr_2 = "1:2:3"
    components_2 = HwiUtils.keypad_address_components(keypad_addr_2)
    assert components_2 == ("1", "2", "3")


def test_shade_address_components():
    shade_addr = "01:02:03:04"
    components = HwiUtils.shade_address_components(shade_addr)
    assert isinstance(components, tuple)
    assert len(components) == 4
    assert all(isinstance(component, str) for component in components)
    assert components == ("1", "2", "3", "4")

    shade_addr_2 = "1:2:3:4"
    components_2 = HwiUtils.shade_address_components(shade_addr_2)
    assert components_2 == ("1", "2", "3", "4")


def test_zone_address_components():
    zone_addr = "01:02:03:04:05"
    components = HwiUtils.zone_address_components(zone_addr)
    assert isinstance(components, tuple)
    assert len(components) == 5
    assert all(isinstance(component, str) for component in components)
    assert components == ("1", "2", "3", "4", "5")

    zone_addr_2 = "1:2:3:4:5"
    components_2 = HwiUtils.zone_address_components(zone_addr_2)
    assert components_2 == ("1", "2", "3", "4", "5")
