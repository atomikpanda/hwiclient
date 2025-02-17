from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Protocol

_LOGGER = logging.getLogger(__name__)


class MonitoringTopic(str, Enum):
    DIMMER_LEVEL_CHANGED = "DL"
    KEYPAD_BUTTON_PRESS = "KBP"
    KEYPAD_BUTTON_RELEASE = "KBR"
    KEYPAD_BUTTON_HOLD = "KBH"
    KEYPAD_BUTTON_DOUBLE_TAP = "KBDT"
    KEYPAD_LED_STATES_CHANGED = "KLS"


class MonitoringTopicKey(str, Enum):
    ADDRESS = "address"
    BUTTON = "button"
    LEVEL = "level"
    LED_STATES = "led_states"


class TopicSubscriber(Protocol):
    def on_topic_update(self, topic: MonitoringTopic, data: dict):
        pass


class TopicNotifier(Protocol):
    def subscribe(self, subscriber: TopicSubscriber, *topics: MonitoringTopic):
        pass

    def unsubscribe(self, subscriber: TopicSubscriber, *topics: MonitoringTopic):
        pass

    def notify_subscribers(self, topic: MonitoringTopic, data: dict):
        pass


class MonitoringTopicNotifier(TopicNotifier):
    def __init__(self):
        self._subscribers: dict[MonitoringTopic, list[TopicSubscriber]] = {}

    def subscribe(self, subscriber: TopicSubscriber, *topics: MonitoringTopic):
        for topic in topics:
            if topic not in self._subscribers:
                self._subscribers[topic] = [subscriber]
            else:
                self._subscribers[topic].append(subscriber)

    def unsubscribe(self, subscriber: TopicSubscriber, *topics: MonitoringTopic):
        for topic in topics:
            if topic in self._subscribers:
                self._subscribers[topic].remove(subscriber)

    def notify_subscribers(
        self, topic: MonitoringTopic, data: dict[MonitoringTopicKey, Any]
    ):
        _LOGGER.warning(f"TOPIC {topic} data={data}")
        if topic in self._subscribers:
            for subscriber in self._subscribers[topic]:
                subscriber.on_topic_update(topic, data)
