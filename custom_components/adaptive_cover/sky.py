"""Sky gating for Adaptive Cover: decide *whether* shading is warranted.

Pure logic, no Home Assistant imports — the coordinator feeds it values read
from HA. Two ideas live here:

* **Hysteresis gate** — works on "clearness". For a brightness sensor,
  clearness is just the value (higher = brighter/clearer). For the weather
  cloud-cover fallback, clearness = 100 - cloud%. A single pair of thresholds
  (``shade_above`` / ``open_below``) then applies in one direction with a
  dead-band between them, so a signal hovering near a value — or a cloud
  drifting past — cannot make slow, loud covers flap.
* **Indoor-lux governor** — an optional, bounded comfort trim (see
  :func:`apply_governor`).
"""

from __future__ import annotations

from .const import SKY_CLOUD

GOVERNOR_STEP = 15  # percent; at most one of these per cycle


def clearness(value: float, kind: str) -> float:
    """Map a raw sky signal to 'clearness' (higher = more direct sun)."""
    if kind == SKY_CLOUD:
        return 100.0 - value
    return value


class SkyGate:
    """Stateful hysteresis gate. Can only *suppress* shading, never close."""

    def __init__(self, shade_above: float, open_below: float) -> None:
        self.shade_above = shade_above
        self.open_below = open_below
        self._shading = False  # remembered between evaluations

    def evaluate(self, value: float, kind: str) -> tuple[bool, str]:
        """Return ``(allow_shading, reason_fragment)`` for the given signal.

        ``allow_shading`` False means "keep the cover open regardless of
        geometry"; True means "geometry may shade".
        """
        c = clearness(value, kind)
        if c >= self.shade_above:
            self._shading = True
        elif c <= self.open_below:
            self._shading = False
        # else: inside the dead-band → hold previous state

        if self._shading:
            return True, f"bright enough (sun strength {c:g} ≥ {self.shade_above:g})"
        return False, f"not bright enough (sun strength {c:g} ≤ {self.open_below:g})"


def apply_governor(
    position: int,
    *,
    room_lux: float | None,
    cap: float,
    is_day: bool,
    min_position: int,
) -> tuple[int, str | None]:
    """Optionally trim the position more closed when the room is too bright.

    Bounded to a single :data:`GOVERNOR_STEP` per call and only during the day,
    so a noisy indoor sensor cannot drive a slow cover into oscillation. Returns
    ``(position, reason_fragment_or_None)``.
    """
    if not cap or room_lux is None or not is_day:
        return position, None
    if room_lux <= cap:
        return position, None
    trimmed = max(min_position, position - GOVERNOR_STEP)
    if trimmed == position:
        return position, None
    return trimmed, f"room-lux trim ({room_lux:g} > {cap:g})"
