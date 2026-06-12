"""Binary sensor exposing whether the sun is in this window's field of view.

Mirrors the ``in_field_of_view`` attribute of the Status sensor as a standalone
on/off entity, so history shows exactly when the geometry considered the sun
relevant. On means the sun is within the configured field of view AND above the
minimum elevation (the same gate the positioning maths uses).
"""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import AdaptiveCoverCoordinator
from .entity import AdaptiveCoverEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sun-in-view binary sensor."""
    coordinator: AdaptiveCoverCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AdaptiveCoverSunInViewSensor(coordinator)])


class AdaptiveCoverSunInViewSensor(AdaptiveCoverEntity, BinarySensorEntity):
    """On while the sun is inside the window's field of view."""

    _attr_name = "Sun in view"
    _attr_icon = "mdi:sun-angle"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: AdaptiveCoverCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._entry.entry_id}_sun_in_view"

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        return data.in_fov if data is not None else None
