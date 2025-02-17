from datetime import timedelta

import pytest

from hwiclient.commands.dimmer import FadeDimmer, RequestDimmerLevel, StopDimmer
from hwiclient.commands.sender import CommandSender
from hwiclient.device import DeviceAddress


@pytest.fixture
def mock_sender(mocker):
    return mocker.AsyncMock(spec=CommandSender)


@pytest.fixture
def device_address():
    return DeviceAddress("1:1:1")


def test_fade_dimmer_initialization(device_address):
    fade_dimmer = FadeDimmer(
        50, timedelta(seconds=10), timedelta(seconds=5), device_address
    )
    assert fade_dimmer._intensity == 50
    assert fade_dimmer._fade_time == timedelta(seconds=10)
    assert fade_dimmer._delay_time == timedelta(seconds=5)
    assert fade_dimmer._dimmer_adresses == (device_address,)


def test_fade_dimmer_invalid_intensity(device_address):
    with pytest.raises(ValueError, match="intensity must be between 0 and 100"):
        FadeDimmer(150, timedelta(seconds=10), timedelta(seconds=5), device_address)


def test_fade_dimmer_no_addresses():
    with pytest.raises(ValueError, match="At least one dimmer address is required"):
        FadeDimmer(50, timedelta(seconds=10), timedelta(seconds=5))


def test_fade_dimmer_too_many_addresses(device_address):
    addresses = [device_address] * 11
    with pytest.raises(ValueError, match="Exceeded max limit of 10 dimmer addresses"):
        FadeDimmer(50, timedelta(seconds=10), timedelta(seconds=5), *addresses)


@pytest.mark.asyncio
async def test_fade_dimmer_perform_command(mock_sender, device_address):
    fade_dimmer = FadeDimmer(
        50, timedelta(seconds=10), timedelta(seconds=5), device_address
    )
    await fade_dimmer.execute(mock_sender)
    mock_sender.send_raw_command.assert_called_once_with(
        "FADEDIM", "50", "00:00:10", "00:00:05", device_address.unencoded_with_brackets
    )


def test_request_dimmer_level_initialization(device_address):
    request_dimmer_level = RequestDimmerLevel(device_address)
    assert request_dimmer_level._address == device_address


async def test_request_dimmer_level_perform_command(mock_sender, device_address):
    request_dimmer_level = RequestDimmerLevel(device_address)
    await request_dimmer_level.execute(mock_sender)
    mock_sender.send_raw_command.assert_called_once_with(
        "RDL", device_address.unencoded_with_brackets
    )


def test_stop_dimmer_initialization(device_address):
    stop_dimmer = StopDimmer(device_address)
    assert stop_dimmer._dimmer_adresses == (device_address,)


def test_stop_dimmer_no_addresses():
    with pytest.raises(ValueError, match="At least one dimmer address is required"):
        StopDimmer()


def test_stop_dimmer_too_many_addresses(device_address):
    addresses = [device_address] * 11
    with pytest.raises(ValueError, match="Exceeded max limit of 10 dimmer addresses"):
        StopDimmer(*addresses)


async def test_stop_dimmer_perform_command(mock_sender, device_address):
    stop_dimmer = StopDimmer(device_address)
    await stop_dimmer.execute(mock_sender)
    mock_sender.send_raw_command.assert_called_once_with(
        "STOPDIM", device_address.unencoded_with_brackets
    )
