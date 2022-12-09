
from .login import LutronCredentials
from .message import RequestMessage, ResponseMessage, ResponseMessageKind, RequestMessageKind, Transport
from .listener import ConnectionState
from .tcp import TcpConnection
from queue import Empty

class LutronSession:
    _LNET_PROMPT = "LNET>"
    _CLOSING_CONNECTION = "closing connection due to"

    def __init__(self, connection: TcpConnection, credentials: LutronCredentials):
        self._disconnect = False
        self._connection = connection
        self._credentials = credentials

    async def disconnect(self):
        self._disconnect = True
        await self._connection.writer.write_str("QUIT")
        self._connection.close()

    async def _process_send_message(self, message: RequestMessage):
        if message.kind == RequestMessageKind.SEND_DATA:
            await self._connection.writer.write_str(message.data)
        elif message.kind == RequestMessageKind.SEND_COMMAND:
            await self._connection.writer.write_str(message.data)
        elif message.kind == RequestMessageKind.DISCONNECT:
            await self.disconnect()
            
    async def _send_next_pending_request(self, transport: Transport):
        try:
            request_to_send = transport.get_request()
            await self._process_send_message(request_to_send)
        except Empty:
            return
            
    async def send_and_receive_on_transport(self, transport: Transport):
        reader = self._connection.reader
        while self._disconnect == False:
            line = await reader.readline()
            
            if len(line) > 0 and len(line.strip()) > 0:
                line = line.strip()
                print(f"`{{{line}}}`")
                # If line is just a blank lnet prompt notify ready for command
                if line == self._LNET_PROMPT:
                    transport.send_response(ResponseMessage(
                        ResponseMessageKind.STATE_UPDATE, ConnectionState.CONNECTED_READY_FOR_COMMAND))
                else:
                    # Remove LNET prompt prefix
                    without_prompt = line.removeprefix(self._LNET_PROMPT).strip()
                    
                    if without_prompt.startswith(self._CLOSING_CONNECTION):
                        self._disconnect = True
                        break
                    else:
                        # Send response data
                        transport.send_response(ResponseMessage(
                            ResponseMessageKind.SERVER_RESPONSE_DATA, without_prompt))
            
            await self._send_next_pending_request(transport)
