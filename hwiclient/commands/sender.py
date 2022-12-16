from typing import Protocol


class CommandSender(Protocol):
    ready_for_command: bool

    async def send_raw_command(self, name: str, *args: str):
        pass
