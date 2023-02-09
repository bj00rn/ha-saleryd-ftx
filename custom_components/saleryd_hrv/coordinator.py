"""Data update coordinator"""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from .const import DOMAIN, SUPPORTED_FIRMWARES


_LOGGER: logging.Logger = logging.getLogger(__package__)


class SalerydLokeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, *args, **xargs) -> None:
        """Initialize."""
        self.platforms = []
        super().__init__(hass, _LOGGER, name=DOMAIN, *args, **xargs)

    async def _async_update_data(self):
        """Fetch the latest data from the source."""
        data = await self.update_method()
        version = data.get("*SC")
        if version and version not in SUPPORTED_FIRMWARES:
            _LOGGER.warning(
                "Unsupported control system (%s). This integration has been verified to work with the following systems: %s",
                version,
                ", ".join(SUPPORTED_FIRMWARES),
            )
        return data
