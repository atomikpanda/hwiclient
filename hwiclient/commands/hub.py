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
    def _perform_command(self, sender: CommandSender):
        pass

    def execute(self, sender: CommandSender):
        if self._can_perform_command(sender):
            self._perform_command(sender)

    def enqueue(self, queue: CommandQueue):
        queue.enqueue_command(self)


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

    def _perform_command(self, sender: CommandSender):
        for cmd in self._commands:
            cmd.execute(sender)


