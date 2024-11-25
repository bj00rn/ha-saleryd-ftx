"""Custom types for integration"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pysaleryd.client import Client

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .coordinator import SalerydLokeDataUpdateCoordinator


type SalerydLokeConfigEntry = ConfigEntry[SalerydLokeData]


@dataclass
class SalerydLokeData:
    """Data for the integration."""

    client: Client
    coordinator: SalerydLokeDataUpdateCoordinator
    integration: Integration
