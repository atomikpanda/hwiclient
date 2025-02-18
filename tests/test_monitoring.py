import pytest

from hwiclient.monitoring import (
    MonitoringTopic,
    MonitoringTopicKey,
    MonitoringTopicNotifier,
)


class TestSubscriber:
    def __init__(self):
        self.received_updates = []

    def on_topic_update(self, topic: MonitoringTopic, data: dict):
        self.received_updates.append((topic, data))


@pytest.fixture
def notifier():
    return MonitoringTopicNotifier()


@pytest.fixture
def subscriber():
    return TestSubscriber()


def test_subscribe_and_notify(notifier, subscriber):
    notifier.subscribe(subscriber, MonitoringTopic.DIMMER_LEVEL_CHANGED)
    data = {MonitoringTopicKey.LEVEL: 50}
    notifier.notify_subscribers(MonitoringTopic.DIMMER_LEVEL_CHANGED, data)
    assert subscriber.received_updates == [(MonitoringTopic.DIMMER_LEVEL_CHANGED, data)]


def test_unsubscribe(notifier, subscriber):
    notifier.subscribe(subscriber, MonitoringTopic.DIMMER_LEVEL_CHANGED)
    notifier.unsubscribe(subscriber, MonitoringTopic.DIMMER_LEVEL_CHANGED)
    data = {MonitoringTopicKey.LEVEL: 50}
    notifier.notify_subscribers(MonitoringTopic.DIMMER_LEVEL_CHANGED, data)
    assert subscriber.received_updates == []


def test_notify_multiple_subscribers(notifier):
    subscriber1 = TestSubscriber()
    subscriber2 = TestSubscriber()
    notifier.subscribe(subscriber1, MonitoringTopic.DIMMER_LEVEL_CHANGED)
    notifier.subscribe(subscriber2, MonitoringTopic.DIMMER_LEVEL_CHANGED)
    data = {MonitoringTopicKey.LEVEL: 50}
    notifier.notify_subscribers(MonitoringTopic.DIMMER_LEVEL_CHANGED, data)
    assert subscriber1.received_updates == [
        (MonitoringTopic.DIMMER_LEVEL_CHANGED, data)
    ]
    assert subscriber2.received_updates == [
        (MonitoringTopic.DIMMER_LEVEL_CHANGED, data)
    ]


def test_subscribe_to_multiple_topics(notifier, subscriber):
    notifier.subscribe(
        subscriber,
        MonitoringTopic.DIMMER_LEVEL_CHANGED,
        MonitoringTopic.KEYPAD_BUTTON_PRESS,
    )
    data1 = {MonitoringTopicKey.LEVEL: 50}
    data2 = {MonitoringTopicKey.BUTTON: 1}
    notifier.notify_subscribers(MonitoringTopic.DIMMER_LEVEL_CHANGED, data1)
    notifier.notify_subscribers(MonitoringTopic.KEYPAD_BUTTON_PRESS, data2)
    assert subscriber.received_updates == [
        (MonitoringTopic.DIMMER_LEVEL_CHANGED, data1),
        (MonitoringTopic.KEYPAD_BUTTON_PRESS, data2),
    ]
