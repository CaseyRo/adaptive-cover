"""Config + options flow for Adaptive Cover (CDiT).

Mirrors the adaptive_lighting shape: a single-field create step (name), then a
sectioned options flow that reloads the entry on save. The field set, defaults
and help text come from ``const.py`` so there is one source of truth.

Window azimuth: a numeric field plus a 16-point compass select for the
zero-friction default. (The "map pin + heading dial" exact helper from the
design needs a custom frontend element — stock selectors can't render a heading
dial — so it is deferred; numeric + compass is the v1 surface.)
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_AZIMUTH,
    CONF_BRIGHTNESS_SENSOR,
    CONF_COOLDOWN,
    CONF_COVERS,
    CONF_FOV_LEFT,
    CONF_FOV_RIGHT,
    CONF_GLARE_DISTANCE,
    CONF_INDOOR_LUX_CAP,
    CONF_INDOOR_LUX_SENSOR,
    CONF_INTERVAL,
    CONF_MANUAL_TIMEOUT,
    CONF_MANUAL_TOLERANCE,
    CONF_MAX_POSITION,
    CONF_MIN_DELTA,
    CONF_MIN_ELEVATION,
    CONF_MIN_POSITION,
    CONF_OPEN_BELOW,
    CONF_POSITION_AFTER_SUNSET,
    CONF_QUANTIZE_STEP,
    CONF_SHADE_ABOVE,
    CONF_WEATHER_ENTITY,
    CONF_WINDOW_HEIGHT,
    DEFAULTS,
    DOMAIN,
    SECTIONS,
)

CONF_FACING = "facing"
FACING_CUSTOM = "custom"

# 16-point compass → degrees (true north).
COMPASS: dict[str, int] = {
    "N": 0,
    "NNE": 23,
    "NE": 45,
    "ENE": 68,
    "E": 90,
    "ESE": 113,
    "SE": 135,
    "SSE": 158,
    "S": 180,
    "SSW": 203,
    "SW": 225,
    "WSW": 248,
    "W": 270,
    "WNW": 293,
    "NW": 315,
    "NNW": 338,
}

ENTITY_OPTIONAL = {CONF_BRIGHTNESS_SENSOR, CONF_WEATHER_ENTITY, CONF_INDOOR_LUX_SENSOR}

# key -> (min, max, step, unit)
NUMBER_RANGES: dict[str, tuple[float, float, float, str | None]] = {
    CONF_AZIMUTH: (0, 359, 1, "°"),
    CONF_WINDOW_HEIGHT: (0.1, 6, 0.1, "m"),
    CONF_GLARE_DISTANCE: (0.1, 3, 0.1, "m"),
    CONF_FOV_LEFT: (1, 90, 1, "°"),
    CONF_FOV_RIGHT: (1, 90, 1, "°"),
    CONF_MIN_ELEVATION: (0, 45, 1, "°"),
    CONF_POSITION_AFTER_SUNSET: (0, 100, 1, "%"),
    CONF_MIN_POSITION: (0, 100, 1, "%"),
    CONF_MAX_POSITION: (0, 100, 1, "%"),
    CONF_SHADE_ABOVE: (0, 100000, 1, None),
    CONF_OPEN_BELOW: (0, 100000, 1, None),
    CONF_INDOOR_LUX_CAP: (0, 100000, 10, "lx"),
    CONF_INTERVAL: (10, 3600, 5, "s"),
    CONF_QUANTIZE_STEP: (1, 50, 1, "%"),
    CONF_MIN_DELTA: (1, 50, 1, "%"),
    CONF_COOLDOWN: (0, 3600, 5, "s"),
    CONF_MANUAL_TOLERANCE: (0, 50, 1, "%"),
    CONF_MANUAL_TIMEOUT: (60, 86400, 60, "s"),
}


def _selector(key: str):
    if key == CONF_COVERS:
        return EntitySelector(EntitySelectorConfig(domain="cover", multiple=True))
    if key in (CONF_BRIGHTNESS_SENSOR, CONF_INDOOR_LUX_SENSOR):
        return EntitySelector(EntitySelectorConfig(domain="sensor"))
    if key == CONF_WEATHER_ENTITY:
        return EntitySelector(EntitySelectorConfig(domain="weather"))
    low, high, step, unit = NUMBER_RANGES[key]
    config = NumberSelectorConfig(
        min=low, max=high, step=step, mode=NumberSelectorMode.BOX
    )
    if unit is not None:
        config["unit_of_measurement"] = unit
    return NumberSelector(config)


def _marker(key: str, options: dict):
    current = options.get(key, DEFAULTS.get(key))
    if key in ENTITY_OPTIONAL and not current:
        return vol.Optional(key)
    if key == CONF_COVERS:
        return vol.Optional(key, default=current or [])
    return vol.Optional(key, default=current)


def _window_section(options: dict):
    facing_options = [*COMPASS.keys(), FACING_CUSTOM]
    inner = {
        _marker(CONF_COVERS, options): _selector(CONF_COVERS),
        vol.Optional(CONF_FACING, default=FACING_CUSTOM): SelectSelector(
            SelectSelectorConfig(
                options=facing_options,
                mode=SelectSelectorMode.DROPDOWN,
                translation_key=CONF_FACING,
            )
        ),
        _marker(CONF_AZIMUTH, options): _selector(CONF_AZIMUTH),
    }
    return section(vol.Schema(inner), {"collapsed": False})


def _options_schema(options: dict) -> vol.Schema:
    schema: dict = {}
    for name, keys in SECTIONS.items():
        if name == "window":
            schema[vol.Required(name)] = _window_section(options)
            continue
        inner = {_marker(key, options): _selector(key) for key in keys}
        schema[vol.Required(name)] = section(vol.Schema(inner), {"collapsed": True})
    return vol.Schema(schema)


def _flatten(user_input: dict[str, Any]) -> dict[str, Any]:
    """Collapse the sectioned form into flat options and resolve facing."""
    flat: dict[str, Any] = {}
    for value in user_input.values():
        if isinstance(value, dict):
            flat.update(value)
    facing = flat.pop(CONF_FACING, FACING_CUSTOM)
    if facing != FACING_CUSTOM and facing in COMPASS:
        flat[CONF_AZIMUTH] = COMPASS[facing]
    for key in ENTITY_OPTIONAL:
        flat.setdefault(key, "")
    return flat


class AdaptiveCoverConfigFlow(ConfigFlow, domain=DOMAIN):
    """Create a window from just a name."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data={})
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_NAME): str}),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowHandler:
        return OptionsFlowHandler()


class OptionsFlowHandler(OptionsFlowWithReload):
    """Sectioned options; saving reloads the entry so changes apply live."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=_flatten(user_input))
        options = {**DEFAULTS, **self.config_entry.options}
        return self.async_show_form(
            step_id="init", data_schema=_options_schema(options)
        )
