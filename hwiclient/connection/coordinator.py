from typing import Callable
from .watcher import ResponseWatcher
from .login import LutronConnectionConfig
from .thread import ResponseWatcherThread, TcpClientThread
from .tcpclient import TcpClient
from .message import MessageSender, RequestMessageKind, ResponseMessage, RequestMessage, Transport


class ConnectionCoordinator(MessageSender):
    def __init__(self, tcp_client: TcpClient, on_received_response: Callable[[ResponseMessage], bool]) -> None:
        self._client = tcp_client
        self._transport = Transport()
        self._response_watcher = ResponseWatcher(on_received_response)

    def connect_and_attempt_login(self, config: LutronConnectionConfig):
        self._start_threads(config)


    def _start_threads(self, config: LutronConnectionConfig):
        self._response_watcher_thread = ResponseWatcherThread(
            group=None,
            kwargs={
                "response_watcher": self._response_watcher,
                "queue": self._transport.response_queue,
            },
        )
        self._tcp_client_thread = TcpClientThread(
            self._client, config, self._transport)
        self._response_watcher_thread.start()
        self._tcp_client_thread.start()

    def send_request(self, message: RequestMessage):
        self._transport.send_request(message)

    def _send_response(self, message: ResponseMessage):
        self._transport.response_queue.put(message)
