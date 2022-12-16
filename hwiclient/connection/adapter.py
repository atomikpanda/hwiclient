from .message import ReponseMessageFactory, ResponseMessage, ResponseMessageKind
from .state import ConnectionState
import logging
_LOGGER = logging.getLogger(__name__)


class DataToResponseAdapter:
    _LOGIN_PROMPT = 'LOGIN:'
    _LNET_PROMPT = 'LNET>'
    _LOGIN_SUCCESSFUL = 'login successful'
    _LOGIN_INCORRECT = 'login incorrect'

    def __init__(self, encoding: str):
        self._encoding = encoding
        self._message_factory = ReponseMessageFactory()

    def adapt(self, data: bytes) -> ResponseMessage:
        message = data.decode(self._encoding)
        stripped = message.strip()
        print('RES> %s' % stripped)
        if stripped == self._LOGIN_PROMPT:
            return self._message_factory.create_state_update(ConnectionState.CONNECTED_READY_FOR_LOGIN_ATTEMPT)
        elif stripped == self._LOGIN_SUCCESSFUL:
            return self._message_factory.create_state_update(ConnectionState.CONNECTED_LOGGED_IN)
        elif stripped == self._LOGIN_INCORRECT:
            return self._message_factory.create_state_update(ConnectionState.CONNECTED_LOGIN_INCORRECT)
        elif stripped == self._LNET_PROMPT:
            return self._message_factory.create_state_update(ConnectionState.CONNECTED_READY_FOR_COMMAND)
        else:
            return self._message_factory.create_response_data(stripped)
