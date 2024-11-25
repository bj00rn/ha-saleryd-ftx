"""Data update coordinator"""

from logging import Logger
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, KEY_CLIENT_STATE, KEY_TARGET_TEMPERATURE

if TYPE_CHECKING:
    from .data import SalerydLokeConfigEntry


class SalerydLokeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: "SalerydLokeConfigEntry"

    def inject_virtual_keys(self, data):
        """Inject additional keys for virtual sensors not present in the data set"""
        data[KEY_CLIENT_STATE] = self.config_entry.runtime_data.client.state.name
        data[KEY_TARGET_TEMPERATURE] = None

    def __init__(self, hass: HomeAssistant, logger: Logger) -> None:
        """Initialize."""
        self.platforms = []
        super().__init__(hass, logger, name=DOMAIN)

    async def _async_update_data(self):
        """Fetch the latest data from the source."""
        return self.data or dict()

    def async_set_updated_data(self, data) -> None:
        self.logger.debug("Received data")
        _data = data.copy()
        self.inject_virtual_keys(_data)
        return super().async_set_updated_data(_data)
