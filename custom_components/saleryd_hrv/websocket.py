"""Python library to connect HRV and Home Assistant to work together."""

from asyncio import create_task, get_running_loop
from collections import deque
from collections.abc import Callable, Coroutine
import enum
import logging
from typing import Any, Final
import datetime
import aiohttp

LOGGER = logging.getLogger(__package__)


class Signal(enum.Enum):
    """What is the content of the callback."""

    CONNECTION_STATE = "state"
    DATA = "data"


class State(enum.Enum):
    """State of the connection."""
    NONE = ""
    RETRYING = "retrying"
    RUNNING = "running"
    STOPPED = "stopped"


RETRY_TIMER: Final = 15
QUEUE_LEN: Final = 100


class WSClient:
    """Websocket transport, session handling, message generation."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        callback: Callable[[Signal], Coroutine[Any, Any, None]],
    ) -> None:
        """Create resources for websocket communication."""
        self.session = session
        self.host = host
        self.port = port
        self.session_handler_callback = callback

        self.loop = get_running_loop()
        self._ws = None

        self._data: deque[dict[str, Any]] = deque(maxlen=QUEUE_LEN)
        self._state = self._previous_state = State.NONE

    @property
    def data(self) -> dict[str, Any]:
        """Return data from data queue."""
        try:
            return list(self._data.copy())
        except IndexError:
            return []

    @property
    def state(self) -> State:
        """State of websocket."""
        return self._state

    def set_state(self, value: State) -> None:
        """Set state of websocket and store previous state."""
        self._previous_state = self._state
        self._state = value

    def state_changed(self) -> None:
        """Signal state change."""
        create_task(self.session_handler_callback(Signal.CONNECTION_STATE))

    def start(self) -> None:
        """Start websocket and update its state."""
        create_task(self.running())

    async def running(self) -> None:
        """Start websocket connection."""
        if self._state == State.RUNNING:
            return

        url = f"http://{self.host}:{self.port}"

        try:
            self._ws = await self.session.ws_connect(url)
            LOGGER.info("Connected to websocket (%s)", self.host)
            self.set_state(State.RUNNING)
            self.state_changed()
            await self._ws.send_str("#\r")

            async for msg in self._ws:

                if self._state == State.STOPPED:
                    await self._ws.close()
                    break

                if msg.type == aiohttp.WSMsgType.TEXT:
                    self._data.append(msg.data)
                    create_task(self.session_handler_callback(Signal.DATA))
                    LOGGER.debug("%s Received: %s", datetime.datetime.now(), msg.data)
                    continue

                if msg.type == aiohttp.WSMsgType.CLOSED:
                    LOGGER.warning("Connection closed (%s)", self.host)
                    break

                if msg.type == aiohttp.WSMsgType.ERROR:
                    LOGGER.error("Websocket error (%s)", self.host)
                    break

        except aiohttp.ClientConnectorError:
            if self._state != State.RETRYING:
                LOGGER.error("Websocket is not accessible (%s)", self.host)

        except Exception as err:
            if self._state != State.RETRYING:
                LOGGER.error("Unexpected error (%s) %s", self.host, err)

        if self._state != State.STOPPED:
            self.retry()

    def stop(self) -> None:
        """Close websocket connection."""
        self.set_state(State.STOPPED)
        LOGGER.info("Shutting down connection to websocket (%s)", self.host)

    def retry(self) -> None:
        """Retry to connect to websocket.

        Do an immediate retry without timer and without signalling state change.
        Signal state change only after first retry fails.
        """
        if self._state == State.RETRYING and self._previous_state == State.RUNNING:
            LOGGER.info(
                "Reconnecting to websocket (%s) failed, scheduling retry at an interval of %i seconds",
                self.host,
                RETRY_TIMER,
            )
            self.state_changed()

        self.set_state(State.RETRYING)

        if self._previous_state == State.RUNNING:
            LOGGER.info("Reconnecting to websocket (%s)", self.host)
            self.start()
            return

        self.loop.call_later(RETRY_TIMER, self.start)

    async def send_message(self, message):
        """Send message to websocket"""
        if self._state != State.RUNNING:
            raise Exception(
                "Failed to send message %s to websocket. Socket state is %s",
                message,
                self.state,
            )

        await self._ws.send_str(message)
