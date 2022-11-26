from __future__ import annotations
from twisted.internet import defer, reactor
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.protocol import ClientFactory
from twisted.conch.telnet import TelnetTransport, StatefulTelnetProtocol
from twisted.python import log
import logging
from threading import Thread
from typing import Optional
from . import utils
HwiUtils = utils.HwiUtils

_LOGGER = logging.getLogger(__name__)

from .. import keypadstore
from . import models
HwiKeypadStore = keypadstore.HwiKeypadStore

class Hub(object):
    from homeassistant.core import HomeAssistant
    def __init__(self, hass: HomeAssistant, host: str, port: int, username: str, password: str) -> None:
        self._hass = hass
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        
    def get_keypad_at_address(self, keypad_address) -> Optional[models.HwiKeypad]:
        return HwiKeypadStore().get_keypad_at_address(keypad_address)
    
    @property
    def sender(self) -> HwiPacketSender:
        return HwiTcpManager().sender
    

class SenderAdapter(object):
    def __init__(self, packet_sender: HwiPacketSender):
        self._packet_sender = packet_sender
        
    def press_button(self, button: models.HwiButton):
        self._packet_sender.send_keypad_button_press(button.keypad.address, button.number)

class HwiTcpManager(object):
    _instance = None
    _keep_connected = True
    login_state = "not_logged_in"
    sender: Optional[HwiPacketSender] = None
    receiver = None
    cmd = None

    @property
    def logged_in(self) -> bool:
        return HwiTcpManager().login_state == "logged_in"

    def setup(self, host, port, username, password, hass):
        if self.sender != None:
            _LOGGER.warning("WARNING SETUP CALLED MORE THAN ONCE")

        self._host = host
        self._port = port
        self._username = username
        self._password = password

        self.sender = HwiPacketSender()
        self.receiver = HwiPacketReceiver(hass)
        self.cmd = TelnetClientCommand("", '')
        self.cmd.connect(self._host, self._port)

        Thread(target=reactor.run, args=(False,)).start()

        pass

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HwiTcpManager, cls).__new__(cls)
            _LOGGER.warning("NEW INSTANCE OF TCP MANAGER")
            # Put any initialization here.
        return cls._instance

class TelnetConnectionError(Exception):
    pass


class TelnetClient(StatefulTelnetProtocol):
    def __init__(self):
        self.login_deferred = None
        self.command_deferred = None

        self.command = b''
        self.response = b''

        self.done_callback = None

    def connectionMade(self):
        """
        Set rawMode since we do not receive the login and password prompt in line mode.
        We return to default line mode when we detect the prompt in the received data stream.
        """
        self.setRawMode()

    def rawDataReceived(self, bytes):
        self.on_packet_received(bytes.decode("utf-8"))
        return

        # second deferred, fired to signal auth is done
        self.login_deferred.callback(True)

    def on_packet_received(self, string):
        for line in string.strip().splitlines():
            # SUPER HELPFUL FOR DEBUGGING
            _LOGGER.warning("`"+line+"`")
            if len(line.strip()) != 0:
                # I THINK THIS MIGHT NEED TO BE CALLED ON MAIN THREAD
                reactor.callInThread(
                    HwiTcpManager().receiver.on_packet_received, line.strip())
                # HwiTcpManager().receiver.on_packet_received(line.strip())
        pass

    def send_command(self, command):
        """
        Sends a command via Telnet using line mode
        """
        self.command = command.encode()
        self.sendLine(self.command)

    def send_packet_str(self, string, include_return=True):
        self.command = str.encode(string)  # + "\r\n"
        _LOGGER.warning("send: `"+string+"`")
        self.sendLine(self.command)
        pass

    def close(self):
        """
        Sends exit to the Telnet server and closes connection.
        Fires the deferred with the command's output.
        """
        self.sendLine(b'exit')
        self.factory.transport.loseConnection()

        # third deferred, to signal command's output was fully received
        self.command_deferred.callback(self.response)


