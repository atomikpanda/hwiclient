

from typing import Callable

from .listener import ConnectionState
from .message import ResponseMessage, ResponseMessageKind, ResponseQueue


class ResponseWatcher:
    def __init__(self, on_received_response: Callable[[ResponseMessage], bool]) -> None:
        self._on_received_response_callback = on_received_response

    async def watch(self, queue: ResponseQueue):
        keep_watching = True
        while keep_watching:
            response = queue.get()
            keep_watching = self._on_received_response(response)

    def _on_received_response(self, response: ResponseMessage) -> bool:
        if response.kind == ResponseMessageKind.STATE_UPDATE and response.data == ConnectionState.DISCONNECTING:
            self._on_received_response_callback(response)
            return False
        else:
            return self._on_received_response_callback(response)
