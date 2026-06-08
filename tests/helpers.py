"""Shared helpers for the HA-coupled Adaptive Cover tests.

These tests use ``pytest-homeassistant-custom-component``. We mock ``sun.sun``
and the target cover as plain states (the integration only reads them), and we
register a capturing ``cover.set_cover_position`` service so we can assert what
the switch commands without a real cover platform.
"""

from __future__ import annotations

from homeassistant.components.cover import CoverEntityFeature
from homeassistant.const import ATTR_SUPPORTED_FEATURES
from homeassistant.core import Context, HomeAssistant, ServiceCall
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.adaptive_cover.const import DOMAIN

COVER = "cover.test"


def set_cover(hass: HomeAssistant, position: int, *, cover: str = COVER, context=None):
    """Set a cover's state, optionally with a foreign (non-integration) context."""
    hass.states.async_set(
        cover,
        "open",
        {
            "current_position": position,
            ATTR_SUPPORTED_FEATURES: CoverEntityFeature.SET_POSITION,
        },
        context=context or Context(),
    )


def set_sun(hass: HomeAssistant, azimuth: float, elevation: float):
    state = "above_horizon" if elevation > 0 else "below_horizon"
    hass.states.async_set(
        "sun.sun", state, {"azimuth": azimuth, "elevation": elevation}
    )


async def make_window(
    hass: HomeAssistant,
    *,
    options: dict | None = None,
    sun_azimuth: float = 180.0,
    sun_elevation: float = 60.0,
    cover_position: int = 100,
):
    """Create and set up one window. Returns (entry, coordinator, switch, calls).

    ``calls`` is the list of captured ``cover.set_cover_position`` ServiceCalls.
    The switch's initial apply has already run by the time this returns.
    """
    opts = {"covers": [COVER], "azimuth": 180}
    if options:
        opts.update(options)

    calls: list[ServiceCall] = []

    async def _capture(call: ServiceCall) -> None:
        calls.append(call)

    hass.services.async_register("cover", "set_cover_position", _capture)

    # States must exist before the switch subscribes, so the initial cover state
    # is not seen as a manual move and the first compute reads our mocked sun.
    set_cover(hass, cover_position)
    set_sun(hass, sun_azimuth, sun_elevation)
    await hass.async_block_till_done()

    entry = MockConfigEntry(domain=DOMAIN, title="Living room", data={}, options=opts)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][entry.entry_id]
    return entry, coordinator, coordinator.switch, calls
