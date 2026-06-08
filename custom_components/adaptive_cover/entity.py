"""Shared base entity: groups every entity for a window under one device."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AdaptiveCoverCoordinator


class AdaptiveCoverEntity(CoordinatorEntity[AdaptiveCoverCoordinator]):
    """Base class wiring device info from the config entry."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AdaptiveCoverCoordinator) -> None:
        super().__init__(coordinator)
        entry = coordinator.entry
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="CDiT",
            model="Adaptive Cover",
        )
