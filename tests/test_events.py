from hwiclient.events import (
    DeviceEventKey,
    DeviceEventKind,
    DeviceEventSource,
    EventListener,
    FilteredListener,
)


class TestEventListener:
    def on_event(self, kind: str, data: dict):
        pass


def test_register_listener():
    source = DeviceEventSource()
    listener = TestEventListener()
    source.register_listener(listener, None, DeviceEventKind.DIMMER_LEVEL_CHANGED)
    assert listener in source._listeners[DeviceEventKind.DIMMER_LEVEL_CHANGED]


def test_unregister_listener():
    source = DeviceEventSource()
    listener = TestEventListener()
    source.register_listener(listener, None, DeviceEventKind.DIMMER_LEVEL_CHANGED)
    source.unregister_listener(listener, DeviceEventKind.DIMMER_LEVEL_CHANGED)
    assert listener not in source._listeners[DeviceEventKind.DIMMER_LEVEL_CHANGED]


def test_post_event(mocker):
    source = DeviceEventSource()
    listener = mocker.Mock(spec=EventListener)
    source.register_listener(listener, None, DeviceEventKind.DIMMER_LEVEL_CHANGED)
    data = {DeviceEventKey.DIMMER_LEVEL: 50}
    source.post(DeviceEventKind.DIMMER_LEVEL_CHANGED, data)
    listener.on_event.assert_called_once_with(
        DeviceEventKind.DIMMER_LEVEL_CHANGED, data
    )


def test_filtered_listener(mocker):
    listener = mocker.Mock(spec=EventListener)
    filter = {DeviceEventKey.DIMMER_LEVEL: 50}
    filtered_listener = FilteredListener(listener, filter)
    data = {DeviceEventKey.DIMMER_LEVEL: 50}
    filtered_listener.on_event(DeviceEventKind.DIMMER_LEVEL_CHANGED, data)
    listener.on_event.assert_called_once_with(
        DeviceEventKind.DIMMER_LEVEL_CHANGED, data
    )


def test_filtered_listener_does_not_pass(mocker):
    listener = mocker.Mock(spec=EventListener)
    filter = {DeviceEventKey.DIMMER_LEVEL: 50}
    filtered_listener = FilteredListener(listener, filter)
    data = {DeviceEventKey.DIMMER_LEVEL: 30}
    filtered_listener.on_event(DeviceEventKind.DIMMER_LEVEL_CHANGED, data)
    listener.on_event.assert_not_called()
