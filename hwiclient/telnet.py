from __future__ import annotations
from twisted.internet import defer, reactor
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.protocol import ClientFactory
from twisted.conch.telnet import TelnetTransport, StatefulTelnetProtocol
from twisted.python import log
import logging
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .connection import TcpConnectionManager
    
_LOGGER = logging.getLogger(__name__)
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
                    self.factory.manager.receiver.on_packet_received, line.strip())

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
    def __init__(self, manager: TcpConnectionManager):
        self.transport = None
        self.manager = manager

    def buildProtocol(self, addr):
        self.transport = TelnetTransport(TelnetClient)
        self.transport.factory = self
        return self.transport

    def clientConnectionLost(self, connector, reason):
        _LOGGER.warning('Lost telnet connection.  Reason: %s ' % reason)

    def clientConnectionFailed(self, connector, reason):
        _LOGGER.warning('Telnet connection failed. Reason:%s ' % reason)


class TelnetClientCommand:
    def __init__(self, prompt, command, manager: TcpConnectionManager):
        self._manager = manager
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
        telnetFactory = TelnetFactory(manager=self._manager)
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
        assert self.transport is not None
        self.transport.send_command(self.command)

    def send_packet_str(self, string, include_return=True):
        assert self.transport is not None
        self.transport.send_packet_str(string, include_return)
        pass

    def received_response(self, response):
        _LOGGER.warning("received response: " + response)
        # HwiTcpManager().receiver.on_packet_received(response)
