import asyncio
import logging
from typing import Callable, Optional

from .packets import PacketBuffer

_LOGGER = logging.getLogger(__name__)


class LutronClientProtocol(asyncio.Protocol):
    def __init__(
        self,
        on_data_received: Callable[[bytes], None],
        on_connection_lost: asyncio.Future,
    ) -> None:
        self._buffer = PacketBuffer()
        self._on_data_received = on_data_received
        self.on_connection_lost = on_connection_lost

    def connection_made(self, transport: asyncio.Transport) -> None:
        self._transport = transport

    def data_received(self, packet: bytes) -> None:
        self._buffer.append(packet)
        _LOGGER.debug(f"packet `{packet}`")
        _LOGGER.debug(f"buffer: `{self._buffer.data}")
        _LOGGER.debug(f"is_complete: `{self._buffer.is_complete}`")
        if self._buffer.is_complete:
            complete_data = self._buffer.data
            self._buffer.clear()
            lines = self._split_lines(complete_data)
            for line in lines:
                self._on_data_received(line)

    def _split_lines(self, data: bytes) -> list[bytes]:
        lines = data.split(b"\r\n")
        lines = [line.strip() for line in lines]
        lines = [line for line in lines if line != b"\r\n" and line != b""]
        return lines

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self.on_connection_lost.set_result(True)
