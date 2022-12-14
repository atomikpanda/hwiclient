from enum import Enum
from typing import Any, Optional, Protocol, Tuple
import logging
_LOGGER = logging.getLogger(__name__)


class DeviceEventKind(str, Enum):
    DIMMER_LEVEL_CHANGED = "dimmer_level_changed"
    KEYPAD_LED_STATES_CHANGED = "keypad_led_states_changed"
    KEYPAD_BUTTON_PRESSED = "keypad_button_pressed"
    KEYPAD_BUTTON_RELEASED = "keypad_button_released"
    KEYPAD_BUTTON_HELD = "keypad_button_held"
    KEYPAD_BUTTON_DOUBLE_TAPPED = "keypad_button_double_tapped"
    DEVICE_GROUP_DIMMER_LEVEL_CHANGED = "device_group_dimmer_level_changed"


class DeviceEventKey(str, Enum):
    DEVICE_ADDRESS = "address"
    DIMMER_LEVEL = "level"
    KEYPAD_LED_STATES = "keypad_led_states"
    BUTTON_NUMBER = "button"
    DEVICE = "device"
    DEVICE_GROUP = "device_group"


class TimeclockEventKind(str, Enum):
    TIMECLOCK_SUNRISE = "timeclock_sunrise"
    TIMECLOCK_SUNSET = "timeclock_sunset"
    TIMECLOCK_REALTIME = "timeclock_realtime"


class TimeclockEventKey(str, Enum):
    RAW_DATA = "raw_data"


class EventListener(Protocol):
    def on_event(self, kind: str, data: dict):
        pass


class EventSource(Protocol):
    def register_listener(self, listener: EventListener, filter: Optional[dict] = None, *kind: str):
        pass

    def unregister_listener(self, listener: EventListener, *kind: str):
        pass


class DeviceEventSource(EventSource):

    def __init__(self):
        self._listeners: dict[DeviceEventKind,
                              list[Tuple[EventListener, Optional[dict]]]] = {}

    def _passes_filter(self, data, filter: dict) -> bool:
        result = True
        for key, value in filter.items():
            if key not in data:
                return False

            if data[key] == value:
                result = result and True
            else:
                return False
        return result

    def post(self, kind: DeviceEventKind, data: dict):
        _LOGGER.warning(f"POST {kind} data={data}")
        if kind not in self._listeners:
            return
        for listener, filter in self._listeners[kind]:
            if filter != None and self._passes_filter(data, filter):
                _LOGGER.debug("FILTER PASSED: %s", filter)
                listener.on_event(kind, data)
            else:
                _LOGGER.debug("NO FILTER")
                listener.on_event(kind, data)

    def register_listener(self, listener: EventListener, filter: Optional[dict] = None, *kind: DeviceEventKind):
        for event_kind in kind:
            if event_kind in self._listeners:
                self._listeners[event_kind].append((listener, filter))
            else:
                self._listeners[event_kind] = [(listener, filter)]

    def _unregister_listener(self, listener: EventListener, event_kind: DeviceEventKind):
        if event_kind in self._listeners:
            for index, (event_listener, filter) in enumerate(self._listeners[event_kind]):
                if event_listener == listener:
                    self._listeners[event_kind].pop(index)
                    return

    def unregister_listener(self, listener: EventListener, *kind: DeviceEventKind):
        for event_kind in kind:
            self._unregister_listener(listener, event_kind)
