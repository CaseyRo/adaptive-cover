"""The two live-tunable sky thresholds.

Per the design decision, these are the *only* settings exposed as number
entities — the genuinely subjective "tune while watching" values. Calibrating
the cloud/brightness response is a slider you drag on a dashboard, not a trip
back through the options flow. Values restore across restarts and take effect on
the next recompute.
"""

from __future__ import annotations

from homeassistant.components.number import NumberMode, RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_OPEN_BELOW,
    CONF_SHADE_ABOVE,
    DOMAIN,
)
from .coordinator import AdaptiveCoverCoordinator
from .entity import AdaptiveCoverEntity

# Generous upper bound so the same entity works for clearness% and raw lux alike
# (unit-agnostic: you set it in the active sensor's own scale).
MAX_THRESHOLD = 200000.0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the shade/open threshold numbers."""
    coordinator: AdaptiveCoverCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            AdaptiveCoverThreshold(coordinator, CONF_SHADE_ABOVE, "Shade above"),
            AdaptiveCoverThreshold(coordinator, CONF_OPEN_BELOW, "Open below"),
        ]
    )


class AdaptiveCoverThreshold(AdaptiveCoverEntity, RestoreNumber):
    """A single live-tunable sky threshold pushed into the coordinator's gate."""

    _attr_native_min_value = 0.0
    _attr_native_max_value = MAX_THRESHOLD
    _attr_native_step = 1.0
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:weather-partly-cloudy"

    def __init__(
        self, coordinator: AdaptiveCoverCoordinator, key: str, name: str
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{self._entry.entry_id}_{key}"
        self._attr_native_value = float(coordinator.options[key])

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_number_data()
        if last is not None and last.native_value is not None:
            self._attr_native_value = last.native_value
        self.coordinator.set_threshold(self._key, self._attr_native_value)

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.coordinator.set_threshold(self._key, value)
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
