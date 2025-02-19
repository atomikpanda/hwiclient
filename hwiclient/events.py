import logging
from abc import abstractmethod
from enum import StrEnum
from typing import Optional, Protocol

_LOGGER = logging.getLogger(__name__)


class DeviceEventKind(StrEnum):
    DIMMER_LEVEL_CHANGED = "dimmer_level_changed"
    KEYPAD_LED_STATES_CHANGED = "keypad_led_states_changed"
    KEYPAD_BUTTON_PRESSED = "keypad_button_pressed"
    KEYPAD_BUTTON_RELEASED = "keypad_button_released"
    KEYPAD_BUTTON_HELD = "keypad_button_held"
    KEYPAD_BUTTON_DOUBLE_TAPPED = "keypad_button_double_tapped"
    DEVICE_GROUP_DIMMER_LEVEL_CHANGED = "device_group_dimmer_level_changed"


class DeviceEventKey(StrEnum):
    DEVICE_ADDRESS = "address"
    DIMMER_LEVEL = "level"
    KEYPAD_LED_STATES = "keypad_led_states"
    BUTTON_NUMBER = "button"
    DEVICE = "device"
    DEVICE_GROUP = "device_group"


class TimeclockEventKind(StrEnum):
    TIMECLOCK_SUNRISE = "timeclock_sunrise"
    TIMECLOCK_SUNSET = "timeclock_sunset"
    TIMECLOCK_REALTIME = "timeclock_realtime"


class TimeclockEventKey(StrEnum):
    RAW_DATA = "raw_data"


class EventListener(Protocol):
    def on_event(self, kind: str, data: dict):
        pass


class EventSource(Protocol):
    @abstractmethod
    def register_listener(
        self, listener: EventListener, filter: Optional[dict] = None, *kind: str
    ):
        pass

    @abstractmethod
    def unregister_listener(self, listener: EventListener, *kind: str):
        pass


class FilteredListener(EventListener):
    def __init__(self, listener: EventListener, filter: dict):
        self._listener = listener
        self._filter = filter

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

    def on_event(self, kind: str, data: dict):
        if self._passes_filter(data, self._filter):
            self._listener.on_event(kind, data)


class DeviceEventSource(EventSource):
    def __init__(self):
        self._listeners: dict[DeviceEventKind, list[EventListener]] = {}

    # def _passes_filter(self, data, filter: dict) -> bool:
    #     result = True
    #     for key, value in filter.items():
    #         if key not in data:
    #             return False

    #         if data[key] == value:
    #             result = result and True
    #         else:
    #             return False
    #     return result

    def is_listener_registered(self, listener: EventListener, kind: str) -> bool:
        event_kind = DeviceEventKind(kind)
        if event_kind is None:
            return False
        return listener in self._listeners[event_kind]

    def post(self, kind: DeviceEventKind, data: dict):
        if kind not in self._listeners:
            return

        for listener in self._listeners[kind]:
            listener.on_event(kind, data)

    def register_listener(
        self, listener: EventListener, filter: Optional[dict] = None, *kind: str
    ):
        # check if kind is DeviceEventKind
        for event_kind in kind:
            if not isinstance(event_kind, DeviceEventKind):
                raise ValueError(f"Invalid event kind: {event_kind}")
        _LOGGER.debug("Register listener %s with filter %s", listener, filter)
        listener_to_register = (
            FilteredListener(listener, filter) if filter is not None else listener
        )
        for event_kind in kind:
            assert isinstance(event_kind, DeviceEventKind)
            if event_kind in self._listeners:
                self._listeners[event_kind].append(listener_to_register)
            else:
                self._listeners[event_kind] = [listener_to_register]

    def _unregister_listener(
        self, listener: EventListener, event_kind: DeviceEventKind
    ):
        if event_kind in self._listeners:
            for index, event_listener in enumerate(self._listeners[event_kind]):
                if event_listener == listener:
                    self._listeners[event_kind].pop(index)
                    return

    def unregister_listener(self, listener: EventListener, *kind: str):
        for event_kind in kind:
            assert isinstance(event_kind, DeviceEventKind)
            self._unregister_listener(listener, event_kind)
