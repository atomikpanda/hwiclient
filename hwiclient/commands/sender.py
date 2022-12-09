from typing import Protocol


class CommandSender(Protocol):
    ready_for_command: bool

    def send_command(self, name: str, *args: str):
        pass
