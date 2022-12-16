from typing import Tuple
from .state import ConnectionState
import asyncio
from typing import Callable, Optional
from .login import LutronConnectionConfig, LutronServerAddress
from .message import _RequestMessageQueue, RequestEnqueuer, RequestMessageKind, ResponseMessage, RequestMessage, ResponseMessageKind
from .adapter import DataToResponseAdapter
from .tcp import TcpConnection
import logging
_LOGGER = logging.getLogger(__name__)


class ConnectionCoordinator(RequestEnqueuer):
    _ENCODING = 'ascii'

    def __init__(self, on_received_response: Callable[[ResponseMessage], bool]) -> None:
        self._queue = _RequestMessageQueue()
        self._on_received_response_callback = on_received_response
        self._data_to_response_adapter = DataToResponseAdapter(self._ENCODING)

    async def _put_priory_requests_in_queue(self):
        mon_cmds = ["DLMON", "KBMON", "KLMON", "GSMON", "TEMON"]
        msgs = [RequestMessage(RequestMessageKind.SEND_DATA, cmd, 1)
                for cmd in mon_cmds]
        for msg in msgs:
            await self.enqueue(msg)
            
    @property
    def connection_state(self) -> ConnectionState:
        if self._connection != None:
            return self._connection.connection_state
        return ConnectionState.NOT_CONNECTED

    async def connect(self, server: LutronServerAddress) -> TcpConnection:
        self._connection = TcpConnection(server, self._on_data_received, self._ENCODING)
        await self._connection.open()
        await self._put_priory_requests_in_queue()
        self._connection.on_next_state_change.add_done_callback(
            self._on_next_state)
        return self._connection

    def _on_next_state(self, future: asyncio.Future[Tuple[ConnectionState, ConnectionState]]) -> None:
        _LOGGER.debug(f"ON NEXT STATE {future.result}")
        pass

    def _write_next_pending_request(self):
        try:
            request = self._queue.get_nowait()
            self._connection.write_request(request)
        except asyncio.QueueEmpty:
            pass

    def _on_data_received(self, data: bytes) -> None:
        response = self._data_to_response_adapter.adapt(data)
        _LOGGER.debug(response)

        if response.kind == ResponseMessageKind.STATE_UPDATE:
            self._connection.on_state_update(response.data)
            
        if response.kind == ResponseMessageKind.STATE_UPDATE and response.data == ConnectionState.CONNECTED_READY_FOR_COMMAND:
            self._write_next_pending_request()

        if response.kind == ResponseMessageKind.STATE_UPDATE and response.data == ConnectionState.DISCONNECTING:
            self._on_received_response_callback(response)
            # DISCONNECT
        else:
            self._on_received_response_callback(response)
            
    async def enqueue(self, message: RequestMessage):
        await self._queue.put(message)
        if self._connection._state == ConnectionState.CONNECTED_READY_FOR_COMMAND:
            self._write_next_pending_request()
    

