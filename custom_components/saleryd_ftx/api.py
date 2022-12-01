"""Sample API Client."""
import logging
import asyncio
import socket
from datetime import date, datetime
import aiohttp
import async_timeout
from homeassistant.exceptions import IntegrationError

TIMEOUT = 10
SAMPLE_TIMEOUT = 5


_LOGGER: logging.Logger = logging.getLogger(__package__)

HEADERS = {"Content-type": "application/json; charset=UTF-8"}


class SalerydLokeApiClient:
    """Api Client"""

    def __init__(self, url, session: aiohttp.ClientSession) -> None:
        """Sample API Client."""
        self._url = url
        self._session = session
        self._ws = None
        self._consumer = None

    async def init_ws(self):
        """Init websocket connection"""
        async with async_timeout.timeout(TIMEOUT):
            _LOGGER.debug("Connecting to websocket %s", self._url)
            self._ws = await self._session.ws_connect(self._url)
            _LOGGER.debug("Connnected to websocket %s", self._url)
            # Set time on server and begin connection
            command = f"#CS:{date.strftime(datetime.now(), '%y-%m-%d-%w-%H-%M-%S')}"
            await self._ws.send_str(command)
            # Server should begin sending messages. Make sure we receive at least one message
            response = await self._ws.receive_str()
            _LOGGER.debug("Received first message from websocket: %s", response)

    async def listen(self):
        async for msg in self._ws:
            key, value = self._parse_message(msg)
            self.state[key] = value

    async def async_get_data(self) -> dict:
        """Get data from the API."""
        is_socket_open = True

        if not self._ws:
            _LOGGER.debug("Websocket needs setting up")
            is_socket_open = False
        elif self._ws.closed:
            _LOGGER.debug("Websocket was closed. Needs setting up")
            is_socket_open = False

        if not is_socket_open:
            await self.init_ws()

        return await self.api_wrapper("ws_get", self._url)

    async def async_send_command(self, data):
        """Send data to API"""
        _LOGGER.debug("Outgoing command %s", data)
        return await self.api_wrapper("ws_set", data)

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
                    value = value.split("+")
                key = msg[1::].split(":")[0]
                parsed = (key, value)
        except Exception as exc:
            _LOGGER.warning("Failed to parse message %s", msg, exc_info=True)
            raise ParseError() from exc
        return parsed

    async def api_wrapper(self, method, data: str = dict) -> dict:
        """Get information from the API."""

        try:
            async with async_timeout.timeout(TIMEOUT):
                if method == "ws_get":
                    state = dict()
                    count = 0
                    _LOGGER.debug("Starting collection of messages from server")
                    while True:
                        msg = await self._ws.receive_str()
                        try:
                            _LOGGER.debug("Incoming message [%d]: %s", count, msg)
                            parsed = self._parse_message(msg)
                            key, value = parsed
                            if state.get(key) and key != "*CV":
                                # We are done
                                _LOGGER.debug(
                                    "Finished sampling, got %d messages", count
                                )
                                _LOGGER.debug("Got state %s", state)
                                return state
                            state[key] = value
                        except ParseError:
                            pass
                        count = count + 1
                elif method == "ws_set":
                    await self._ws.send_str(f"{data}\r")

        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                self._url,
                exception,
                exc_info=True,
            )
            raise exception

        except (KeyError, TypeError) as exception:
            _LOGGER.error(
                "Error parsing information from %s - %s",
                self._url,
                exception,
                exc_info=True,
            )
            raise exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            _LOGGER.error(
                "Error fetching information from %s - %s",
                self._url,
                exception,
                exc_info=True,
            )
            raise exception
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error(
                "Something really wrong happened! - %s", exception, exc_info=True
            )
            raise exception


class ParseError(IntegrationError):
    """Error when parsing websocket message fails"""

    pass
