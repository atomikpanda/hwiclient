
from .hub import Hub
from .bus import EventBus
from typing import Any, TYPE_CHECKING
from .repos import DeviceRepository
from .connection import TcpConnectionManager, ConnectionStateListener

from .commands.hub import HubCommand


class HomeworksHub(Hub):
    def __init__(self, bus: EventBus, homeworks_config: dict[str, Any]) -> None:
        self._bus = bus

        self._homeworks_config = homeworks_config
        self._devices = DeviceRepository(homeworks_config)
        self._connection = TcpConnectionManager(hub=self, bus=self._bus)

    @property
    def devices(self) -> DeviceRepository:
        return self._devices

    @property
    def connection(self) -> TcpConnectionManager:
        return self._connection

    def connect_and_attempt_login(self, host: str, port: int, username: str, password: str, listener: ConnectionStateListener):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._connection.connect_and_attempt_login(
            host=host, port=port, username=username,
            password=password, listener=listener)

    def enqueue_command(self, command: HubCommand):
        # TODO: actually use a queue
        command._perform_command(self)

