import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.util import Throttle

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from .gateway import Gateway
from .const import DOMAIN


_LOGGER: logging.Logger = logging.getLogger(__package__)


class SalerydLokeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, *args, **xargs) -> None:
        """Initialize."""
        self.platforms = []
        super().__init__(hass, _LOGGER, name=DOMAIN, *args, **xargs)
