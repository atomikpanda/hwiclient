from __future__ import annotations

from typing import Optional, Any, TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .commands.hub import HubCommand
    from .bus import EventBus
    from .repos import DeviceRepository
    from .connection import TcpConnectionManager, ConnectionStateListener


class Hub(Protocol):
    def __init__(self, bus: EventBus, homeworks_config: dict[str, Any]) -> None:
        pass

    def attempt_login(self, host: str, port: int, username: str, password: str, listener: ConnectionStateListener) -> None:
        pass
    
    devices: DeviceRepository
    connection: TcpConnectionManager
    
    def enqueue_command(self, command: HubCommand):
        pass
    


