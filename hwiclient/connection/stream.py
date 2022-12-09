import asyncio
from typing import Iterable


class _WriterHelper:
    def __init__(self, writer: asyncio.StreamWriter, encoding: str):
        self._encoding = encoding
        self._writer = writer

    async def write_str(self, data: str):
        assert self._writer != None
        self._writer.write(data.encode(self._encoding))
        self._writer.write(b"\r\n")
        return await self._writer.drain()

    async def write_login(self, username: str, password: str):
        await self.write_str(f"{username},{password}")

    def close(self):
        self._writer.close()


class _ReaderHelper:
    def __init__(self, reader: asyncio.StreamReader, encoding: str):
        self._encoding = encoding
        self._reader = reader

    def _decode(self, data: bytes) -> str:
        decoded = data.decode(self._encoding)
        return decoded

    async def read_login_prompt(self) -> str:
        data = await self._reader.read(1024)
        return self._decode(data).strip()

    async def read_str(self) -> str:
        data = await self._reader.read(1024)
        return self._decode(data)

    async def readline(self, strip: bool = False) -> str:
        data = await self._reader.readline()
        return self._decode(data).strip() if strip else self._decode(data)

    async def readuntil(self, message: str, strip: bool = False) -> str:
        data = await self._reader.readuntil(message.encode(self._encoding))
        return self._decode(data).strip() if strip else self._decode(data)

    async def readlines_until_lnet(self) -> list[str]:
        lines = (await self.readuntil("LNET>", True)).splitlines()
        result = []
        for line in lines:
            if line.strip() == "" or line.strip() == "LNET>":
                continue
            result.append(line.strip())
        return result

    async def readlines(self) -> list[str]:
        buffer = ""
        
        while not (buffer.strip().endswith("LNET>") or buffer.strip().find("closing connection") != -1):
            just_read = await self._reader.read(1024)
            if len(just_read) == 0:
                break
            else:
                buffer += self._decode(just_read)
                print("j: ", just_read)
            pass
        
        lines = buffer.splitlines()
        result = []
        for line in lines:
            if line.strip() == "" or line.strip() == "LNET>":
                continue
            result.append(line.strip())
        return result

    async def read_login_response(self) -> str:
        return await self.readline(True)
