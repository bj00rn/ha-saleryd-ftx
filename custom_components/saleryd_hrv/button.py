from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.helpers.entity import EntityCategory
from homeassistant.util import slugify
from pysaleryd.const import DataKeyEnum

from .const import CONF_ENABLE_INSTALLER_SETTINGS, SystemActiveModeEnum
from .entity import SaleryLokeVirtualEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import SalerydLokeConfigEntry


class SalerydLokeButton(SaleryLokeVirtualEntity, ButtonEntity):
    def __init__(self, entry: "SalerydLokeConfigEntry", entity_description):
        self._entry = entry
        self.entity_id = f"button.{entry.unique_id}_{slugify(entity_description.name)}"
        super().__init__(entry, entity_description)


class SalerydLokeSystemResetButton(SalerydLokeButton):
    async def async_press(self):
        await self._entry.runtime_data.bridge.send_command(
            DataKeyEnum.CONTROL_SYSTEM_STATE, SystemActiveModeEnum.Reset, True
        )


async def async_setup_entry(
    hass: "HomeAssistant",
    entry: "SalerydLokeConfigEntry",
    async_add_entities: "AddEntitiesCallback",
):
    if entry.data.get(CONF_ENABLE_INSTALLER_SETTINGS):
        config_entities = [
            SalerydLokeSystemResetButton(
                entry,
                ButtonEntityDescription(
                    key=DataKeyEnum.CONTROL_SYSTEM_STATE,
                    name="System reset",
                    entity_category=EntityCategory.CONFIG,
                    icon="mdi:restart",
                ),
            )
        ]
        async_add_entities(config_entities)
