from abc import abstractmethod
from typing import Protocol

from .hub import HubCommand


class CommandQueue(Protocol):
    @abstractmethod
    async def enqueue_command(self, command: HubCommand) -> None:
        pass
