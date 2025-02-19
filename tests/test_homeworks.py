from unittest.mock import AsyncMock, MagicMock

import pytest

from hwiclient.commands.hub import HubCommand
from hwiclient.connection.login import LutronServerAddress
from hwiclient.connection.message import ResponseMessage, ResponseMessageKind
from hwiclient.events import DeviceEventKey, DeviceEventKind
from hwiclient.homeworks import HomeworksHub
from hwiclient.monitoring import MonitoringTopic, TopicSubscriber


@pytest.fixture
def homeworks_config():
    return {
        "devices": {
            "room1": {"dimmers": [{"number": 1, "address": "1:1:1", "name": "light1"}]}
        }
    }


@pytest.fixture
def homeworks_hub(homeworks_config):
    return HomeworksHub(homeworks_config)


async def test_connect(homeworks_hub):
    server_address = MagicMock(spec=LutronServerAddress)
    homeworks_hub._coordinator.connect = AsyncMock(return_value=MagicMock())
    connection = await homeworks_hub.connect(server_address)
    homeworks_hub._coordinator.connect.assert_awaited_once_with(server_address)
    assert connection is not None


async def test_disconnect(homeworks_hub):
    homeworks_hub._coordinator.enqueue = AsyncMock()
    await homeworks_hub.disconnect()
    homeworks_hub._coordinator.enqueue.assert_awaited_once()


def test_handle_response_state_update(homeworks_hub):
    response = MagicMock(spec=ResponseMessage)
    response.kind = ResponseMessageKind.STATE_UPDATE
    assert homeworks_hub._handle_response(response) is True


def test_handle_response_server_response_data(homeworks_hub):
    response = MagicMock(spec=ResponseMessage)
    response.kind = ResponseMessageKind.SERVER_RESPONSE_DATA
    response.data = {"key": "value"}
    homeworks_hub._response_data_handler.handle = MagicMock()
    assert homeworks_hub._handle_response(response) is True
    homeworks_hub._response_data_handler.handle.assert_called_once_with(response.data)


def test_handle_response_not_implemented(homeworks_hub):
    response = MagicMock(spec=ResponseMessage)
    response.kind = "UNKNOWN_KIND"
    with pytest.raises(NotImplementedError):
        homeworks_hub._handle_response(response)


def test_devices_property(homeworks_hub):
    assert homeworks_hub.devices is not None


def test_ready_for_command_property(homeworks_hub):
    assert homeworks_hub.ready_for_command is True


@pytest.mark.asyncio
async def test_send_raw_command(homeworks_hub):
    homeworks_hub._coordinator.enqueue = AsyncMock()
    await homeworks_hub.send_raw_command("COMMAND", "arg1", "arg2")
    homeworks_hub._coordinator.enqueue.assert_awaited_once()


async def test_enqueue_command(homeworks_hub):
    command = MagicMock(spec=HubCommand)
    command._perform_command = AsyncMock()
    await homeworks_hub.enqueue_command(command)
    command._perform_command.assert_awaited_once_with(homeworks_hub)


def test_subscribe(homeworks_hub):
    subscriber = MagicMock(spec=TopicSubscriber)
    topic = MagicMock(spec=MonitoringTopic)
    homeworks_hub.subscribe(subscriber, topic)
    homeworks_hub._monitoring_topic_notifier.subscribe.assert_called_once_with(
        subscriber, topic
    )


def test_unsubscribe(homeworks_hub):
    subscriber = MagicMock(spec=TopicSubscriber)
    topic = MagicMock(spec=MonitoringTopic)
    homeworks_hub.unsubscribe(subscriber, topic)
    homeworks_hub._monitoring_topic_notifier.unsubscribe.assert_called_once_with(
        subscriber, topic
    )


def test_notify_subscribers(homeworks_hub):
    topic = DeviceEventKind.KEYPAD_BUTTON_PRESSED
    data = {DeviceEventKey.BUTTON_NUMBER: 1}
    homeworks_hub.notify_subscribers(topic, data)
    homeworks_hub._monitoring_topic_notifier.notify_subscribers.assert_called_once_with(
        topic, data
    )
