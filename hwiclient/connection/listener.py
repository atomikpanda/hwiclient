from enum import Enum
from typing import Protocol


class ConnectionState(Enum):
    NOT_CONNECTED = 1
    CONNECTED_NOT_LOGGED_IN = 2
    CONNECTED_READY_FOR_LOGIN_ATTEMPT = 3
    CONNECTED_LOGIN_INCORRECT = 4
    CONNECTED_LOGGED_IN = 5
    CONNECTED_READY_FOR_COMMAND = 6
    DISCONNECTING = 7


class ConnectionStateListener(Protocol):
    def on_connection_state_changed(self, old_state: ConnectionState, new_state: ConnectionState):
        pass
