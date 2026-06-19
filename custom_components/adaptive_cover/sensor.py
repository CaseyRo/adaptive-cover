"""The reason sensor plus standalone diagnostic output sensors.

The Status sensor's state is the recommended position and its attributes are
the why. It updates on every recompute whether or not the master switch is on,
so the recommended position (and its explanation, plus today's sun-entry
preview) can be observed and trusted before active control is enabled.

The diagnostic sensors promote each explanatory value (profile angle, sun
position, sky signal, preview times) to its own entity so the "how the magic
worked" is graphable in history — attributes are recorded but cannot be
plotted. They are pure readers over the same coordinator data; rows come from
``DIAGNOSTIC_SENSORS`` in ``const.py`` (mirroring the output-sensor table in
the CDiT Adaptive Lighting fork).
"""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_BRIGHTNESS_SENSOR,
    CONF_WEATHER_ENTITY,
    DIAGNOSTIC_SENSORS,
    DOMAIN,
)
from .coordinator import AdaptiveCoverCoordinator
from .entity import AdaptiveCoverEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the reason sensor and the diagnostic output sensors."""
    coordinator: AdaptiveCoverCoordinator = hass.data[DOMAIN][entry.entry_id]
    opts = coordinator.options
    entities: list[SensorEntity] = [AdaptiveCoverSensor(coordinator)]
    for row in DIAGNOSTIC_SENSORS:
        conditional = row.get("conditional")
        if conditional and not opts.get(conditional):
            continue
        conditional_any = row.get("conditional_any")
        if conditional_any and not any(opts.get(key) for key in conditional_any):
            continue
        entities.append(AdaptiveCoverDiagnosticSensor(coordinator, row))
    async_add_entities(entities)


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


class AdaptiveCoverDiagnosticSensor(AdaptiveCoverEntity, SensorEntity):
    """One read-only value from the coordinator's last recompute.

    Reports ``unknown`` (None) whenever the underlying value was not computed —
    e.g. the profile angle after sunset, or a sky row that is not the active
    signal. Stale numbers would lie about how the decision was made. Most rows
    are diagnostic telemetry; ``primary`` rows (Sun strength — the axis the
    cover acts on) are surfaced as normal sensors instead.
    """

    def __init__(
        self, coordinator: AdaptiveCoverCoordinator, description: dict
    ) -> None:
        super().__init__(coordinator)
        self._row = description
        if not description.get("primary"):
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_unique_id = f"{self._entry.entry_id}_{description['key']}"
        self._attr_name = description["name"]
        self._attr_icon = description["icon"]
        if description.get("device_class") == "timestamp":
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
        else:
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_suggested_display_precision = 1
            self._attr_native_unit_of_measurement = self._resolve_unit(description)

    def _resolve_unit(self, description: dict) -> str | None:
        """Resolve the unit once at setup so it never changes at runtime.

        The Sun strength row inherits the brightness source's own unit (lux or
        W/m² — the gate is unit-agnostic); with only the weather fallback it is
        the 0-100 clearness percentage. Falls back to the table default.
        """
        unit = description.get("unit")
        if description.get("key") != "sun_strength":
            return unit
        opts = self.coordinator.options
        source = opts.get(CONF_BRIGHTNESS_SENSOR)
        state = self.coordinator.hass.states.get(source) if source else None
        if state is not None:
            return state.attributes.get("unit_of_measurement") or unit
        if opts.get(CONF_WEATHER_ENTITY):
            return PERCENTAGE
        return unit

    @property
    def native_value(self):
        data = self.coordinator.data
        if data is None:
            return None
        sky_kind = self._row.get("sky_kind")
        if sky_kind is not None and data.sky_kind != sky_kind:
            return None
        return getattr(data, self._row["attr"])
