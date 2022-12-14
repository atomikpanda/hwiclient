import sys
import asyncio
from threading import Thread
from typing import Any, Callable, Iterable, Mapping

from .tcpclient import TcpClient
from .login import LutronConnectionConfig
from .message import RequestMessage, RequestMessageKind, ResponseQueue, Transport
from .listener import ConnectionState
from .watcher import ResponseWatcher
import logging
_LOGGER = logging.getLogger(__name__)


class ResponseWatcherThread(Thread):
    def __init__(
        self,
        queue: ResponseQueue,
        watcher: ResponseWatcher
    ) -> None:
        super().__init__(None, None, None, (), {}, daemon=None)
        self._queue = queue
        self._response_watcher = watcher

    def run(self) -> None:
        asyncio.run(self._response_watcher.watch(self._queue))
        print("done watching queue for response")


class TcpClientThread(Thread):
    def __init__(
        self,
        client: TcpClient,
        login: LutronConnectionConfig,
        transport: Transport
    ) -> None:
        super().__init__(None, None, None, (), {}, daemon=False)
        self._client = client
        self._login = login
        self._transport = transport
        self._disconnect = False

    def run(self) -> None:
        self._disconnect = False
        asyncio.run(self._start_tcp_client(self._client, self._login))

    async def _start_tcp_client(self, client: TcpClient, login: LutronConnectionConfig):
        retries = 0
        while retries <= 5 and self._disconnect == False:
            try:
                await self._connect_and_login(client, login)
            except asyncio.exceptions.IncompleteReadError as ex:
                _LOGGER.debug("Lost connection")
                _LOGGER.debug("Retry connection")
                retries += 1

    def _put_priory_requests_in_transport(self):
        self._transport.send_request(RequestMessage(
            RequestMessageKind.SEND_DATA, "DLMON", 1))
        self._transport.send_request(RequestMessage(
            RequestMessageKind.SEND_DATA, "KBMON", 1))
        self._transport.send_request(RequestMessage(
            RequestMessageKind.SEND_DATA, "KLMON", 1))
        self._transport.send_request(RequestMessage(
            RequestMessageKind.SEND_DATA, "GSMON", 1))
        self._transport.send_request(RequestMessage(
            RequestMessageKind.SEND_DATA, "TEMON", 1))

    async def _connect_and_login(self, client: TcpClient, login: LutronConnectionConfig):
        connection = await client.open_connection(login.server_address)
        self._transport.response_queue.put_state_update(
            ConnectionState.CONNECTED_NOT_LOGGED_IN)
        session = await client.attempt_login(
            connection,
            login.credentials,
            self._transport
        )
        if session == None:
            _LOGGER.error("Login failed")
        else:
            self._put_priory_requests_in_transport()
            await session.send_and_receive_on_transport(self._transport)
            if session.disconnect_flag:
                self._disconnect = True
                sys.exit()
