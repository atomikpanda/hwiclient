from .stream import _ReaderHelper, _WriterHelper
from typing import Tuple
import asyncio


class TcpConnection:
    def __init__(self, streams: Tuple[asyncio.StreamReader, asyncio.StreamWriter], encoding: str):
        self._reader = _ReaderHelper(streams[0], encoding)
        self._writer = _WriterHelper(streams[1], encoding)

    @property
    def reader(self) -> _ReaderHelper:
        return self._reader

    @property
    def writer(self) -> _WriterHelper:
        return self._writer

    def close(self):
        self._writer.close()
