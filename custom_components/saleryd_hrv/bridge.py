from typing import TYPE_CHECKING

from pysaleryd.const import DataKeyEnum

from .const import CONF_INSTALLER_PASSWORD, KEY_CLIENT_STATE, KEY_TARGET_TEMPERATURE

if TYPE_CHECKING:
    from pysaleryd.client import Client

    from .coordinator import SalerydLokeDataUpdateCoordinator
    from .data import SalerydLokeConfigEntry


class SalerydLokeBridge:
    """Representation of bridge between client and coordinator"""

    def __init__(
        self, client: "Client", coordinator: "SalerydLokeDataUpdateCoordinator", logger
    ):
        self.client = client
        self.coordinator = coordinator
        self.logger = logger

        self.client.add_handler(self.update_data_callback)

    def update_data_callback(self, data):
        """Update coordindator data"""
        self.logger.debug("Received data")
        _data = data.copy()
        self.__inject_virtual_keys(_data)
        self.coordinator.async_set_updated_data(data)

    def __inject_virtual_keys(self, data):
        """Inject additional keys for virtual sensors not present in the data set"""
        data[KEY_CLIENT_STATE] = self.client.state.name
        data[KEY_TARGET_TEMPERATURE] = None

    async def send_command(self, key: DataKeyEnum, data: str | int, auth: bool = False):
        """Send command to client"""

        async def send(key, data):
            self.logger.debug("Sending control request %s with payload %s", key, data)
            await self.client.send_command(key, data)

        if auth:
            installer_password = self._entry.data.get(CONF_INSTALLER_PASSWORD)
            await send(DataKeyEnum.INSTALLER_PASSWORD, installer_password)
        await send(key, data)