class TelnetFactory(ClientFactory):
    def __init__(self):
        self.transport = None

    def buildProtocol(self, addr):
        self.transport = TelnetTransport(TelnetClient)
        self.transport.factory = self
        return self.transport

    def clientConnectionLost(self, connector, reason):
        _LOGGER.warning('Lost telnet connection.  Reason: %s ' % reason)

    def clientConnectionFailed(self, connector, reason):
        _LOGGER.warning('Telnet connection failed. Reason:%s ' % reason)


class TelnetClientCommand:
    def __init__(self, prompt, command):
        self.connection_deferred = None

        self.login_deferred = defer.Deferred()
        self.login_deferred.addCallback(self.send_command)

        self.command_deferred = defer.Deferred()
        self.command_deferred.addCallback(self.received_response)

        self.transport = None
        self.prompt = prompt
        self.command = command

    def connect(self, host, port):
        def check_connection_state(transport):
            """Since we can't use the telnet connection before we have
            logged in and the client is in line_mode 1
            we pause the connection_deferred here until the client is ready
            The client unpuase the defer when wee are logged in
            """
            if transport.protocol.line_mode == 1:
                return transport

            transport.protocol.connected_deferred = self.connection_deferred
            return transport

        def connection_failed(reason):
            _LOGGER.warning(reason)
            raise TelnetConnectionError(reason)

        # start connection to the Telnet server
        _LOGGER.warning("start connection")
        endpoint = TCP4ClientEndpoint(reactor, host, port, 30)
        telnetFactory = TelnetFactory()
        telnetFactory.protocol = TelnetClient
        self.connection_deferred = endpoint.connect(telnetFactory)

        # first deferred, fired on connection
        self.connection_deferred.addCallback(check_connection_state)
        self.connection_deferred.addErrback(connection_failed)
        self.connection_deferred.addCallback(self.start_protocol)

    def start_protocol(self, protocol):
        self.transport = protocol.protocol
        self.transport.login_deferred = self.login_deferred
        self.transport.command_deferred = self.command_deferred

    def send_command(self, _):
        self.transport.send_command(self.command)

    def send_packet_str(self, string, include_return=True):
        self.transport.send_packet_str(string, include_return)
        pass

    def received_response(self, response):
        _LOGGER.warning("received response: " + response)
        # HwiTcpManager().receiver.on_packet_received(response)


class PacketSender(object):
    def send_packet_str(self, string, include_return=True):
        pass


class PacketReceiver(object):
    def on_packet_received(self, string):
        # _LOGGER.warning("got packet " + string)
        pass


class HwiPacketSender(PacketSender):

    def send_packet_str(self, string, include_return=True):
        reactor.callFromThread(HwiTcpManager().cmd.send_packet_str, string)
        pass

    def send_login_packet(self):
        self.send_packet_str(HwiTcpManager()._username +
                             "," + HwiTcpManager()._password)
        pass

    def send_monitor_packet(self):
        self.send_packet_str("DLMON\r\nKBMON\r\nKLMON\r\nGSMON\r\nTEMON")
        pass

    def send_command_with_args(self, command_name, args):
        self.send_packet_str(command_name+","+",".join(args))

    def send_read_keypad_led_status(self, keypad_address):
        if HwiTcpManager().logged_in:
            self.send_command_with_args("RKLS", [keypad_address])
        pass

    def send_read_dimmer_level(self, dimmer_address):
        if HwiTcpManager().logged_in:
            self.send_command_with_args("RDL", [dimmer_address])
        pass

    def send_shade_dim(self, shade_address, level):
        if level >= 0 and level <= 100:
            if HwiTcpManager().logged_in:
                self.send_command_with_args(
                    "RTDIM", [str(level), "0", shade_address])
        pass

    def send_fade_shade_dim(self, shade_address, level):
        if level >= 0 and level <= 100:
            if HwiTcpManager().logged_in:
                self.send_command_with_args(
                    "FADEDIM", [str(level), "0", "0", shade_address])
        pass

    def send_dim_light(self, dimmer_address, level):
        if level >= 0 and level <= 100:
            if HwiTcpManager().logged_in:
                self.send_command_with_args(
                    "FADEDIM", [str(level), "0", "0", dimmer_address])
        pass

    def send_set_shade_percent_open(self, shade_address, level):
        if level >= 0 and level <= 100:
            self.send_fade_shade_dim(shade_address, 100-level)
        pass

    def send_keypad_button_press(self, keypad_address, button_number):
        if HwiTcpManager().logged_in:
            self.send_command_with_args(
                "KBP", [keypad_address, str(button_number)])
    pass


