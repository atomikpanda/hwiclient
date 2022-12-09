from __future__ import annotations
import asyncio
from typing import Any, Optional, Protocol, Tuple
from abc import abstractmethod
import logging
from .message import RequestMessage, RequestMessageKind, ResponseMessage, ResponseMessageKind, ResponseQueue, Transport
from .session import LutronSession
from .listener import ConnectionState
from .tcp import TcpConnection
from .login import LutronCredentials, LutronServerAddress

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
log_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s [%(threadName)s] "
)  # I am printing thread id here
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
_LOGGER.addHandler(console_handler)


class TcpClient(Protocol):
    @abstractmethod
    async def open_connection(self, server_address: LutronServerAddress) -> TcpConnection:
        pass

    async def attempt_login(self, connection: TcpConnection, credentials: LutronCredentials, transport: Transport) -> Optional[LutronSession]:
        pass


class AsyncioTcpClient(TcpClient):
    _LOGIN_SUCCESSFUL = "login successful"
    _LOGIN_INCORRECT = "login incorrect"
    _LOGIN_PROMPT = "LOGIN:"
    _ENCODING = "ascii"

    def __init__(self):
        self._disconnect = False

    async def open_connection(self, server_address: LutronServerAddress) -> TcpConnection:
        self._disconnect = False
        return TcpConnection(await asyncio.open_connection(host=server_address.host, port=server_address.port), self._ENCODING)

    async def attempt_login(self, connection: TcpConnection, credentials: LutronCredentials, transport: Transport) -> Optional[LutronSession]:

        prompt = await connection.reader.read_login_prompt()
        if prompt == self._LOGIN_PROMPT:
            self._respond_state_update(
            ConnectionState.CONNECTED_READY_FOR_LOGIN_ATTEMPT, transport.response_queue)
            await connection.writer.write_login(credentials.username, credentials.password)
            response = await connection.reader.read_login_response()
            return self._handle_login_response(response, transport, connection, credentials)
        else:
            return None

    def _respond_state_update(self, new_state: ConnectionState, queue: ResponseQueue):
        queue.put(ResponseMessage(ResponseMessageKind.STATE_UPDATE, new_state))

    def _respond_with_data(self, data: Any, queue: ResponseQueue):
        queue.put(ResponseMessage(
            ResponseMessageKind.SERVER_RESPONSE_DATA, data))
        

        
    def _handle_login_response(self, response: str, transport: Transport, connection: TcpConnection, credentials: LutronCredentials) -> Optional[LutronSession]:

        if response == self._LOGIN_SUCCESSFUL:
            self._respond_state_update(
                ConnectionState.CONNECTED_LOGGED_IN, transport.response_queue)
            return LutronSession(connection, credentials)
        elif response == self._LOGIN_INCORRECT:
            return None
        else:
            return None


