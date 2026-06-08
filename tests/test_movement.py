"""HA-coupled tests for the anti-hum movement policy (task 4.5).

Covers quantize, min-delta suppression, and cooldown via the switch's apply
loop, plus the pure ``_quantize`` helper.
"""

from datetime import timedelta

from homeassistant.util import dt as dt_util

from custom_components.adaptive_cover.geometry import calculate_position
from custom_components.adaptive_cover.switch import _quantize

from .helpers import COVER, make_window, set_cover, set_sun


def test_quantize_pure():
    assert _quantize(47, 5) == 45
    assert _quantize(42, 10) == 40
    assert _quantize(50, 1) == 50  # step <= 1 is a no-op
    assert _quantize(3, 5) == 5


async def test_commands_quantized_position(hass):
    # Sun high on the window → geometry shades; cover starts open at 100.
    _, _, _, calls = await make_window(
        hass,
        sun_azimuth=180,
        sun_elevation=60,
        cover_position=100,
        options={"quantize_step": 5, "cooldown": 0},
    )
    assert len(calls) == 1
    commanded = calls[0].data["position"]
    assert calls[0].data["entity_id"] == COVER
    assert commanded % 5 == 0  # quantized
    assert commanded < 100  # actually shaded

    expected = calculate_position(60, 180, 180).position
    expected_q = _quantize(expected, 5)
    assert commanded == expected_q


async def test_no_command_when_already_at_target(hass):
    # Sun in the north → out of FOV → target is fully open (100); cover already
    # at 100, so the change is below min-delta and nothing is commanded.
    _, _, _, calls = await make_window(
        hass,
        sun_azimuth=10,
        sun_elevation=40,
        cover_position=100,
    )
    assert calls == []


async def test_cooldown_defers_then_allows(hass):
    coordinator_opts = {"quantize_step": 5, "min_delta": 5, "cooldown": 300}
    _, coordinator, switch, calls = await make_window(
        hass,
        sun_azimuth=180,
        sun_elevation=60,
        cover_position=100,
        options=coordinator_opts,
    )
    assert len(calls) == 1
    first = calls[0].data["position"]

    # A genuinely different target arrives, but within the cooldown window.
    set_cover(hass, first)  # settle where we commanded
    set_sun(hass, 180, 20)  # lower sun → much more closed → new target
    switch._last_move[COVER] = dt_util.utcnow()  # a move just happened
    calls.clear()
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert calls == []  # cooldown blocked the move

    # Once the cooldown has elapsed, the deferred target is applied.
    switch._last_move[COVER] = dt_util.utcnow() - timedelta(seconds=400)
    await switch._async_apply()
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["position"] % 5 == 0


async def test_unsupported_cover_raises_repair_issue(hass):
    from homeassistant.helpers import issue_registry as ir

    _, _, switch, calls = await make_window(
        hass,
        sun_azimuth=180,
        sun_elevation=60,
        cover_position=100,
    )
    commanded = calls[0].data["position"]
    # Re-publish the cover WITHOUT the SET_POSITION feature, settled where we
    # last commanded (so it is not flagged as a manual move), then force apply.
    hass.states.async_set("cover.test", "open", {"current_position": commanded})
    await hass.async_block_till_done()
    await switch._async_apply(force=True)
    await hass.async_block_till_done()

    registry = ir.async_get(hass)
    issue = registry.async_get_issue("adaptive_cover", "no_set_position_cover.test")
    assert issue is not None
