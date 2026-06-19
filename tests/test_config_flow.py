"""HA-coupled tests for the config + options flow (task 7.6)."""

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.adaptive_cover.const import (
    CONF_FOV_LEFT,
    CONF_FOV_RIGHT,
    DOMAIN,
    SECTIONS,
)

from .helpers import COVER, set_sun


def test_field_of_view_not_in_options_sun_section():
    # Field of view is tuned live via number entities, not the options flow.
    assert CONF_FOV_LEFT not in SECTIONS["sun"]
    assert CONF_FOV_RIGHT not in SECTIONS["sun"]


def _options_input(window: dict) -> dict:
    """A full sectioned options payload; empty sections fall back to defaults."""
    return {
        "window": window,
        "geometry": {},
        "sun": {},
        "sky": {},
        "movement": {},
        "manual": {},
    }


async def test_create_step_yields_working_entry(hass):
    set_sun(hass, 180, 40)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    # Name + cover + facing + fine-tune in one go → a working window.
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": "Kitchen", "covers": [COVER], "facing": "S", "finetune": 8},
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Kitchen"
    await hass.async_block_till_done()

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.data["covers"] == [COVER]
    assert entry.data["azimuth"] == 188  # South (180) + fine-tune (+8)

    # The create-time data must reach the engine via the defaults/data/options merge.
    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert coordinator.options["covers"] == [COVER]
    assert coordinator.options["azimuth"] == 188
    assert coordinator.data is not None


async def test_options_fill_defaults_and_facing_maps_to_azimuth(hass):
    set_sun(hass, 180, 40)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Living room",
        options={"covers": [COVER], "azimuth": 180},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"], _options_input({"covers": [COVER], "facing": "W"})
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    # Facing "W" overrides azimuth → 270; geometry default filled in.
    assert entry.options["azimuth"] == 270
    assert entry.options["window_height"] == 2.1
    # Optional entity slots resolve to empty strings, never missing.
    assert entry.options["brightness_sensor"] == ""


async def test_options_reload_applies_new_value(hass):
    set_sun(hass, 180, 40)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Living room",
        options={"covers": [COVER], "azimuth": 180},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        result["flow_id"], _options_input({"covers": [COVER], "facing": "E"})
    )
    await hass.async_block_till_done()

    # OptionsFlowWithReload recreated the entry → fresh coordinator sees azimuth 90.
    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert coordinator.options["azimuth"] == 90


async def test_options_finetune_offsets_compass(hass):
    set_sun(hass, 180, 40)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Living room",
        options={"covers": [COVER], "azimuth": 0},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    # South with a -10° nudge → 170.
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        _options_input({"covers": [COVER], "facing": "S", "finetune": -10}),
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["azimuth"] == 170


async def test_defaults_produce_working_behaviour(hass):
    set_sun(hass, 180, 50)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Living room",
        options={"covers": [COVER], "azimuth": 180},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert coordinator.data is not None
    assert 0 <= coordinator.data.position <= 100
    assert isinstance(coordinator.data.reason, str)
