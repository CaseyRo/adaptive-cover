"""Pure tests for the sky gate and the indoor-lux governor.

Like the geometry tests, these touch no Home Assistant — the coordinator feeds
``SkyGate``/``apply_governor`` values read from HA, but the logic itself stands
alone.
"""

from custom_components.adaptive_cover.const import SKY_BRIGHTNESS, SKY_CLOUD
from custom_components.adaptive_cover.sky import SkyGate, apply_governor, clearness


def test_clearness_brightness_is_passthrough():
    assert clearness(35000, SKY_BRIGHTNESS) == 35000


def test_clearness_cloud_inverts():
    assert clearness(70, SKY_CLOUD) == 30


def test_gate_hysteresis_holds_in_dead_band():
    gate = SkyGate(shade_above=60, open_below=30)
    assert gate.evaluate(70, SKY_BRIGHTNESS)[0] is True  # bright → shade
    assert gate.evaluate(45, SKY_BRIGHTNESS)[0] is True  # dead-band → hold shade
    assert gate.evaluate(20, SKY_BRIGHTNESS)[0] is False  # dim → open
    assert gate.evaluate(45, SKY_BRIGHTNESS)[0] is False  # dead-band → hold open


def test_gate_cloud_is_inverted():
    gate = SkyGate(shade_above=60, open_below=30)  # thresholds in clearness
    assert gate.evaluate(20, SKY_CLOUD)[0] is True  # cloud 20 → clearness 80 → shade
    assert gate.evaluate(85, SKY_CLOUD)[0] is False  # cloud 85 → clearness 15 → open


def test_gate_reason_uses_sun_strength_wording():
    # The user-facing axis is "sun strength" (not "clearness"/"level"/"cloud"),
    # so the reason reads in the same direction as the threshold that was set.
    gate = SkyGate(shade_above=60, open_below=30)
    allow, shade_frag = gate.evaluate(70, SKY_BRIGHTNESS)
    assert allow is True and "sun strength" in shade_frag
    allow, open_frag = gate.evaluate(85, SKY_CLOUD)
    assert allow is False and "sun strength" in open_frag


def test_governor_trims_when_room_too_bright():
    pos, frag = apply_governor(50, room_lux=3000, cap=2000, is_day=True, min_position=0)
    assert pos < 50
    assert frag is not None


def test_governor_noop_when_disabled():
    assert apply_governor(50, room_lux=3000, cap=0, is_day=True, min_position=0) == (
        50,
        None,
    )


def test_governor_noop_at_night():
    assert apply_governor(
        50, room_lux=3000, cap=2000, is_day=False, min_position=0
    ) == (50, None)


def test_governor_respects_min_position():
    pos, _ = apply_governor(10, room_lux=9999, cap=100, is_day=True, min_position=5)
    assert pos == 5
