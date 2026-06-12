"""Constants, defaults, help text and section layout for Adaptive Cover (CDiT).

This is the single source of truth for the configuration surface. ``config_flow``
builds its sectioned options form from :data:`SECTIONS` + :data:`DEFAULTS`, and
renders the per-field help text from :data:`DOCS`. Keep new options here.
"""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "adaptive_cover"

# --- config-entry keys -----------------------------------------------------

# Window (the only fields that need human judgement)
CONF_NAME: Final = "name"
CONF_COVERS: Final = "covers"
CONF_AZIMUTH: Final = "azimuth"

# Geometry (approximate; great help text matters more than precision)
CONF_WINDOW_HEIGHT: Final = "window_height"
CONF_GLARE_DISTANCE: Final = "glare_distance"

# Sun
CONF_FOV_LEFT: Final = "fov_left"
CONF_FOV_RIGHT: Final = "fov_right"
CONF_MIN_ELEVATION: Final = "min_elevation"
CONF_POSITION_AFTER_SUNSET: Final = "position_after_sunset"
CONF_MIN_POSITION: Final = "min_position"
CONF_MAX_POSITION: Final = "max_position"

# Sky gating
CONF_BRIGHTNESS_SENSOR: Final = "brightness_sensor"
CONF_WEATHER_ENTITY: Final = "weather_entity"
CONF_SHADE_ABOVE: Final = "shade_above"
CONF_OPEN_BELOW: Final = "open_below"
CONF_INDOOR_LUX_SENSOR: Final = "indoor_lux_sensor"
CONF_INDOOR_LUX_CAP: Final = "indoor_lux_cap"

# Movement settings — the anti-hum throttle
CONF_INTERVAL: Final = "interval"
CONF_QUANTIZE_STEP: Final = "quantize_step"
CONF_MIN_DELTA: Final = "min_delta"
CONF_COOLDOWN: Final = "cooldown"

# Manual override (WAF)
CONF_MANUAL_TOLERANCE: Final = "manual_tolerance"
CONF_MANUAL_TIMEOUT: Final = "manual_timeout"

# --- defaults --------------------------------------------------------------

DEFAULTS: Final[dict[str, object]] = {
    CONF_COVERS: [],
    CONF_AZIMUTH: 180,
    CONF_WINDOW_HEIGHT: 2.1,
    CONF_GLARE_DISTANCE: 0.5,
    CONF_FOV_LEFT: 90,
    CONF_FOV_RIGHT: 90,
    CONF_MIN_ELEVATION: 5,
    CONF_POSITION_AFTER_SUNSET: 100,
    CONF_MIN_POSITION: 0,
    CONF_MAX_POSITION: 100,
    CONF_BRIGHTNESS_SENSOR: "",
    CONF_WEATHER_ENTITY: "",
    # Defaults are in "clearness" terms for the cloud fallback most people use:
    # clearness = 100 - cloud%. shade when clearness >= 60 (cloud <= 40),
    # open when clearness <= 30 (cloud >= 70). With a lux/irradiance sensor you
    # set these in the sensor's own scale instead (unit-agnostic).
    CONF_SHADE_ABOVE: 60,
    CONF_OPEN_BELOW: 30,
    CONF_INDOOR_LUX_SENSOR: "",
    CONF_INDOOR_LUX_CAP: 0,  # 0 = governor disabled
    CONF_INTERVAL: 120,
    CONF_QUANTIZE_STEP: 5,
    CONF_MIN_DELTA: 5,
    CONF_COOLDOWN: 120,
    CONF_MANUAL_TOLERANCE: 5,
    CONF_MANUAL_TIMEOUT: 7200,
}

# --- help text (rendered in the options flow) ------------------------------

DOCS: Final[dict[str, str]] = {
    CONF_COVERS: "The cover(s) this window controls. Multiple covers move together.",
    CONF_AZIMUTH: (
        "Which way the glass faces, in degrees (0=N, 90=E, 180=S, 270=W). "
        "An approximation is fine — pick the nearest compass point."
    ),
    CONF_WINDOW_HEIGHT: (
        "Roughly how high the top of the glass is above the floor, in metres. "
        "You're eyeballing it, not measuring."
    ),
    CONF_GLARE_DISTANCE: (
        "How far across the floor direct sun may reach before the blind shades "
        "it, in metres. Smaller = darker/cooler room; larger = more sun and view."
    ),
    CONF_FOV_LEFT: "Degrees to the left of centre the window still 'sees' the sun.",
    CONF_FOV_RIGHT: "Degrees to the right of centre the window still 'sees' the sun.",
    CONF_MIN_ELEVATION: "Ignore the sun below this elevation (degrees).",
    CONF_POSITION_AFTER_SUNSET: "Where to leave the cover once the sun is down (0-100).",
    CONF_MIN_POSITION: "Never close past this position (0-100).",
    CONF_MAX_POSITION: "Never open past this position (0-100).",
    CONF_BRIGHTNESS_SENSOR: (
        "Optional outdoor light/irradiance sensor (lux or W/m²). Preferred over "
        "cloud cover — shades only when it's actually bright."
    ),
    CONF_WEATHER_ENTITY: (
        "Optional weather entity; its cloud-cover % is used only when no "
        "brightness sensor is set."
    ),
    CONF_SHADE_ABOVE: (
        "Shade when clearness rises to/above this (in the active signal's own "
        "scale — lux/irradiance, or clearness%=100-cloud for the weather fallback)."
    ),
    CONF_OPEN_BELOW: (
        "Open back up when clearness falls to/below this. Keep it below 'shade "
        "above' — the gap is a dead-band so passing clouds can't make the blind flap."
    ),
    CONF_INDOOR_LUX_SENSOR: (
        "Optional room light sensor. Acts as a gentle comfort governor (closes a "
        "little more if the room is too bright). Leave empty to disable."
    ),
    CONF_INDOOR_LUX_CAP: "Room brightness above which to trim more closed (0 = off).",
    CONF_INTERVAL: "How often to recompute and (if enabled) move, in seconds.",
    CONF_QUANTIZE_STEP: "Snap target positions to this step, in percent (anti-hum).",
    CONF_MIN_DELTA: "Don't move for changes smaller than this, in percent (anti-hum).",
    CONF_COOLDOWN: "Minimum time between commanded moves, in seconds (anti-hum).",
    CONF_MANUAL_TOLERANCE: (
        "How far a settled cover may differ from our last command before it's "
        "treated as manually moved, in percent."
    ),
    CONF_MANUAL_TIMEOUT: (
        "After a manual move, resume automatic control after this many seconds "
        "(also resets at sunrise)."
    ),
}

