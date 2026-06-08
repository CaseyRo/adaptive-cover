"""Recompute loop for Adaptive Cover.

Reads sun position (from ``sun.sun``) and the optional sky signal, runs the pure
geometry + sky logic, and publishes an :class:`AdaptiveCoverData` for the
entities. The coordinator only *computes the recommendation* — actually moving
covers (and respecting manual control) is the switch's job, so the recommended
position and reason are available even when active control is off.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from . import geometry
from .const import (
    CONF_AZIMUTH,
    CONF_BRIGHTNESS_SENSOR,
    CONF_FOV_LEFT,
    CONF_FOV_RIGHT,
    CONF_GLARE_DISTANCE,
    CONF_INDOOR_LUX_CAP,
    CONF_INDOOR_LUX_SENSOR,
    CONF_INTERVAL,
    CONF_MAX_POSITION,
    CONF_MIN_ELEVATION,
    CONF_MIN_POSITION,
    CONF_OPEN_BELOW,
    CONF_POSITION_AFTER_SUNSET,
    CONF_SHADE_ABOVE,
    CONF_WEATHER_ENTITY,
    CONF_WINDOW_HEIGHT,
    DEFAULTS,
    DOMAIN,
    SKY_BRIGHTNESS,
    SKY_CLOUD,
    SUN_ENTITY,
)
from .sky import SkyGate, apply_governor

_LOGGER = logging.getLogger(__name__)

PREVIEW_STEP_MINUTES = 10


@dataclass
class AdaptiveCoverData:
    """Everything the entities need, including the 'why'."""

    position: int
    reason: str
    profile_angle: float | None
    in_fov: bool
    sun_azimuth: float | None
    sun_elevation: float | None
    sky_kind: str | None
    sky_value: float | None
    allow_shading: bool
    preview_entry: datetime | None = None
    preview_exit: datetime | None = None
    preview_peak: datetime | None = None


class AdaptiveCoverCoordinator(DataUpdateCoordinator[AdaptiveCoverData]):
    """Computes the recommended cover position on a fixed interval."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        opts = {**DEFAULTS, **entry.options}
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {entry.title}",
            update_interval=timedelta(seconds=int(opts[CONF_INTERVAL])),
        )
        self._gate = SkyGate(
            float(opts[CONF_SHADE_ABOVE]), float(opts[CONF_OPEN_BELOW])
        )
        self._preview_cache_date: object | None = None
        self._preview = geometry.SunWindowInterval(None, None, None)
        # Set by the switch entity so the sensor can surface manual state.
        self.switch = None

    @property
    def options(self) -> dict:
        """Merged defaults + entry options."""
        return {**DEFAULTS, **self.entry.options}

    def set_threshold(self, key: str, value: float) -> None:
        """Live-update one sky threshold from its number entity."""
        if key == CONF_SHADE_ABOVE:
            self._gate.shade_above = value
        elif key == CONF_OPEN_BELOW:
            self._gate.open_below = value

    # --- helpers -----------------------------------------------------------

    def _num_state(self, entity_id: str | None) -> float | None:
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable", ""):
            return None
        try:
            return float(state.state)
        except (TypeError, ValueError):
            return None

    def _read_sky(self, opts: dict) -> tuple[str | None, float | None]:
        """Resolve the sky signal: brightness sensor first, then cloud cover."""
        brightness = self._num_state(opts.get(CONF_BRIGHTNESS_SENSOR))
        if brightness is not None:
            return SKY_BRIGHTNESS, brightness
        weather = opts.get(CONF_WEATHER_ENTITY)
        if weather:
            state = self.hass.states.get(weather)
            if state is not None:
                cloud = state.attributes.get("cloud_coverage")
                try:
                    if cloud is not None:
                        return SKY_CLOUD, float(cloud)
                except (TypeError, ValueError):
                    pass
        return None, None

    def _compute_preview(self, opts: dict) -> geometry.SunWindowInterval:
        """Best-effort 'sun enters ~HH:MM' preview, cached per day."""
        now = dt_util.now()
        today = now.date()
        if self._preview_cache_date == today:
            return self._preview
        try:
            from astral import Observer
            from astral.sun import azimuth as _azimuth
            from astral.sun import elevation as _elevation

            observer = Observer(
                self.hass.config.latitude,
                self.hass.config.longitude,
                self.hass.config.elevation,
            )
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            samples: list[geometry.SunSample] = []
            steps = (24 * 60) // PREVIEW_STEP_MINUTES
            for i in range(steps + 1):
                t = start + timedelta(minutes=PREVIEW_STEP_MINUTES * i)
                samples.append(
                    geometry.SunSample(
                        time=t,
                        azimuth=_azimuth(observer, t),
                        elevation=_elevation(observer, t),
                    )
                )
            self._preview = geometry.sun_window_interval(
                samples,
                float(opts[CONF_AZIMUTH]),
                float(opts[CONF_FOV_LEFT]),
                float(opts[CONF_FOV_RIGHT]),
                float(opts[CONF_MIN_ELEVATION]),
            )
            self._preview_cache_date = today
        except Exception as err:  # noqa: BLE001 - preview is best-effort
            _LOGGER.debug("Preview computation skipped: %s", err)
            self._preview = geometry.SunWindowInterval(None, None, None)
        return self._preview

    # --- main loop ---------------------------------------------------------

    async def _async_update_data(self) -> AdaptiveCoverData:
        opts = self.options
        sun = self.hass.states.get(SUN_ENTITY)
        if sun is None:
            raise UpdateFailed("sun.sun is not available")
        try:
            azimuth = float(sun.attributes["azimuth"])
            elevation = float(sun.attributes["elevation"])
        except (KeyError, TypeError, ValueError) as err:
            raise UpdateFailed(f"sun.sun missing azimuth/elevation: {err}") from err

        decision = geometry.calculate_position(
            elevation,
            azimuth,
            float(opts[CONF_AZIMUTH]),
            window_height=float(opts[CONF_WINDOW_HEIGHT]),
            glare_distance=float(opts[CONF_GLARE_DISTANCE]),
            fov_left=float(opts[CONF_FOV_LEFT]),
            fov_right=float(opts[CONF_FOV_RIGHT]),
            min_elevation=float(opts[CONF_MIN_ELEVATION]),
            min_position=int(opts[CONF_MIN_POSITION]),
            max_position=int(opts[CONF_MAX_POSITION]),
            position_after_sunset=int(opts[CONF_POSITION_AFTER_SUNSET]),
        )

        position = decision.position
        reason = decision.reason
        sky_kind: str | None = None
        sky_value: float | None = None
        allow = True
        max_pos = int(opts[CONF_MAX_POSITION])

        wants_to_shade = decision.in_fov and position < max_pos
        if wants_to_shade:
            sky_kind, sky_value = self._read_sky(opts)
            if sky_kind is not None and sky_value is not None:
                allow, fragment = self._gate.evaluate(sky_value, sky_kind)
                if not allow:
                    position = max_pos
                    reason = f"open — {fragment}"
                else:
                    reason = f"{decision.reason}; {fragment}"
            if allow:
                room_lux = self._num_state(opts.get(CONF_INDOOR_LUX_SENSOR))
                position, gov = apply_governor(
                    position,
                    room_lux=room_lux,
                    cap=float(opts[CONF_INDOOR_LUX_CAP]),
                    is_day=elevation > 0,
                    min_position=int(opts[CONF_MIN_POSITION]),
                )
                if gov:
                    reason = f"{reason}; {gov}"

        preview = self._compute_preview(opts)

        _LOGGER.debug("%s: position=%s, reason=%s", self.name, position, reason)
        return AdaptiveCoverData(
            position=position,
            reason=reason,
            profile_angle=decision.profile_angle,
            in_fov=decision.in_fov,
            sun_azimuth=azimuth,
            sun_elevation=elevation,
            sky_kind=sky_kind,
            sky_value=sky_value,
            allow_shading=allow,
            preview_entry=preview.entry,
            preview_exit=preview.exit,
            preview_peak=preview.peak,
        )
