from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import TYPE_CHECKING

from ..hub import Hub


class HubCommand(ABC):

    def __init__(self):
        pass

    def _can_perform_command(self, hub: Hub) -> bool:
        return True

    @abstractmethod
    def _perform_command(self, hub: Hub):
        pass

    def execute(self, hub: Hub):
        if self._can_perform_command(hub):
            self._perform_command(hub)

    def enqueue(self, hub: Hub):
        hub.enqueue_command(self)


class HubActionCommand(HubCommand, ABC):
    pass


class HubRequestCommand(HubCommand, ABC):
    pass


class SessionActionCommand(HubActionCommand, ABC):
    def _can_perform_command(self, hub: Hub) -> bool:
        return super()._can_perform_command(hub) and hub.connection.ready


class SessionRequestCommand(HubRequestCommand, ABC):
    def _can_perform_command(self, hub: Hub) -> bool:
        return super()._can_perform_command(hub) and hub.connection.ready


class Sequence(HubCommand):
    def __init__(self, commands: list[HubCommand]):
        super().__init__()
        self._commands = commands

    def _perform_command(self, hub: Hub):
        for cmd in self._commands:
            cmd.execute(hub)


