"""Pure sun-to-cover geometry for Adaptive Cover (Model A: floor penetration).

This module has **no Home Assistant imports** on purpose: it is plain
trigonometry, so it can be unit-tested in isolation and reasoned about without
booting HA. Everything on the public surface is in degrees and percent; radians
only live inside the functions.

Model A in one line:

    position% = clamp( glare_distance · tan(profile_angle) / window_height )

where ``profile_angle`` is the sun's elevation projected onto the plane
perpendicular to the window. 100% = fully open, 0% = fully closed.

Intuition the maths encodes:
  * Sun **high** in the sky → steep rays that barely reach into the room →
    the cover can stay **more open**.
  * Sun **low** (early/late) → shallow rays that crawl far across the floor →
    the cover **closes** to hold the glare back.
  * **Larger** ``glare_distance`` (you allow sun to reach further in) → the
    cover stays **more open**.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import NamedTuple

# Sensible, plain-language defaults. These are approximations, not survey data —
# the help text in the config flow says as much.
DEFAULT_WINDOW_HEIGHT = 2.1  # metres, top of glass above the floor
DEFAULT_GLARE_DISTANCE = 0.5  # metres of floor the sun may reach before shading
DEFAULT_FOV = 90.0  # degrees either side of the window normal
DEFAULT_MIN_ELEVATION = 5.0  # degrees; ignore the sun below this
OPEN = 100
CLOSED = 0


class CoverDecision(NamedTuple):
    """The outcome of a single positioning calculation."""

    position: int  # 0-100, where 100 is fully open
    reason: str  # human-readable explanation, e.g. "shading 45% (γ=22°)"
    profile_angle: float | None  # degrees, or None when geometry did not run
    in_fov: bool  # whether the sun was within the window's field of view


@dataclass(frozen=True)
class SunSample:
    """A single point on the sun's track for the preview calculation.

    ``time`` is opaque to this module (a ``datetime`` in practice) so the
    geometry stays free of timezone concerns.
    """

    time: object
    azimuth: float
    elevation: float


class SunWindowInterval(NamedTuple):
    """When direct sun is expected to fall on a window today."""

    entry: object | None
    exit: object | None
    peak: object | None


def _clamp(value: float, low: float, high: float) -> int:
    return round(max(low, min(high, value)))


def _relative_azimuth(sun_azimuth: float, window_azimuth: float) -> float:
    """Signed difference (sun − window) folded into [-180, 180] degrees."""
    return ((sun_azimuth - window_azimuth + 180) % 360) - 180


def angle_in_fov(
    sun_azimuth: float,
    window_azimuth: float,
    fov_left: float = DEFAULT_FOV,
    fov_right: float = DEFAULT_FOV,
) -> bool:
    """Return whether the sun's azimuth lies within the window's field of view.

    Handles wrap-around at 360° (e.g. a north-facing window spanning 315°-45°).
    """
    low = (window_azimuth - fov_left) % 360
    high = (window_azimuth + fov_right) % 360
    az = sun_azimuth % 360
    if low <= high:
        return low <= az <= high
    return az >= low or az <= high


def profile_angle(
    sun_elevation: float,
    sun_azimuth: float,
    window_azimuth: float,
) -> float:
    """Vertical shadow (profile) angle γ in degrees.

    ``γ = atan( tan(elevation) / cos(sun_azimuth − window_azimuth) )``

    When the sun sits on the window's normal the result equals the elevation;
    as the sun moves off-axis the projected angle grows. Off-axis beyond ~90°
    the sun is behind the wall plane and there is no meaningful angle — callers
    gate this with :func:`angle_in_fov`, but we still guard the division.
    """
    rel = math.radians(_relative_azimuth(sun_azimuth, window_azimuth))
    cos_rel = math.cos(rel)
    if cos_rel <= 1e-6:
        return 90.0
    return math.degrees(math.atan(math.tan(math.radians(sun_elevation)) / cos_rel))


def calculate_position(
    sun_elevation: float,
    sun_azimuth: float,
    window_azimuth: float,
    *,
    window_height: float = DEFAULT_WINDOW_HEIGHT,
    glare_distance: float = DEFAULT_GLARE_DISTANCE,
    fov_left: float = DEFAULT_FOV,
    fov_right: float = DEFAULT_FOV,
    min_elevation: float = DEFAULT_MIN_ELEVATION,
    min_position: int = CLOSED,
    max_position: int = OPEN,
    position_after_sunset: int = OPEN,
) -> CoverDecision:
    """Compute the target cover position and a human-readable reason.

    Returns a :class:`CoverDecision`. 100 = fully open, 0 = fully closed.
    """
    if sun_elevation <= 0:
        return CoverDecision(
            _clamp(position_after_sunset, min_position, max_position),
            "after sunset",
            None,
            False,
        )

    if sun_elevation < min_elevation:
        return CoverDecision(
            _clamp(max_position, min_position, max_position),
            f"open — sun below {min_elevation:g}°",
            None,
            False,
        )

    in_fov = angle_in_fov(sun_azimuth, window_azimuth, fov_left, fov_right)
    if not in_fov:
        return CoverDecision(
            _clamp(max_position, min_position, max_position),
            "open — not in field of view",
            None,
            False,
        )

    gamma = profile_angle(sun_elevation, sun_azimuth, window_azimuth)
    fraction = glare_distance * math.tan(math.radians(gamma)) / window_height
    position = _clamp(fraction * 100, min_position, max_position)

    if position <= min_position:
        reason = f"shading — clamped to min {min_position}% (γ={gamma:.0f}°)"
    elif position >= max_position:
        reason = f"open — sun high (γ={gamma:.0f}°)"
    else:
        reason = f"shading {position}% (γ={gamma:.0f}°, glare {glare_distance:g}m)"

    return CoverDecision(position, reason, gamma, True)


def sun_window_interval(
    samples: list[SunSample],
    window_azimuth: float,
    fov_left: float = DEFAULT_FOV,
    fov_right: float = DEFAULT_FOV,
    min_elevation: float = DEFAULT_MIN_ELEVATION,
) -> SunWindowInterval:
    """Find when direct sun falls on the window today, for setup verification.

    Given chronological sun ``samples`` (azimuth/elevation over the day, e.g.
    sampled every 10 minutes from HA's location), return the entry, exit, and
    peak (highest-elevation) times of the contiguous span where the sun is both
    above ``min_elevation`` and within the window's field of view. Returns all
    ``None`` when the sun never enters — a strong hint the azimuth is wrong.
    """
    in_view = [
        s
        for s in samples
        if s.elevation >= min_elevation
        and angle_in_fov(s.azimuth, window_azimuth, fov_left, fov_right)
    ]
    if not in_view:
        return SunWindowInterval(None, None, None)
    peak = max(in_view, key=lambda s: s.elevation)
    return SunWindowInterval(in_view[0].time, in_view[-1].time, peak.time)


def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial true-north bearing in degrees (0-360) from point 1 to point 2.

    Used by the config flow's map helper: drop a pin inside the room (point 1)
    and one outside through the window (point 2); the bearing from inside to
    outside is the window's azimuth, in true north (no magnetic declination to
    correct, unlike a phone compass).
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    y = math.sin(dlon) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(
        dlon
    )
    return (math.degrees(math.atan2(y, x)) + 360) % 360
