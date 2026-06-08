"""HA-coupled tests for manual-override detection and reset (task 5.5).

Verifies the WAF behaviour: the integration yields to a human-moved cover but is
not fooled by its own commanded travel, and resumes on timeout / sunrise / reset.
"""

from datetime import timedelta

from homeassistant.components.cover import CoverEntityFeature
from homeassistant.const import ATTR_SUPPORTED_FEATURES
from homeassistant.core import Context
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from .helpers import COVER, make_window, set_cover, set_sun


async def _commanded(hass):
    """A set-up window whose initial apply has commanded the cover once."""
    entry, coordinator, switch, calls = await make_window(
        hass,
        sun_azimuth=180,
        sun_elevation=60,
        cover_position=100,
    )
    assert calls, "expected the initial apply to command the cover"
    return entry, coordinator, switch, calls, calls[0].data["position"]


async def test_settle_within_tolerance_is_not_manual(hass):
    _, _, switch, _, last = await _commanded(hass)
    set_cover(hass, last + 3, context=Context())  # within default tolerance (5)
    await hass.async_block_till_done()
    assert switch.manual_covers == []


async def test_settle_outside_tolerance_marks_manual(hass):
    _, _, switch, _, last = await _commanded(hass)
    set_cover(hass, last + 30, context=Context())  # well outside tolerance
    await hass.async_block_till_done()
    assert COVER in switch.manual_covers


async def test_transitional_travel_is_ignored(hass):
    _, _, switch, _, _ = await _commanded(hass)
    # A mid-travel 'opening' report at an arbitrary position must not flag manual.
    hass.states.async_set(
        COVER,
        "opening",
        {
            "current_position": 40,
            ATTR_SUPPORTED_FEATURES: CoverEntityFeature.SET_POSITION,
        },
        context=Context(),
    )
    await hass.async_block_till_done()
    assert switch.manual_covers == []


async def test_no_command_while_manual(hass):
    _, _, switch, calls, last = await _commanded(hass)
    set_cover(hass, last + 30, context=Context())  # → manual
    await hass.async_block_till_done()
    assert COVER in switch.manual_covers

    calls.clear()
    await switch._async_apply(force=True)  # force must still respect manual
    await hass.async_block_till_done()
    assert calls == []


async def test_reset_service_resumes_control(hass):
    _, _, switch, _, last = await _commanded(hass)
    set_cover(hass, last + 30, context=Context())
    await hass.async_block_till_done()
    assert COVER in switch.manual_covers

    await switch.async_reset_manual()
    await hass.async_block_till_done()
    assert switch.manual_covers == []


async def test_timeout_auto_resets(hass):
    _, _, switch, _, last = await _commanded_with_timeout(hass)
    set_cover(hass, last + 30, context=Context())
    await hass.async_block_till_done()
    assert COVER in switch.manual_covers

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=2))
    await hass.async_block_till_done()
    assert switch.manual_covers == []


async def test_sunrise_resets_all(hass):
    _, _, switch, _, last = await _commanded(hass)
    set_cover(hass, last + 30, context=Context())
    await hass.async_block_till_done()
    assert COVER in switch.manual_covers

    set_sun(hass, 180, -5)  # below horizon
    await hass.async_block_till_done()
    set_sun(hass, 180, 30)  # back above → sunrise
    await hass.async_block_till_done()
    assert switch.manual_covers == []


async def _commanded_with_timeout(hass):
    entry, coordinator, switch, calls = await make_window(
        hass,
        sun_azimuth=180,
        sun_elevation=60,
        cover_position=100,
        options={"manual_timeout": 1},
    )
    assert calls
    return entry, coordinator, switch, calls, calls[0].data["position"]
