from typing import Protocol

from .hub import HubCommand


class CommandQueue(Protocol):
    async def enqueue_command(self, command: HubCommand):
        pass
