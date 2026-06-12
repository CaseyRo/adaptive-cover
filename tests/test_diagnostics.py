"""HA-coupled tests for the diagnostic output sensors and sun-in-view binary sensor.

The diagnostic entities are pure readers over the coordinator's data, so these
tests assert that each published state matches what the geometry/sky pipeline
computed — and that values which were *not* computed read as unknown instead of
going stale.
"""

import pytest

from custom_components.adaptive_cover.geometry import profile_angle

from .helpers import make_window, set_sun

PROFILE = "sensor.living_room_profile_angle"
AZIMUTH = "sensor.living_room_sun_azimuth"
ELEVATION = "sensor.living_room_sun_elevation"
CLOUD = "sensor.living_room_cloud_cover"
BRIGHTNESS = "sensor.living_room_sky_brightness"
SUN_IN_VIEW = "binary_sensor.living_room_sun_in_view"


async def test_diagnostic_sensors_match_coordinator_data(hass):
    await make_window(hass, sun_azimuth=200, sun_elevation=45)

    expected_gamma = profile_angle(45, 200, 180)
    assert float(hass.states.get(PROFILE).state) == pytest.approx(
        expected_gamma, abs=0.01
    )
    assert float(hass.states.get(AZIMUTH).state) == pytest.approx(200.0)
    assert float(hass.states.get(ELEVATION).state) == pytest.approx(45.0)
    assert hass.states.get(SUN_IN_VIEW).state == "on"

    # Preview timestamps exist as their own entities (state may be unknown only
    # if the sun never enters, which it does for a south window at default lat).
    for key in ("sun_enters", "sun_leaves", "sun_peak"):
        state = hass.states.get(f"sensor.living_room_{key}")
        assert state is not None
        assert state.state != "unavailable"


async def test_uncomputed_values_read_unknown_after_sunset(hass):
    await make_window(hass, sun_azimuth=300, sun_elevation=-5)

    # Geometry did not run → no profile angle; sun position is still reported.
    assert hass.states.get(PROFILE).state == "unknown"
    assert float(hass.states.get(AZIMUTH).state) == pytest.approx(300.0)
    assert hass.states.get(SUN_IN_VIEW).state == "off"


async def test_sky_sensors_absent_without_a_source(hass):
    await make_window(hass)
    assert hass.states.get(CLOUD) is None
    assert hass.states.get(BRIGHTNESS) is None


async def test_cloud_cover_reads_all_day_without_changing_position(hass):
    # Sun in the north → out of FOV → no shading wanted. The cloud value must
    # still be published (always-on sky read) while the position stays open.
    hass.states.async_set("weather.home", "cloudy", {"cloud_coverage": 72})
    await make_window(
        hass,
        sun_azimuth=10,
        sun_elevation=40,
        options={"weather_entity": "weather.home"},
    )

    assert float(hass.states.get(CLOUD).state) == pytest.approx(72.0)
    status = hass.states.get("sensor.living_room_status")
    assert status.state == "100"  # gating did not kick in
    assert status.attributes["reason"] == "open — not in field of view"
    # Brightness sensor not configured → that entity must not exist.
    assert hass.states.get(BRIGHTNESS) is None


async def test_sky_brightness_inherits_source_unit(hass):
    hass.states.async_set(
        "sensor.outdoor_irradiance", "350", {"unit_of_measurement": "W/m²"}
    )
    await make_window(
        hass,
        options={"brightness_sensor": "sensor.outdoor_irradiance"},
    )

    state = hass.states.get(BRIGHTNESS)
    assert state is not None
    assert state.attributes["unit_of_measurement"] == "W/m²"
    assert float(state.state) == pytest.approx(350.0)


async def test_sun_in_view_follows_the_sun(hass):
    _, coordinator, _, _ = await make_window(hass, sun_azimuth=180, sun_elevation=45)
    assert hass.states.get(SUN_IN_VIEW).state == "on"

    set_sun(hass, 10, 40)  # move the sun out of the field of view
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(SUN_IN_VIEW).state == "off"
    assert hass.states.get(PROFILE).state == "unknown"
