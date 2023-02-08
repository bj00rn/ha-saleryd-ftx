"""Data update coordinator"""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from .const import DOMAIN


_LOGGER: logging.Logger = logging.getLogger(__package__)


class SalerydLokeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, *args, **xargs) -> None:
        """Initialize."""
        self.platforms = []
        super().__init__(hass, _LOGGER, name=DOMAIN, *args, **xargs)
