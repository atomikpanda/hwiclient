# from datetime import timedelta

# from .sender import CommandSender
# from .hub import HubActionCommand
# from typing import TYPE_CHECKING
# from ..models import Time

# if TYPE_CHECKING:
#     from ..device import DeviceAddress

# class LoginCommand(HubActionCommand):
#     def __init__(self, username: str, password: str):
#         self._username = username
#         self._password = password
    
#     def _perform_command(self, sender: CommandSender):
#         sender.connection.send_packet(f"{self._username},{self._password}")
        