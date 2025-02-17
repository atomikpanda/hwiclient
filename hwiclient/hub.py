from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from .connection.login import LutronServerAddress
    from .connection.state import ConnectionState
    from .connection.tcp import TcpConnection
    from .repos import DeviceRepository

from .commands.queue import CommandQueue
from .commands.sender import CommandSender
from .monitoring import TopicNotifier


class Hub(TopicNotifier, CommandSender, CommandQueue, Protocol):
    def __init__(self, homeworks_config: dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def connect(self, server: LutronServerAddress) -> TcpConnection:
        pass

    @property
    @abstractmethod
    def devices(self) -> DeviceRepository:
        pass

    @property
    @abstractmethod
    def connection_state(self) -> ConnectionState:
        pass

    async def disconnect(self):
        pass
