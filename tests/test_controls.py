"""HA-coupled tests for the live-tunable field-of-view number controls.

The field-of-view spans graduated from the options flow to number entities, so
they can be dragged on a dashboard while watching the cover. These assert the
controls exist, seed from the stored option, and feed the geometry engine live
through the coordinator's override map.
"""

import pytest

from .helpers import make_window

SUN_IN_VIEW = "binary_sensor.living_room_sun_in_view"
STATUS = "sensor.living_room_recommended_position"


def _fov_ids(hass) -> tuple[str, str]:
    """The left/right field-of-view number entity ids (thresholds end otherwise)."""
    ids = hass.states.async_entity_ids("number")
    left = next(e for e in ids if e.endswith("_left"))
    right = next(e for e in ids if e.endswith("_right"))
    return left, right


async def test_fov_controls_exist_and_default_to_90(hass):
    await make_window(hass)
    left, right = _fov_ids(hass)
    assert float(hass.states.get(left).state) == pytest.approx(90.0)
    assert float(hass.states.get(right).state) == pytest.approx(90.0)


async def test_fov_control_seeds_from_stored_option(hass):
    # An existing entry that configured a narrower right arc keeps it: the
    # control initialises from the stored option, not the default.
    await make_window(hass, options={"fov_right": 30})
    _, right = _fov_ids(hass)
    assert float(hass.states.get(right).state) == pytest.approx(30.0)


async def test_narrowing_fov_drops_the_sun_out_of_view(hass):
    # Window faces south (180); the sun 70° to its right (250) is in view at the
    # default 90° arc, then falls out once the right arc is narrowed to 60°.
    await make_window(hass, sun_azimuth=250, sun_elevation=45)
    assert hass.states.get(SUN_IN_VIEW).state == "on"

    _, right = _fov_ids(hass)
    await hass.services.async_call(
        "number", "set_value", {"entity_id": right, "value": 60}, blocking=True
    )
    await hass.async_block_till_done()

    assert hass.states.get(SUN_IN_VIEW).state == "off"
    status = hass.states.get(STATUS)
    assert status.state == "100"
    assert status.attributes["reason"] == "open — not in field of view"
