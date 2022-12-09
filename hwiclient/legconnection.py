from __future__ import annotations
from .utils import HwiUtils
from abc import ABC, abstractmethod
from typing import Any, Optional, TYPE_CHECKING, Protocol
from twisted.internet import reactor
import logging
from threading import Thread
from .telnet import TelnetClientCommand
from .commands.system import LoginCommand
from enum import Enum
from .monitoring import TopicNotifier, MonitoringTopic, MonitoringTopicKey
_LOGGER = logging.getLogger(__name__)


if TYPE_CHECKING:
    from .hub import Hub, EventBus




class TcpConnectionManager(ConnectionStateListener):

    def __init__(self, hub: Hub, bus: EventBus):
        self._hub = hub
        self._bus = bus
        self._state = ConnectionState.NOT_CONNECTED
        self._keep_connected = True
        self._has_enabled_monitoring = False
        self._cmd = None
        self._sender = HwiPacketSender(self)
        self._receiver = HwiPacketReceiver(
            self, self._hub, self._bus,
            listener=self)

    def on_connection_state_changed(self, old_state: ConnectionState, new_state: ConnectionState):
        self._state = new_state

        if new_state == ConnectionState.CONNECTED_READY_FOR_LOGIN_ATTEMPT:
            LoginCommand(self._username,
                         self._password).execute(self._hub)
        if old_state == ConnectionState.CONNECTED_LOGGED_IN and new_state == ConnectionState.CONNECTED_READY_FOR_COMMAND:
            if self._has_enabled_monitoring == False:
                self._has_enabled_monitoring = True
                self._sender.send_monitor_packet()

        if self._listener != None:
            self._listener.on_connection_state_changed(old_state, new_state)

    def connect_and_attempt_login(self, host: str, port: int, username: str, password: str, listener: ConnectionStateListener):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._listener = listener
        self._cmd = TelnetClientCommand("", '', self)
        self._cmd.connect(self._host, self._port)

        Thread(target=reactor.run, args=(False,)).start()  # type: ignore

    @property
    def sender(self) -> HwiPacketSender:
        return self._sender

    @property
    def receiver(self) -> HwiPacketReceiver:
        return self._receiver

    def send_command_with_args(self, command_name: str, args: list[str]):
        self._sender.send_command_with_args(command_name, args)

    def send_packet(self, packet: str) -> None:
        self._sender.send_packet_str(packet)

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def ready(self) -> bool:
        return self._state == ConnectionState.CONNECTED_READY_FOR_COMMAND


class PacketSender(ABC):
    @abstractmethod
    def send_packet_str(self, string: str, include_return=True):
        pass


class PacketReceiver(ABC):
    @abstractmethod
    def on_packet_received(self, string: str):
        # _LOGGER.warning("got packet " + string)
        pass


class HwiPacketSender(PacketSender):
    from .device import DeviceAddress

    def __init__(self, connection: TcpConnectionManager):
        self._connection = connection

    def send_packet_str(self, string: str):
        reactor.callFromThread(self._connection._cmd.send_packet_str, string)

    def send_monitor_packet(self):
        self.send_packet_str("DLMON\r\nKBMON\r\nKLMON\r\nGSMON\r\nTEMON")
        pass

    def send_command_with_args(self, command_name: str, args: list[str]):
        if len(args) > 0:
            self.send_packet_str(command_name+","+",".join(args))
        else:
            self.send_packet_str(command_name)


