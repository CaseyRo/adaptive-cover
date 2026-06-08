"""The reason sensor: state is the recommended position, attributes are the why.

This updates on every recompute whether or not the master switch is on, so the
recommended position (and its explanation, plus today's sun-entry preview) can
be observed and trusted before active control is enabled.
"""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
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
    """Set up the reason sensor."""
    coordinator: AdaptiveCoverCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AdaptiveCoverSensor(coordinator)])


def _iso(value) -> str | None:
    return value.isoformat() if value is not None else None


class AdaptiveCoverSensor(AdaptiveCoverEntity, SensorEntity):
    """Publishes the recommended position and a readable reason."""

    _attr_name = "Status"
    _attr_icon = "mdi:blinds"
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator: AdaptiveCoverCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._entry.entry_id}_status"

    @property
    def native_value(self) -> int | None:
        data = self.coordinator.data
        return data.position if data is not None else None

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data
        if data is None:
            return {}
        switch = getattr(self.coordinator, "switch", None)
        manual = switch.manual_covers if switch is not None else []
        return {
            "reason": data.reason,
            "profile_angle": (
                round(data.profile_angle, 1) if data.profile_angle is not None else None
            ),
            "sun_azimuth": (
                round(data.sun_azimuth, 1) if data.sun_azimuth is not None else None
            ),
            "sun_elevation": (
                round(data.sun_elevation, 1) if data.sun_elevation is not None else None
            ),
            "in_field_of_view": data.in_fov,
            "sky_signal": data.sky_kind,
            "sky_value": data.sky_value,
            "manual_override": bool(manual),
            "manually_controlled": manual,
            "sun_enters": _iso(data.preview_entry),
            "sun_leaves": _iso(data.preview_exit),
            "sun_peak": _iso(data.preview_peak),
        }
