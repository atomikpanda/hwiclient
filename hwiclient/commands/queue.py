from typing import Protocol, TYPE_CHECKING

from .hub import HubCommand


class CommandQueue(Protocol):
    
    async def enqueue_command(self, command: HubCommand):
        pass