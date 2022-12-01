from datetime import timedelta
from .hub import HubActionCommand
from typing import TYPE_CHECKING
from ..models import Time

from ..hub import Hub
if TYPE_CHECKING:
    from ..device import DeviceAddress

class LoginCommand(HubActionCommand):
    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password
    
    def _perform_command(self, hub: Hub):
        hub.connection.send_packet(f"{self._username},{self._password}")
        