from typing import Callable, Optional, Tuple, cast
import asyncio
from .protocol import LutronClientProtocol
from .login import LutronCredentials, LutronServerAddress
from .state import ConnectionState
from .message import RequestMessage, RequestMessageKind
import logging

_LOGGER = logging.getLogger(__name__)

class TcpConnection:
    def __init__(self, server: LutronServerAddress, on_data_received: Callable[[bytes], None], encoding: str):
        self._on_data_received_callback = on_data_received
        self._server = server
        self._encoding = encoding
        self._loop = asyncio.get_running_loop()
        self._on_connection_lost = self._loop.create_future()
        self._on_next_state_change = self._loop.create_future()
        self._on_logged_in = self._loop.create_future()
        self._transport: Optional[asyncio.Transport] = None
        self._state = ConnectionState.NOT_CONNECTED
        
    @property
    def connection_state(self) -> ConnectionState:
        return self._state

    async def open(self):
        transport, protocol = await self._loop.create_connection(lambda: LutronClientProtocol(self._on_data_received, self._on_connection_lost), host=self._server.host, port=self._server.port)
        self._transport = cast(asyncio.Transport, transport)
        self._protocol = protocol

    async def attempt_login(self, credentials: LutronCredentials) -> asyncio.Future:
        if self._protocol == None or self._transport == None or self._state != ConnectionState.CONNECTED_READY_FOR_LOGIN_ATTEMPT:
            raise ConnectionError(
                "Cannot attempt login when connection is not connected or ready for login")

        self.write_str('%s,%s' % (credentials.username, credentials.password))
        return self._on_logged_in

    def _on_data_received(self, data: bytes):
        self._on_data_received_callback(data)

    def write_str(self, data: str):
        if self._transport == None:
            raise ConnectionError("Cannot write when transport is None")
        _LOGGER.debug("WRITE: %s" % data)
        self._transport.write(f"{data}\r\n".encode(self._encoding))

    def write_request(self, request: RequestMessage):
        if request.kind == RequestMessageKind.SEND_DATA:
            self.write_str(request.data)
        elif request.kind == RequestMessageKind.SEND_COMMAND:
            self.write_str(request.data)

    @property
    def on_connection_lost(self) -> asyncio.Future:
        return self._on_connection_lost

    @property
    def on_next_state_change(self) -> asyncio.Future[Tuple[ConnectionState, ConnectionState]]:
        return self._on_next_state_change

    @property
    def on_logged_in(self) -> asyncio.Future:
        return self._on_logged_in

    def on_state_update(self, new_state: ConnectionState):
        old_state = self._state
        self._state = new_state
        self.on_next_state_change.set_result((old_state, new_state))
        self._on_next_state_change = self._loop.create_future()
        if old_state == ConnectionState.CONNECTED_READY_FOR_LOGIN_ATTEMPT and new_state == ConnectionState.CONNECTED_LOGGED_IN:
            self._on_logged_in.set_result(True)

    def close(self):
        if self._transport != None:
            self._transport.close()
            self._transport = None
