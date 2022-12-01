
from abc import ABC, abstractmethod
from typing import Any
import logging
_LOGGER = logging.getLogger(__name__)

class EventBus(ABC):
    @abstractmethod
    def fire(self, event: str, obj: Any):
        pass


class LoggerEventBus(EventBus):
    def fire(self, event: str, obj: Any):
        _LOGGER.info(f"event fired {event}: {obj}")
