class PacketBuffer:
    _LOGIN_BYTES = b"LOGIN: "
    _LNET_BYTES = b"\r\nLNET> "
    _NEWLINE_BYTES = b"\r\n"
    _EMPTY_BYTES = b""

    def __init__(self) -> None:
        self._buffer = self._EMPTY_BYTES

    def append(self, packet: bytes):
        self._buffer += packet

    @property
    def is_complete(self) -> bool:
        if self._buffer == self._LOGIN_BYTES:
            return True
        elif self._buffer == self._LNET_BYTES:
            return True
        elif self._buffer.endswith(self._NEWLINE_BYTES):
            return True
        elif self._buffer.endswith(self._LNET_BYTES):
            return True
        return False

    @property
    def data(self) -> bytes:
        return self._buffer

    def clear(self) -> None:
        self._buffer = self._EMPTY_BYTES
