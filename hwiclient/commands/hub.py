from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .queue import CommandQueue

from .sender import CommandSender

class HubCommand(ABC):

    def __init__(self):
        pass

    def _can_perform_command(self, sender: CommandSender) -> bool:
        return True

    @abstractmethod
    async def _perform_command(self, sender: CommandSender):
        pass

    async def execute(self, sender: CommandSender):
        if self._can_perform_command(sender):
            await self._perform_command(sender)

    async def enqueue(self, queue: CommandQueue):
        await queue.enqueue_command(self)


class HubActionCommand(HubCommand, ABC):
    pass


class HubRequestCommand(HubCommand, ABC):
    pass


class SessionActionCommand(HubActionCommand, ABC):
    def _can_perform_command(self, sender: CommandSender) -> bool:
        return super()._can_perform_command(sender) and sender.ready_for_command


class SessionRequestCommand(HubRequestCommand, ABC):
    def _can_perform_command(self, sender: CommandSender) -> bool:
        return super()._can_perform_command(sender) and sender.ready_for_command


class Sequence(HubCommand):
    def __init__(self, commands: list[HubCommand]):
        super().__init__()
        self._commands = commands

    async def _perform_command(self, sender: CommandSender):
        for cmd in self._commands:
            await cmd.execute(sender)


