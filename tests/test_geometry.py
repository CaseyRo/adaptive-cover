"""Golden-case tests for the pure geometry engine.

These import ``geometry`` directly and never touch Home Assistant, so they run
fast and in isolation — the engine is the one piece of real maths, so it gets
verified first and on its own.
"""

import math

import pytest

from custom_components.adaptive_cover.geometry import (
    CLOSED,
    OPEN,
    SunSample,
    angle_in_fov,
    calculate_position,
    profile_angle,
    sun_window_interval,
)

SOUTH = 180.0


# --- profile_angle ---------------------------------------------------------


def test_profile_angle_on_axis_equals_elevation():
    # Sun on the window normal: the projected angle is just the elevation.
    assert profile_angle(30.0, SOUTH, SOUTH) == pytest.approx(30.0, abs=1e-6)


def test_profile_angle_off_axis_exceeds_elevation():
    # Off to the side, the same elevation projects to a steeper profile angle.
    on_axis = profile_angle(30.0, SOUTH, SOUTH)
    off_axis = profile_angle(30.0, SOUTH + 40.0, SOUTH)
    assert off_axis > on_axis


# --- angle_in_fov ----------------------------------------------------------


def test_in_fov_centre_and_edges():
    assert angle_in_fov(SOUTH, SOUTH, 45, 45) is True
    assert angle_in_fov(180 - 45, SOUTH, 45, 45) is True
    assert angle_in_fov(180 + 45, SOUTH, 45, 45) is True


def test_out_of_fov():
    assert angle_in_fov(90.0, SOUTH, 45, 45) is False
    assert angle_in_fov(280.0, SOUTH, 45, 45) is False


def test_in_fov_wraps_around_north():
    # A north-facing window (0°) spanning 315°-45°.
    assert angle_in_fov(350.0, 0.0, 45, 45) is True
    assert angle_in_fov(10.0, 0.0, 45, 45) is True
    assert angle_in_fov(180.0, 0.0, 45, 45) is False


# --- calculate_position: the headline behaviours ---------------------------


def test_high_sun_is_more_open_than_low_sun():
    low = calculate_position(15.0, SOUTH, SOUTH)
    high = calculate_position(60.0, SOUTH, SOUTH)
    assert high.position > low.position
    assert high.in_fov and low.in_fov


def test_larger_glare_distance_opens_more():
    strict = calculate_position(40.0, SOUTH, SOUTH, glare_distance=0.3)
    relaxed = calculate_position(40.0, SOUTH, SOUTH, glare_distance=1.5)
    assert relaxed.position > strict.position


def test_sun_out_of_fov_is_open_with_reason():
    # Sun in the north (10°) cannot reach a south-facing window.
    decision = calculate_position(40.0, 10.0, SOUTH)
    assert decision.position == OPEN
    assert decision.in_fov is False
    assert "field of view" in decision.reason


def test_after_sunset_uses_configured_position():
    decision = calculate_position(-5.0, SOUTH, SOUTH, position_after_sunset=100)
    assert decision.position == 100
    assert decision.reason == "after sunset"
    assert decision.profile_angle is None


def test_below_min_elevation_is_open():
    decision = calculate_position(3.0, SOUTH, SOUTH, min_elevation=5.0)
    assert decision.position == OPEN
    assert "below" in decision.reason


def test_min_position_clamp():
    # Very low sun in view drives toward closed; clamp holds the floor.
    decision = calculate_position(6.0, SOUTH, SOUTH, min_elevation=5.0, min_position=20)
    assert decision.position >= 20


def test_max_position_clamp():
    decision = calculate_position(80.0, SOUTH, SOUTH, max_position=70)
    assert decision.position <= 70


def test_position_matches_closed_form():
    # Independently recompute Model A and confirm the engine agrees.
    elev, glare, height = 35.0, 0.5, 2.1
    gamma = profile_angle(elev, SOUTH, SOUTH)
    expected = round(glare * math.tan(math.radians(gamma)) / height * 100)
    decision = calculate_position(
        elev, SOUTH, SOUTH, glare_distance=glare, window_height=height
    )
    assert decision.position == expected
    assert CLOSED <= decision.position <= OPEN


# --- sun_window_interval (setup preview) -----------------------------------


def _track():
    # A crude south-facing day: azimuth sweeps 90→270, elevation arcs up at noon.
    samples = []
    for i in range(25):  # hourly-ish samples
        az = 90 + i * 7.5  # 90 → 270
        elev = 60 * math.sin(math.pi * i / 24)  # 0 → 60 → 0
        samples.append(SunSample(time=f"t{i:02d}", azimuth=az, elevation=elev))
    return samples


def test_preview_finds_an_interval_for_a_sunny_window():
    interval = sun_window_interval(_track(), SOUTH, 45, 45)
    assert interval.entry is not None
    assert interval.exit is not None
    assert interval.peak is not None
    assert interval.entry <= interval.peak <= interval.exit


def test_preview_reports_no_sun_for_wrong_azimuth():
    # A window facing due north never sees this southern track.
    interval = sun_window_interval(_track(), 0.0, 45, 45)
    assert interval == (None, None, None)
