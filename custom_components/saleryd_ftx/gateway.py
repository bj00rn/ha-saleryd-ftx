import logging
from .websocket import WSClient, Signal

_LOGGER: logging.Logger = logging.getLogger(__package__)


class Gateway:
    """Gateway to manage communication with FTX"""

    def __init__(self, session, url, port):
        self._url = url
        self._port = port
        self._session = session
        self._ws = WSClient(self._session, self._url, self._port, self._handler)
        self._ws.start()
        self._handlers = []

    def add_handler(self, handler):
        """Add event handler"""
        self._handlers.append(handler)

    async def _handler(self, signal: Signal):
        """Call handlers"""
        if signal == Signal.DATA:
            for handler in self._handlers:
                handler(self.data)

    def _parse_message(self, msg):
        """parse socket message"""
        parsed = None

        try:
            if msg[0] == "#":
                if msg[1] == "?" or msg[1] == "$":
                    # ignore all acks end ack errors for now
                    _LOGGER.debug("Ignoring ack message %s", msg)
                    return

                value = msg[1::].split(":")[1].strip()
                if msg[1] != "*":
                    # messages beginning with * are arrays
                    # [value, min, max] or [value, min, max, time_left]
                    value = [v.strip() for v in value.split("+")]
                key = msg[1::].split(":")[0]
                parsed = (key, value)
        except Exception as exc:
            _LOGGER.warning("Failed to parse message %s", msg, exc_info=1)
        return parsed

    @property
    def data(self):
        """Get data"""
        data = self._ws.data
        parsed_data = {}

        for message in data:
            parsed_message = self._parse_message(message)
            if parsed_message:
                (key, value) = parsed_message
                parsed_data[key] = value

        return parsed_data

    async def send_command(self, key, value):
        """Send command to FTX"""
        await self._ws.send_message(f"#{key}:{value}\r")
