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

    def __init__(self, hass: HomeAssistant, gateway: Gateway) -> None:
        """Initialize."""
        self._gateway = gateway

        self.platforms = []

        self._gateway.add_handler(self.async_set_updated_data)

        super().__init__(hass, _LOGGER, name=DOMAIN)

    @Throttle(timedelta(seconds=10))
    def async_set_updated_data(self, data) -> None:
        super().async_set_updated_data(data)
