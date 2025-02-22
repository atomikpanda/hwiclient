import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from hwiclient.commands.hub import HubCommand
from hwiclient.commands.sender import CommandSender
from hwiclient.connection.login import LutronServerAddress
from hwiclient.connection.message import ResponseMessage, ResponseMessageKind
from hwiclient.homeworks import HomeworksHub
from hwiclient.monitoring import MonitoringTopic, MonitoringTopicKey, TopicSubscriber


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


class TestSubscriber(TopicSubscriber):
    def __init__(self):
        self.notified = False
        self.data = None

    def on_topic_update(self, topic: MonitoringTopic, data: dict):
        self.notified = True
        self.data = data


async def test_enqueue_command(homeworks_hub):
    class TestCommand(HubCommand):
        def __init__(self):
            self.executed = False

        async def _perform_command(self, sender: CommandSender):
            self.executed = True

    command = TestCommand()
    await homeworks_hub.enqueue_command(command)
    # Delay
    await asyncio.sleep(1)
    assert command.executed


def test_subscribe(homeworks_hub):
    subscriber = TestSubscriber()
    topic = MonitoringTopic.DIMMER_LEVEL_CHANGED
    homeworks_hub.subscribe(subscriber, topic)
    assert subscriber in homeworks_hub._monitoring_topic_notifier._subscribers[topic]


def test_unsubscribe(homeworks_hub):
    subscriber = TestSubscriber()
    topic = MonitoringTopic.KEYPAD_BUTTON_DOUBLE_TAP
    homeworks_hub.subscribe(subscriber, topic)
    homeworks_hub.notify_subscribers(topic, {MonitoringTopicKey.BUTTON: 1})
    assert subscriber.notified
    assert subscriber.data == {MonitoringTopicKey.BUTTON: 1}
    subscriber.notified = False
    subscriber.data = None
    homeworks_hub.unsubscribe(subscriber, topic)
    homeworks_hub.notify_subscribers(topic, {MonitoringTopicKey.BUTTON: 2})
    assert not subscriber.notified
    assert subscriber.data is None


def test_notify_subscribers(homeworks_hub):
    subscriber = TestSubscriber()
    topic = MonitoringTopic.KEYPAD_BUTTON_PRESS
    data = {MonitoringTopicKey.BUTTON: 1}
    homeworks_hub.subscribe(subscriber, topic)
    homeworks_hub.notify_subscribers(topic, data)
    assert subscriber.notified
    assert subscriber.data == data
