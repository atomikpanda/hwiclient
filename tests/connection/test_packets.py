from hwiclient.connection.packets import PacketBuffer


def test_append():
    buffer = PacketBuffer()
    buffer.append(b"TEST")
    assert buffer.data == b"TEST"


def test_is_complete_login_bytes():
    buffer = PacketBuffer()
    buffer.append(PacketBuffer._LOGIN_BYTES)
    assert buffer.is_complete


def test_is_complete_lnet_bytes():
    buffer = PacketBuffer()
    buffer.append(PacketBuffer._LNET_BYTES)
    assert buffer.is_complete


def test_is_complete_newline_bytes():
    buffer = PacketBuffer()
    buffer.append(b"TEST" + PacketBuffer._NEWLINE_BYTES)
    assert buffer.is_complete


def test_is_complete_lnet_end_bytes():
    buffer = PacketBuffer()
    buffer.append(b"TEST" + PacketBuffer._LNET_BYTES)
    assert buffer.is_complete


def test_is_not_complete():
    buffer = PacketBuffer()
    buffer.append(b"INCOMPLETE")
    assert not buffer.is_complete


def test_clear():
    buffer = PacketBuffer()
    buffer.append(b"TEST")
    buffer.clear()
    assert buffer.data == PacketBuffer._EMPTY_BYTES