class HwiPacketReceiver(PacketReceiver):
    _cmd_prompt = "LNET>"
    _login_prompt = "LOGIN:"
    _command_dimmer_level = "DL"
    _command_keypad_led_status = "KLS"
    _has_enabled_monitoring = False

    def __init__(self, hass):
        self._hass = hass

    def get_sender(self) -> HwiPacketSender:
        sender = HwiTcpManager().sender
        assert sender is not None
        return sender

    def is_known_command(self, string) -> bool:
        stripped = string.strip().split(",")
        return len(stripped) > 0 and stripped[0] in self._handlers

    def on_packet_received(self, string):
        if string == self._cmd_prompt:
            self.on_ready_for_command()
            pass
        elif string == self._login_prompt:
            self.on_ready_for_login()
            pass
        elif string == "login successful":
            self.on_logged_in()
            pass
        elif string == "login incorrect":
            self.on_login_incorrect()
            pass
        elif string.startswith("Timeclock"):
            self.on_timeclock_event(string)
            pass
        elif self.is_known_command(string):
            # Keypad LED status
            self.on_packet_with_args_received(string)
            pass
        else:
            _LOGGER.warning("unknown packet received: `" + string + "`")
            pass
        pass

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
        if self._has_enabled_monitoring == False:
            self._has_enabled_monitoring = True
            self.get_sender().send_monitor_packet()
        pass

    def on_ready_for_login(self):
        HwiTcpManager().login_state = "ready_for_login"
        _LOGGER.warning("ready to login")
        self.get_sender().send_login_packet()
        pass

    def on_logged_in(self):
        HwiTcpManager().login_state = "logged_in"
        pass

    def on_login_incorrect(self):
        # we dont need to resend login since the pipe will auto write LOGIN: prompt
        pass

    def on_timeclock_event(self, string: str):
        if string.startswith("Timeclock Sunset Event"):
            # Sunset event
            _LOGGER.warning("Captured timeclock sunset")
            self._hass.bus.fire("hwi_timeclock_event", {
                                "kind": "sunset", "raw_data": string})
        elif string.startswith("Timeclock Real Time Event"):
            _LOGGER.warning("Captured timeclock real time")
            self._hass.bus.fire("hwi_timeclock_event", {
                                "kind": "realtime", "raw_data": string})
        elif string.startswith("Timeclock Sunrise Event"):
            _LOGGER.warning("Captured timeclock sunrise")
            self._hass.bus.fire("hwi_timeclock_event", {
                                "kind": "sunrise", "raw_data": string})
        pass

    def on_keypad_led_status_update(self, args):
        _LOGGER.warning("got keypad LED status: " + str(args))
        # Notify any entity that is on this keypad of the change
        if len(args) >= 2:
            keypad_addr = args[0]
            led_states = args[1]
            keypad = HwiKeypadStore().get_keypad_at_address(
                HwiUtils.encode_keypad_address(keypad_addr))
            if keypad != None:
                keypad.led_states = led_states
            else:
                _LOGGER.warning("Keypad not found")
            pass

    def on_keypad_button_press(self, args):
        _LOGGER.warning("keypad button pressed " + str(args))
        # Notify any entity that is on this keypad of the change
        if len(args) >= 2:
            keypad_addr = args[0]
            button_num = int(args[1])
            keypad = HwiKeypadStore().get_keypad_at_address(
                HwiUtils.encode_keypad_address(keypad_addr))
            if keypad != None:
                self._hass.bus.fire("hwi_keypad_button_pressed", {
                                    "keypad_address": keypad.address, "button_number": button_num})
            else:
                _LOGGER.warning("Keypad not found")
            pass

    def on_keypad_button_release(self, args):
        _LOGGER.warning("keypad button released " + str(args))
        # Notify any entity that is on this keypad of the change
        if len(args) >= 2:
            keypad_addr = args[0]
            button_num = int(args[1])
            keypad = HwiKeypadStore().get_keypad_at_address(
                HwiUtils.encode_keypad_address(keypad_addr))
            if keypad != None:
                self._hass.bus.fire("hwi_keypad_button_released", {
                                    "keypad_address": keypad.address, "button_number": button_num})
            else:
                _LOGGER.warning("Keypad not found")
            pass

    def on_keypad_button_double_tap(self, args):
        # KBDT, [01:06:11], 23
        if len(args) >= 2:
            keypad_addr = args[0]
            button_num = int(args[1])
            keypad = HwiKeypadStore().get_keypad_at_address(
                HwiUtils.encode_keypad_address(keypad_addr))
            if keypad != None:
                self._hass.bus.fire("hwi_keypad_button_double_tapped", {
                                    "keypad_address": keypad.address, "button_number": button_num})
            else:
                _LOGGER.warning("Keypad not found")
            pass

    def on_keypad_button_hold(self, args):
        # KBH, [01:06:11], 2
        if len(args) >= 2:
            keypad_addr = args[0]
            button_num = int(args[1])
            keypad = HwiKeypadStore().get_keypad_at_address(
                HwiUtils.encode_keypad_address(keypad_addr))
            if keypad != None:
                self._hass.bus.fire("hwi_keypad_button_hold", {
                                    "keypad_address": keypad.address, "button_number": button_num})
            else:
                _LOGGER.warning("Keypad not found")
            pass

    def on_dimmer_level_update(self, args):
        _LOGGER.warning("dimmer level update: " + str(args))
        keypad_address = args[0]
        level = float(args[1])
        shade = HwiKeypadStore().get_shade_at_address(
            HwiUtils.encode_shade_address(keypad_address))

        if shade != None:
            shade.on_dimmer_level_update(level)
        else:
            zone = HwiKeypadStore().get_zone_at_address(
                HwiUtils.encode_zone_address(keypad_address))
            if zone != None:
                self._hass.bus.fire("hwi_zone_dimmer_level_updated", {
                                    "zone_address": keypad_address, "dimmer_level": level})
                # zone.on_brightness_changed(level)

        #  got keypad LED status: ['[01:06:14]', '100000000000000000000000']
        # StepLight is on
        # [Keypad name: Stairs 2, address: [1:6:14], encoded_address: keypad_1_6_14, buttons:
        # 	[Button name: StepLight, number: 1, is_on: True]
        # 	[Button name: Pendent, number: 2, is_on: False]
        # 	[Button name: To Kitchen, number: 3, is_on: False]
        #  ]
        # unknown packet received: KBR, [01:06:14],  1
        # unknown packet received: KBP, [01:06:14],  1
        # dimmer level update: ['[01:01:00:06:04]', '0']
        # unknown packet received: KBR, [01:06:14],  1
        pass

    _handlers = {
        "KLS": on_keypad_led_status_update,
        "DL": on_dimmer_level_update,
        "KBP": on_keypad_button_press,
        "KBR": on_keypad_button_release,
        "KBDT": on_keypad_button_double_tap,
        "KBH": on_keypad_button_hold
    }

    pass

