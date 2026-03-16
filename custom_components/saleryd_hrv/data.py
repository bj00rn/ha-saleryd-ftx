"""Custom types for integration"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from homeassistant.loader import Integration
    from pysaleryd.client import Client

    from .bridge import SalerydLokeBridge
    from .coordinator import SalerydLokeDataUpdateCoordinator


@dataclass
class SalerydLokeData:
    """Data for the integration."""

    client: Client
    coordinator: SalerydLokeDataUpdateCoordinator
    integration: Integration
    bridge: SalerydLokeBridge


type SalerydLokeConfigEntry = ConfigEntry[SalerydLokeData]
