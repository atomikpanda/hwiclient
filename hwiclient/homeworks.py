
from .hub import Hub
from .bus import EventBus
from typing import Any, TYPE_CHECKING, Callable, Iterable, Optional, Type
from .repos import DeviceRepository
from .connection.listener import ConnectionState, ConnectionStateListener
from .connection.message import RequestMessage, RequestMessageKind, ResponseMessage, ResponseMessageKind
from .connection.tcpclient import AsyncioTcpClient
from .connection.login import LutronConnectionConfig
from .connection.tcp import TcpConnection
from .connection.coordinator import ConnectionCoordinator
from .commands.hub import HubCommand
from .monitoring import MonitoringTopicKey, MonitoringTopicNotifier, TopicSubscriber, MonitoringTopic
from .responsehandler import ServerResponseDataHandler


class HomeworksHub(Hub):
    def __init__(self, bus: EventBus, homeworks_config: dict[str, Any], join_client_thread: bool = False,) -> None:
        self._bus = bus

        self._homeworks_config = homeworks_config
        self._monitoring_topic_notifier = MonitoringTopicNotifier()
        self._devices = DeviceRepository(homeworks_config, self)
        self._client = AsyncioTcpClient()
        self._coordinator = ConnectionCoordinator(
            self._client, join_client_thread,  self._handle_response)
        self._connection_state = ConnectionState.NOT_CONNECTED
        self._response_data_handler = ServerResponseDataHandler(
            self._monitoring_topic_notifier)

    def _notify_state_update(self, state: ConnectionState):
        if self._connection_state_listener != None:
            old_state = self._connection_state
            self._connection_state = state
            self._connection_state_listener.on_connection_state_changed(
                old_state=old_state, new_state=state)

    def _handle_response(self, response: ResponseMessage) -> bool:
        if response.kind == ResponseMessageKind.STATE_UPDATE:
            self._notify_state_update(response.data)
            return True
        elif response.kind == ResponseMessageKind.SERVER_RESPONSE_DATA:
            self._response_data_handler.handle(response.data)
            return True
        else:
            raise NotImplementedError

    @property
    def devices(self) -> DeviceRepository:
        return self._devices

    @property
    def connection_state(self) -> ConnectionState:
        return self._connection_state

    @property
    def ready_for_command(self) -> bool:
        return self._connection_state == ConnectionState.CONNECTED_READY_FOR_COMMAND

    def send_raw_command(self, name: str, *args: str):
        if len(args) > 0:
            data = name+","+",".join(args)
        else:
            data = name
        self._coordinator.send_request(RequestMessage(
            RequestMessageKind.SEND_COMMAND, data))

    def connect_and_attempt_login(self, config: LutronConnectionConfig, listener: ConnectionStateListener):
        self._connection_config = config
        self._connection_state_listener = listener
        self._coordinator.connect_and_attempt_login(config)

    def disconnect(self):
        self._coordinator.send_request(RequestMessage(
            RequestMessageKind.DISCONNECT, None))

    def enqueue_command(self, command: HubCommand):
        # TODO: actually use a queue
        command._perform_command(self)

    def subscribe(self, subscriber: TopicSubscriber, *topics: MonitoringTopic):
        self._monitoring_topic_notifier.subscribe(subscriber, *topics)

    def unsubscribe(self, subscriber: TopicSubscriber, *topics: MonitoringTopic):
        self._monitoring_topic_notifier.unsubscribe(subscriber, *topics)

    def notify_subscribers(self, topic: MonitoringTopic, data: dict[MonitoringTopicKey, Any]):
        self._monitoring_topic_notifier.notify_subscribers(topic, data)
