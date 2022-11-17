"""Sample API Client."""
import logging
import asyncio
import socket
from typing import Optional
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

    async def async_get_data(self) -> dict:
        """Get data from the API."""
        return await self.api_wrapper("ws_get", self._url)

    async def async_send_command(self, command):
        return await self.api_wrapper("ws_set", self._url, command)

    async def async_set_title(self, value: str) -> None:
        """Get data from the API."""
        url = "https://jsonplaceholder.typicode.com/posts/1"
        await self.api_wrapper("patch", url, data={"title": value}, headers=HEADERS)

    def parse_message(self, msg):
        """parse socket message"""
        parsed = None

        try:
            if msg[0] == "#":
                if msg[1] == "?" or msg[1] == "$":
                    # ignore acks
                    _LOGGER.debug("Ignoring message %s", msg)
                    return
                # parse response
                value = msg[1::].split(":")[1].strip()
                key = msg[1::].split(":")[0]
                parsed = (key, value)
        except Exception as exc:
            _LOGGER.warning("Failed to parse message %s", msg)
            raise ParseError() from exc
        return parsed

    async def api_wrapper(
        self, method: str, url: str, data: dict = dict, headers: dict = dict
    ) -> dict:
        """Get information from the API."""

        try:
            async with async_timeout.timeout(TIMEOUT):
                if method == "ws_get":
                    state = {}
                    async with self._session.ws_connect(self._url) as websocket:
                        _LOGGER.debug("Connected to %s", url)
                        command = "#\r"
                        _LOGGER.debug("Outgoing message %s", command)
                        await websocket.send_str(command)
                        nsamples = 50
                        count = 0
                        _LOGGER.debug("Starting sampling of %d messages", nsamples)
                        async for msg in websocket:
                            try:
                                _LOGGER.debug("Incoming message [%d]: %s", count, msg)
                                parsed = self.parse_message(msg.data)
                                key, value = parsed
                                state[key] = value
                            except ParseError:
                                pass
                            count = count + 1
                            if count >= nsamples:
                                _LOGGER.debug(
                                    "Finished sampling, got %d messages", count
                                )
                                _LOGGER.debug("Got state %s", state)
                                return state
                elif method == "ws_set":
                    async with self._session.ws_connect(
                        self._url, headers=headers
                    ) as websocket:
                        await websocket.send_str(f"{data}\r")

        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                url,
                exception,
            )

        except (KeyError, TypeError) as exception:
            _LOGGER.error(
                "Error parsing information from %s - %s",
                url,
                exception,
            )
        except (aiohttp.ClientError, socket.gaierror) as exception:
            _LOGGER.error(
                "Error fetching information from %s - %s",
                url,
                exception,
            )
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Something really wrong happened! - %s", exception)


class ParseError(IntegrationError):
    pass
