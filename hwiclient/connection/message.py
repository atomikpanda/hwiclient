from dataclasses import dataclass
from enum import Enum
from queue import PriorityQueue, Queue
from typing import Any, Protocol, Tuple, TypeAlias
from .listener import ConnectionState
from abc import abstractmethod

class ResponseMessageKind(Enum):
    SERVER_RESPONSE_DATA = 1
    STATE_UPDATE = 2


@dataclass
class ResponseMessage:
    kind: ResponseMessageKind
    data: Any


class RequestMessageKind(Enum):
    SEND_DATA = 1
    DISCONNECT = 2
    SEND_COMMAND = 3


@dataclass
class RequestMessage:
    kind: RequestMessageKind
    data: Any
    priority: int = 20
    
    def __lt__(self, other: 'RequestMessage') -> int:
        return self.priority < other.priority
        


class MessageSender(Protocol):
    def send_request(self, message: RequestMessage):
        pass
    
    def send_response(self, message: ResponseMessage):
        pass
    

class MessageGetter(Protocol):
    
    @abstractmethod
    def get_request(self) -> RequestMessage:
        pass
    
    @abstractmethod
    def get_response(self) -> ResponseMessage:
        pass

class ResponseQueue(Queue[ResponseMessage]):
    def put_response_data(self, data: Any):
        self.put(ResponseMessage(ResponseMessageKind.SERVER_RESPONSE_DATA, data))

    def put_state_update(self, state: ConnectionState):
        self.put(ResponseMessage(ResponseMessageKind.STATE_UPDATE, state))


class RequestQueue(PriorityQueue[RequestMessage]):
    def put_request_data(self, data: Any):
        self.put(RequestMessage(RequestMessageKind.SEND_DATA, data))


class Transport(MessageSender, MessageGetter):
    def __init__(self):
        self._response_queue = ResponseQueue()
        self._request_queue = RequestQueue()

    @property
    def response_queue(self) -> ResponseQueue:
        return self._response_queue

    @property
    def request_queue(self) -> RequestQueue:
        return self._request_queue
    
    def send_request(self, message: RequestMessage):
        self._request_queue.put(message)
    
    def send_response(self, message: ResponseMessage):
        self._response_queue.put(message)
        
    def get_request(self) -> RequestMessage:
        return self._request_queue.get(False)
    
    def get_response(self) -> ResponseMessage:
        return self._response_queue.get()
