from __future__ import annotations

from typing import Optional, Any, TYPE_CHECKING, Protocol, Type

if TYPE_CHECKING:
    from .commands.hub import HubCommand
    from .bus import EventBus
    from .repos import DeviceRepository
    from .connection.listener import ConnectionStateListener, ConnectionState
    from .connection.login import LutronConnectionConfig
    from .monitoring import TopicSubscriber, MonitoringTopic
    
from .monitoring import TopicNotifier
from .commands.sender import CommandSender
from .commands.queue import CommandQueue

class Hub(TopicNotifier, CommandSender, CommandQueue, Protocol):
    def __init__(self, bus: EventBus, homeworks_config: dict[str, Any]) -> None:
        pass

    def connect_and_attempt_login(self, config: LutronConnectionConfig, listener: ConnectionStateListener) -> None:
        pass

    devices: DeviceRepository
    connection_state: ConnectionState

    def disconnect(self):
        pass
