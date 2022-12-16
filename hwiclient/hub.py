from __future__ import annotations
from abc import abstractmethod

from typing import Any, TYPE_CHECKING, Protocol


if TYPE_CHECKING:
    from .repos import DeviceRepository
    from .connection.state import ConnectionState
    from .connection.login import LutronServerAddress
    from .connection.tcp import TcpConnection
    
from .monitoring import TopicNotifier
from .commands.sender import CommandSender
from .commands.queue import CommandQueue

class Hub(TopicNotifier, CommandSender, CommandQueue, Protocol):
    def __init__(self, homeworks_config: dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def connect(self, server: LutronServerAddress) -> TcpConnection:
        pass

    devices: DeviceRepository
    connection_state: ConnectionState

    async def disconnect(self):
        pass
