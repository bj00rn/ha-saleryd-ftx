import logging
import asyncio
from .websocket import WSClient, Signal, State

_LOGGER: logging.Logger = logging.getLogger(__package__)


class Gateway:
    """Gateway to manage communication with HRV"""

    def __init__(self, session, url, port):
        self._url = url
        self._port = port
        self._session = session
        self._state = State.NONE
        self._handlers = []
        self._client = WSClient(self._session, self._url, self._port, self._handler)
        self._client.start()

    def add_handler(self, handler):
        """Add event handler"""
        self._handlers.append(handler)

    async def _handler(self, signal: Signal):
        """Call handlers if data"""
        if signal == Signal.DATA:
            for handler in self._handlers:
                handler(self.data)
        elif signal == Signal.CONNECTION_STATE:
            self._state = self._client.state

    def _parse_message(self, msg):
        """parse socket message"""
        parsed = None

        try:
            if msg[0] == "#":
                if msg[1] == "$":
                    # ack message, strip ack char and treat as state update
                    msg = msg[1::]
                value = msg[1::].split(":")[1].strip()
                if msg[1] != "*":
                    # messages not beginning with * are arrays of integers
                    # [value, min, max] or [value, min, max, time_left]
                    value = [
                        int(v.strip()) if v.strip().isnumeric() else v.strip()
                        for v in value.split("+")
                    ]
                key = msg[1::].split(":")[0]
                parsed = (key, value)
        except Exception as exc:
            _LOGGER.warning("Failed to parse message %s", msg, exc_info=True)
        return parsed

    @property
    def state(self):
        return self._state

    @property
    def data(self):
        """Get data"""
        data = self._client.data
        parsed_data = {}

        for message in data:
            parsed_message = self._parse_message(message)
            if parsed_message:
                (key, value) = parsed_message
                parsed_data[key] = value

        return parsed_data

    async def async_get_data(self):
        return self.data

    async def send_command(self, key, value):
        """Send command to HRV"""

        async def ack_command():
            """Should probably ack command here, just sleep for now"""
            await asyncio.sleep(2)

        await self._client.send_message(f"#{key}:{value}\r")
        await asyncio.gather(ack_command())
