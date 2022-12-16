from .message import ReponseMessageFactory, ResponseMessage, ResponseMessageKind
from .state import ConnectionState as CS
import logging
_LOGGER = logging.getLogger(__name__)


class DataToResponseAdapter:
    _LOGIN_PROMPT = 'LOGIN:'
    _LNET_PROMPT = 'LNET>'
    _LOGIN_SUCCESSFUL = 'login successful'
    _LOGIN_INCORRECT = 'login incorrect'

    def __init__(self, encoding: str):
        self._encoding = encoding
        self._factory = ReponseMessageFactory()

    def adapt(self, data: bytes) -> ResponseMessage:
        message = data.decode(self._encoding)
        stripped = message.strip()
        _LOGGER.debug('adapting string data to response %s' % stripped)
        if stripped == self._LOGIN_PROMPT:
            return self._factory.create_state_update(CS.CONNECTED_READY_FOR_LOGIN_ATTEMPT)
        elif stripped == self._LOGIN_SUCCESSFUL:
            return self._factory.create_state_update(CS.CONNECTED_LOGGED_IN)
        elif stripped == self._LOGIN_INCORRECT:
            return self._factory.create_state_update(CS.CONNECTED_LOGIN_INCORRECT)
        elif stripped == self._LNET_PROMPT:
            return self._factory.create_state_update(CS.CONNECTED_READY_FOR_COMMAND)
        else:
            return self._factory.create_response_data(stripped)
