from typing import Callable, Optional
from .monitoring import MonitoringTopicNotifier, MonitoringTopic, MonitoringTopicKey

class ServerResponseDataHandler:
    def __init__(self, notifier: MonitoringTopicNotifier) -> None:
        self._notifier = notifier
        self._handlers = {}
        self._register_handlers()

    def _register_handler(self, handler: Callable, command_name: str):
        self._handlers[command_name] = handler

    def _register_handlers(self):
        self._register_handler(self._keypad_btn_handler,
                               MonitoringTopic.KEYPAD_BUTTON_PRESS)
        self._register_handler(self._keypad_btn_handler,
                               MonitoringTopic.KEYPAD_BUTTON_DOUBLE_TAP)
        self._register_handler(self._keypad_btn_handler,
                               MonitoringTopic.KEYPAD_BUTTON_HOLD)
        self._register_handler(self._keypad_btn_handler,
                               MonitoringTopic.KEYPAD_BUTTON_RELEASE)
        self._register_handler(
            self._keypad_led_states_changed_handler, MonitoringTopic.KEYPAD_LED_STATES_CHANGED)

        self._register_handler(
            self._dimmer_level_changed_handler, MonitoringTopic.DIMMER_LEVEL_CHANGED)

    def handle(self, data: str):
        args = list(map(lambda e: e.strip(), data.strip().split(",")))
        cmd_name = args[0]
        if cmd_name in self._handlers:
            handler = self._handlers[cmd_name]
            args.pop(0)
            if handler != None:
                print(f"Calling handler {args}")
                handler_data = handler(*args)
                topic = MonitoringTopic(cmd_name)
                self._notifier.notify_subscribers(topic,
                                                  data=handler_data)
        else:
            print("Unknown command: " + data)

    def _keypad_btn_handler(self, keypad_addr: str, button_num: str) -> Optional[dict]:
        return {MonitoringTopicKey.ADDRESS: keypad_addr,
                MonitoringTopicKey.BUTTON: int(button_num)}

    def _keypad_led_states_changed_handler(self, keypad_addr: str, led_states: str) -> Optional[dict]:
        return {MonitoringTopicKey.ADDRESS: keypad_addr,
                MonitoringTopicKey.LED_STATES: led_states}

    def _dimmer_level_changed_handler(self, dimmer_addr: str, level: str) -> Optional[dict]:
        return {MonitoringTopicKey.ADDRESS: dimmer_addr, MonitoringTopicKey.LEVEL: float(level)}
