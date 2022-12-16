import asyncio
from dataclasses import dataclass
from enum import Enum
from asyncio import AbstractEventLoop, PriorityQueue, Queue
from typing import Any, Protocol, Tuple, TypeAlias
from .state import ConnectionState
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


class RequestEnqueuer(Protocol):
    async def enqueue(self, message: RequestMessage):
        pass


class _RequestMessageQueue(PriorityQueue[RequestMessage]):
    pass

class ReponseMessageFactory:
    def create_state_update(self, state: ConnectionState) -> ResponseMessage:
        return ResponseMessage(ResponseMessageKind.STATE_UPDATE, state)
    
    def create_response_data(self, data: Any) -> ResponseMessage:
        return ResponseMessage(ResponseMessageKind.SERVER_RESPONSE_DATA, data)