# --- options-flow section layout -------------------------------------------

SECTIONS: Final[dict[str, list[str]]] = {
    "window": [CONF_COVERS, CONF_AZIMUTH],
    "geometry": [CONF_WINDOW_HEIGHT, CONF_GLARE_DISTANCE],
    "sun": [
        CONF_FOV_LEFT,
        CONF_FOV_RIGHT,
        CONF_MIN_ELEVATION,
        CONF_POSITION_AFTER_SUNSET,
        CONF_MIN_POSITION,
        CONF_MAX_POSITION,
    ],
    "sky": [
        CONF_BRIGHTNESS_SENSOR,
        CONF_WEATHER_ENTITY,
        CONF_SHADE_ABOVE,
        CONF_OPEN_BELOW,
        CONF_INDOOR_LUX_SENSOR,
        CONF_INDOOR_LUX_CAP,
    ],
    "movement": [CONF_INTERVAL, CONF_QUANTIZE_STEP, CONF_MIN_DELTA, CONF_COOLDOWN],
    "manual": [CONF_MANUAL_TOLERANCE, CONF_MANUAL_TIMEOUT],
}

# Sun integration entity we read azimuth/elevation from.
SUN_ENTITY: Final = "sun.sun"

# Services
SERVICE_RESET_MANUAL: Final = "reset_manual_control"
SERVICE_APPLY_NOW: Final = "apply_now"

# Signal kinds for the sky gate
SKY_BRIGHTNESS: Final = "brightness"
SKY_CLOUD: Final = "cloud"

# --- diagnostic output sensors ----------------------------------------------
# One row per standalone diagnostic sensor (mirrors the OUTPUT_SENSORS table in
# the CDiT Adaptive Lighting fork). ``attr`` names the AdaptiveCoverData field
# to read. Rows with ``conditional`` are only created when that config option
# is set; rows with ``sky_kind`` report unknown unless it is the active signal.
# ``device_class: "timestamp"`` rows publish datetimes; all others are numeric
# measurements. Kept HA-import-free on purpose — sensor.py maps the strings.
DIAGNOSTIC_SENSORS: Final[list[dict[str, object]]] = [
    {
        "key": "profile_angle",
        "name": "Profile angle",
        "unit": "°",
        "icon": "mdi:angle-acute",
        "attr": "profile_angle",
    },
    {
        "key": "sun_azimuth",
        "name": "Sun azimuth",
        "unit": "°",
        "icon": "mdi:sun-compass",
        "attr": "sun_azimuth",
    },
    {
        "key": "sun_elevation",
        "name": "Sun elevation",
        "unit": "°",
        "icon": "mdi:weather-sunset",
        "attr": "sun_elevation",
    },
    {
        "key": "sky_brightness",
        "name": "Sky brightness",
        # Fallback unit; replaced at setup with the source sensor's own unit
        # (lux or W/m²) so history statistics stay consistent with the source.
        "unit": "lx",
        "icon": "mdi:brightness-5",
        "attr": "sky_value",
        "sky_kind": SKY_BRIGHTNESS,
        "conditional": CONF_BRIGHTNESS_SENSOR,
    },
    {
        "key": "cloud_cover",
        "name": "Cloud cover",
        "unit": "%",
        "icon": "mdi:weather-partly-cloudy",
        "attr": "sky_value",
        "sky_kind": SKY_CLOUD,
        "conditional": CONF_WEATHER_ENTITY,
    },
    {
        "key": "sun_enters",
        "name": "Sun enters",
        "icon": "mdi:weather-sunset-up",
        "attr": "preview_entry",
        "device_class": "timestamp",
    },
    {
        "key": "sun_leaves",
        "name": "Sun leaves",
        "icon": "mdi:weather-sunset-down",
        "attr": "preview_exit",
        "device_class": "timestamp",
    },
    {
        "key": "sun_peak",
        "name": "Sun peak",
        "icon": "mdi:weather-sunny",
        "attr": "preview_peak",
        "device_class": "timestamp",
    },
]
