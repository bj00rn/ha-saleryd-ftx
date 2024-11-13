"""Data update coordinator"""

from logging import Logger

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pysaleryd.client import Client

from .const import DOMAIN, KEY_CLIENT_STATE, KEY_TARGET_TEMPERATURE


class SalerydLokeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, client: Client, logger: Logger) -> None:
        """Initialize."""
        self.platforms = []
        self.client = client
        self.client.add_handler(self.async_set_updated_data)
        super().__init__(hass, logger, name=DOMAIN)

    def inject_virtual_keys(self, data):
        """Inject additional keys for virtual sensors not present in the data set"""
        data[KEY_CLIENT_STATE] = self.client.state
        data[KEY_TARGET_TEMPERATURE] = None

    async def _async_update_data(self):
        """Fetch the latest data from the source."""
        data = self.client.data.copy()
        self.inject_virtual_keys(data)
        return data

    def async_set_updated_data(self, data) -> None:
        self.logger.debug("Received data")
        _data = data.copy()
        self.inject_virtual_keys(_data)
        return super().async_set_updated_data(_data)

    async def send_command(self, key, data):
        """Send command to client"""
        await self.client.send_command(key, data)
