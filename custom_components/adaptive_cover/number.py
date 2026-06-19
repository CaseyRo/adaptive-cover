"""The live-tunable values exposed as number entities.

Per the design decision, the values you tune *while watching the cover* are
sliders on a dashboard, not a trip back through the options flow:

* the two sky thresholds (shade-above / open-below), pushed into the stateful
  sky gate, and
* the left/right field-of-view spans — narrow one side when a neighbouring
  structure blocks that arc — pushed into the coordinator's live-override map.

All restore across restarts (falling back to the configured option, then the
default) and take effect on the next recompute.
"""

from __future__ import annotations

from homeassistant.components.number import NumberMode, RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_FOV_LEFT,
    CONF_FOV_RIGHT,
    CONF_OPEN_BELOW,
    CONF_SHADE_ABOVE,
    DOMAIN,
)
from .coordinator import AdaptiveCoverCoordinator
from .entity import AdaptiveCoverEntity

# Generous upper bound so the same threshold entity works for clearness% and raw
# lux alike (unit-agnostic: you set it in the active sensor's own scale).
MAX_THRESHOLD = 200000.0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the live-tunable threshold and field-of-view numbers."""
    coordinator: AdaptiveCoverCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            AdaptiveCoverThreshold(
                coordinator, CONF_SHADE_ABOVE, "Sun strength — shade above"
            ),
            AdaptiveCoverThreshold(
                coordinator, CONF_OPEN_BELOW, "Sun strength — open below"
            ),
            AdaptiveCoverFov(coordinator, CONF_FOV_LEFT, "Field of view — left"),
            AdaptiveCoverFov(coordinator, CONF_FOV_RIGHT, "Field of view — right"),
        ]
    )


class AdaptiveCoverLiveNumber(AdaptiveCoverEntity, RestoreNumber):
    """A live-tunable value: restores across restarts, pushed into the coordinator.

    On first run a control seeds from its configured option; thereafter it
    restores its last value. Subclasses say where the value goes via ``_push``.
    """

    _attr_mode = NumberMode.BOX

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
        self._push(self._attr_native_value)

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self._push(value)
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    def _push(self, value: float) -> None:
        raise NotImplementedError


class AdaptiveCoverThreshold(AdaptiveCoverLiveNumber):
    """A live sky threshold pushed into the coordinator's stateful gate."""

    _attr_native_min_value = 0.0
    _attr_native_max_value = MAX_THRESHOLD
    _attr_native_step = 1.0
    _attr_icon = "mdi:weather-partly-cloudy"

    def _push(self, value: float) -> None:
        self.coordinator.set_threshold(self._key, value)


class AdaptiveCoverFov(AdaptiveCoverLiveNumber):
    """A live field-of-view span pushed into the coordinator's override map."""

    _attr_native_min_value = 0.0
    _attr_native_max_value = 90.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "°"
    _attr_icon = "mdi:angle-acute"

    def _push(self, value: float) -> None:
        self.coordinator.set_override(self._key, value)
