"""Adaptive Cover (CDiT) — sun-tracking covers for Home Assistant.

One config entry per window. Each entry owns a coordinator (the recompute loop)
and three entities: a master switch (active control + manual-override), a reason
sensor (the explainable recommendation), and two number entities (the live sky
thresholds).

The only "math" lives in ``geometry.py`` and ``sky.py`` and is deliberately free
of Home Assistant imports so it can be unit-tested in isolation.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import AdaptiveCoverCoordinator

PLATFORMS: list[str] = ["switch", "sensor", "number"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Adaptive Cover from a config entry."""
    coordinator = AdaptiveCoverCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
