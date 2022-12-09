from typing import Protocol, TYPE_CHECKING

from .hub import HubCommand


class CommandQueue(Protocol):
    
    def enqueue_command(self, command: HubCommand):
        pass