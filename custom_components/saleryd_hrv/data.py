"""Custom types for integration"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration
    from pysaleryd.client import Client

    from .bridge import SalerydLokeBridge
    from .coordinator import SalerydLokeDataUpdateCoordinator


type SalerydLokeConfigEntry = ConfigEntry[SalerydLokeData]


@dataclass
class SalerydLokeData:
    """Data for the integration."""

    client: Client
    coordinator: SalerydLokeDataUpdateCoordinator
    integration: Integration
    bridge: SalerydLokeBridge
