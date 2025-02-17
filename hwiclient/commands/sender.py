from abc import abstractmethod
from typing import Protocol


class CommandSender(Protocol):
    @property
    @abstractmethod
    def ready_for_command(self) -> bool:
        pass

    async def send_raw_command(self, name: str, *args: str):
        pass
