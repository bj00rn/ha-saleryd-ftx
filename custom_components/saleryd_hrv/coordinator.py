"""Data update coordinator"""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pysaleryd.client import Client

from .const import CLIENT_STATE, DOMAIN, SUPPORTED_FIRMWARES, UNSUPPORTED_FIRMWARES

_LOGGER: logging.Logger = logging.getLogger(__package__)


class SalerydLokeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, client: Client, update_interval) -> None:
        """Initialize."""
        self.platforms = []
        self.client = client
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self):
        """Fetch the latest data from the source."""
        data = self.client.data
        version = data.get("*SC")
        if version:
            if version not in SUPPORTED_FIRMWARES:
                _LOGGER.warning(
                    "Your control system version is (%s). This integration has been verified to work with the following versions: %s",
                    version,
                    ", ".join(SUPPORTED_FIRMWARES),
                )
            if version in UNSUPPORTED_FIRMWARES:
                _LOGGER.error(
                    "Your control system version is (%s). This integration is incompatible with the following versions: %s",
                    version,
                    ", ".join(UNSUPPORTED_FIRMWARES),
                )
        data[CLIENT_STATE] = self.client.state
        return data