class HwiPacketReceiver(PacketReceiver):
    _cmd_prompt = "LNET>"
    _login_prompt = "LOGIN:"
    _has_enabled_monitoring = False

    def __init__(self, connection: TcpConnectionManager, hub: Hub, bus: EventBus, listener: ConnectionStateListener):
        self._manager = connection
        self._hub = hub
        self._bus = bus
        self._has_called_callback = False
        self._listener = listener
        self._notifier: TopicNotifier = hub

    def get_sender(self) -> HwiPacketSender:
        sender = self._manager.sender
        assert sender is not None
        return sender

    def is_known_command(self, string: str) -> bool:
        stripped = string.strip().split(",")
        return len(stripped) > 0 and stripped[0] in self._handlers

    def on_packet_received(self, string: str):
        if string == self._cmd_prompt:
            self.on_ready_for_command()
        elif string == self._login_prompt:
            self.on_ready_for_login()
        elif string == "login successful":
            self.on_logged_in()
        elif string == "login incorrect":
            self.on_login_incorrect()
        elif string.startswith("Timeclock"):
            self.on_timeclock_event(string)
        elif self.is_known_command(string):
            self.on_packet_with_args_received(string)
        else:
            _LOGGER.warning("unknown packet received: `" + string + "`")

    def on_packet_with_args_received(self, packet_str):
        args = list(map(lambda e: e.strip(), packet_str.strip().split(",")))
        cmd_name = args[0]
        handler = self._handlers[cmd_name]
        args.pop(0)
        if handler != None:
            handler(self, args)
        pass

    def on_ready_for_command(self):
        _LOGGER.warning("ready for command")
        self._listener.on_connection_state_changed(
            self._manager.state, ConnectionState.CONNECTED_READY_FOR_COMMAND)

    def on_ready_for_login(self):
        self._listener.on_connection_state_changed(
            self._manager.state, ConnectionState.CONNECTED_READY_FOR_LOGIN_ATTEMPT)
        _LOGGER.warning("ready to login")

    def on_logged_in(self):
        self._listener.on_connection_state_changed(
            self._manager.state, ConnectionState.CONNECTED_LOGGED_IN)

    def on_login_incorrect(self):
        # we dont need to resend login since the pipe will auto write LOGIN: prompt
        pass

    def on_timeclock_event(self, string: str):
        if string.startswith("Timeclock Sunset Event"):
            # Sunset event
            _LOGGER.warning("Captured timeclock sunset")
            self._bus.fire("hwi_timeclock_event", {
                "kind": "sunset", "raw_data": string})
        elif string.startswith("Timeclock Real Time Event"):
            _LOGGER.warning("Captured timeclock real time")
            self._bus.fire("hwi_timeclock_event", {
                "kind": "realtime", "raw_data": string})
        elif string.startswith("Timeclock Sunrise Event"):
            _LOGGER.warning("Captured timeclock sunrise")
            self._bus.fire("hwi_timeclock_event", {
                "kind": "sunrise", "raw_data": string})
        pass

    def on_keypad_led_status_update(self, args):
        _LOGGER.warning("got keypad LED status: " + str(args))
        # Notify any entity that is on this keypad of the change
        if len(args) >= 2:
            keypad_addr = args[0]
            led_states = args[1]
            self._notifier.notify_subscribers(MonitoringTopic.KEYPAD_LED_STATES_CHANGED,
                                              data={MonitoringTopicKey.ADDRESS: str(keypad_addr),
                                                    MonitoringTopicKey.LED_STATES: led_states})

    def on_keypad_button_press(self, args):
        _LOGGER.warning("keypad button pressed " + str(args))
        # Notify any entity that is on this keypad of the change
        if len(args) >= 2:
            keypad_addr = args[0]
            button_num = int(args[1])
            data = {MonitoringTopicKey.ADDRESS: str(
                keypad_addr), MonitoringTopicKey.BUTTON: button_num}
            self._notifier.notify_subscribers(MonitoringTopic.KEYPAD_BUTTON_PRESS,
                                              data=data)

    def on_keypad_button_release(self, args):
        _LOGGER.warning("keypad button released " + str(args))
        # Notify any entity that is on this keypad of the change
        if len(args) >= 2:
            keypad_addr = args[0]
            button_num = int(args[1])
            data = {MonitoringTopicKey.ADDRESS: str(
                keypad_addr), MonitoringTopicKey.BUTTON: button_num}
            self._notifier.notify_subscribers(MonitoringTopic.KEYPAD_BUTTON_RELEASE,
                                              data=data)

    def on_keypad_button_double_tap(self, args):
        # KBDT, [01:06:11], 23
        if len(args) >= 2:
            keypad_addr = args[0]
            button_num = int(args[1])
            data = {MonitoringTopicKey.ADDRESS: str(
                keypad_addr), MonitoringTopicKey.BUTTON: button_num}
            self._notifier.notify_subscribers(MonitoringTopic.KEYPAD_BUTTON_DOUBLE_TAP,
                                              data=data)

    def on_keypad_button_hold(self, args):
        # KBH, [01:06:11], 2
        if len(args) >= 2:
            keypad_addr = args[0]
            button_num = int(args[1])
            data = {MonitoringTopicKey.ADDRESS: str(
                keypad_addr), MonitoringTopicKey.BUTTON: button_num}
            self._notifier.notify_subscribers(MonitoringTopic.KEYPAD_BUTTON_HOLD,
                                              data=data)

    def on_dimmer_level_update(self, args):
        _LOGGER.warning("dimmer level update: " + str(args))
        dimmer_address = args[0]
        level = float(args[1])
        data = {MonitoringTopicKey.ADDRESS: str(
                dimmer_address), MonitoringTopicKey.LEVEL: level}
        self._notifier.notify_subscribers(MonitoringTopic.DIMMER_LEVEL_CHANGED,
                                          data=data)

    _handlers = {
        MonitoringTopic.KEYPAD_LED_STATES_CHANGED: on_keypad_led_status_update,
        MonitoringTopic.DIMMER_LEVEL_CHANGED: on_dimmer_level_update,
        MonitoringTopic.KEYPAD_BUTTON_PRESS: on_keypad_button_press,
        MonitoringTopic.KEYPAD_BUTTON_RELEASE: on_keypad_button_release,
        MonitoringTopic.KEYPAD_BUTTON_DOUBLE_TAP: on_keypad_button_double_tap,
        MonitoringTopic.KEYPAD_BUTTON_HOLD: on_keypad_button_hold
    }

    pass
