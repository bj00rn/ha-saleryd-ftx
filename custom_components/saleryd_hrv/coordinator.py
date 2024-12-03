"""Data update coordinator"""

from logging import Logger
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pysaleryd.const import DataKeyEnum

from .const import DOMAIN, KEY_CLIENT_STATE, KEY_TARGET_TEMPERATURE

if TYPE_CHECKING:
    from .data import SalerydLokeConfigEntry


class SalerydLokeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: "SalerydLokeConfigEntry"

    def __init__(self, hass: HomeAssistant, logger: Logger) -> None:
        """Initialize."""
        super().__init__(hass, logger, name=DOMAIN)

    async def _async_update_data(self):
        """Fetch the latest data from the source."""
        return self.data or dict()
