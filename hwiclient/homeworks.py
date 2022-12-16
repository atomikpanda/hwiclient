
import asyncio
from .hub import Hub
from typing import Any, TYPE_CHECKING, Callable, Iterable, Optional, Type
from .repos import DeviceRepository
from .connection.state import ConnectionState
from .connection.message import RequestMessage, RequestMessageKind, ResponseMessage, ResponseMessageKind
from .connection.login import LutronServerAddress
from .connection.tcp import TcpConnection
from .connection.coordinator import ConnectionCoordinator
from .commands.hub import HubCommand
from .monitoring import MonitoringTopicKey, MonitoringTopicNotifier, TopicSubscriber, MonitoringTopic
from .responsehandler import ServerResponseDataHandler


class HomeworksHub(Hub):
    def __init__(self, homeworks_config: dict[str, Any]) -> None:
        self._homeworks_config = homeworks_config
        self._monitoring_topic_notifier = MonitoringTopicNotifier()
        self._devices = DeviceRepository(homeworks_config, self)
        self._coordinator = ConnectionCoordinator(self._handle_response)
        self._response_data_handler = ServerResponseDataHandler(
            self._monitoring_topic_notifier)


    def _handle_response(self, response: ResponseMessage) -> bool:
        if response.kind == ResponseMessageKind.STATE_UPDATE:
            return True
        elif response.kind == ResponseMessageKind.SERVER_RESPONSE_DATA:
            self._response_data_handler.handle(response.data)
            return True
        else:
            raise NotImplementedError(response.kind)

    @property
    def devices(self) -> DeviceRepository:
        return self._devices

    @property
    def connection_state(self) -> ConnectionState:
        return self._coordinator.connection_state

    @property
    def ready_for_command(self) -> bool:
        return self.connection_state == ConnectionState.CONNECTED_READY_FOR_COMMAND

    async def send_raw_command(self, name: str, *args: str):
        if len(args) > 0:
            data = name+","+",".join(args)
        else:
            data = name
        await self._coordinator.enqueue(RequestMessage(
            RequestMessageKind.SEND_COMMAND, data))

    async def connect(self, server: LutronServerAddress) -> TcpConnection:
        return await self._coordinator.connect(server)

    async def disconnect(self):
        await self._coordinator.enqueue(RequestMessage(
            RequestMessageKind.DISCONNECT, None))

    async def enqueue_command(self, command: HubCommand):
        # TODO: actually use a queue
        return asyncio.create_task(command._perform_command(self))

    def subscribe(self, subscriber: TopicSubscriber, *topics: MonitoringTopic):
        self._monitoring_topic_notifier.subscribe(subscriber, *topics)

    def unsubscribe(self, subscriber: TopicSubscriber, *topics: MonitoringTopic):
        self._monitoring_topic_notifier.unsubscribe(subscriber, *topics)

    def notify_subscribers(self, topic: MonitoringTopic, data: dict[MonitoringTopicKey, Any]):
        self._monitoring_topic_notifier.notify_subscribers(topic, data)
