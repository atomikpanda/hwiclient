import pytest

from hwiclient.connection.adapter import DataToResponseAdapter
from hwiclient.connection.message import ResponseMessage, ResponseMessageKind
from hwiclient.connection.state import ConnectionState as CS


@pytest.fixture
def adapter():
    return DataToResponseAdapter(encoding="utf-8")


def _assert_is_state_update(response: ResponseMessage, state: CS):
    assert isinstance(response, ResponseMessage)
    assert response.kind == ResponseMessageKind.STATE_UPDATE
    assert response.data == state


def test_adapt_login_prompt(adapter):
    data = b"LOGIN:"
    response = adapter.adapt(data)
    _assert_is_state_update(response, CS.CONNECTED_READY_FOR_LOGIN_ATTEMPT)


def test_adapt_login_successful(adapter):
    data = b"login successful"
    response = adapter.adapt(data)
    _assert_is_state_update(response, CS.CONNECTED_LOGGED_IN)


def test_adapt_login_incorrect(adapter):
    data = b"login incorrect"
    response = adapter.adapt(data)
    _assert_is_state_update(response, CS.CONNECTED_LOGIN_INCORRECT)


def test_adapt_lnet_prompt(adapter):
    data = b"LNET>"
    response = adapter.adapt(data)
    _assert_is_state_update(response, CS.CONNECTED_READY_FOR_COMMAND)


def test_adapt_other_data(adapter):
    data = b"some other data"
    response = adapter.adapt(data)
    assert response.kind == ResponseMessageKind.SERVER_RESPONSE_DATA
    assert response.data == "some other data"
    assert isinstance(response, ResponseMessage)
