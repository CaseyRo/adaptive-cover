"""Master control switch + movement policy + manual-override (the WAF core).

When on, this entity drives the window's covers toward the coordinator's
recommended position, subject to the anti-hum movement policy (quantize /
min-delta / cooldown). It watches the covers for moves it did not command and,
when it sees one *settle* outside a tolerance band, marks that cover
"manually controlled" and stops touching it until a timeout or the next sunrise.

The tricky part covers add (that lights don't): a commanded cover reports a
stream of intermediate positions and ``opening``/``closing`` states while it
travels. Those must not be mistaken for manual control. We therefore ignore
transitional states, ignore changes carrying our own command context, and only
react to a *settled* position outside the tolerance band.
"""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    SERVICE_SET_COVER_POSITION,
    CoverEntityFeature,
)
from homeassistant.components.cover import (
    DOMAIN as COVER_DOMAIN,
)
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, ATTR_SUPPORTED_FEATURES
from homeassistant.core import Context, Event, HomeAssistant, callback
from homeassistant.exceptions import ServiceNotFound
from homeassistant.helpers import entity_platform
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import (
    CONF_COOLDOWN,
    CONF_COVERS,
    CONF_MANUAL_TIMEOUT,
    CONF_MANUAL_TOLERANCE,
    CONF_MIN_DELTA,
    CONF_QUANTIZE_STEP,
    DOMAIN,
    SERVICE_APPLY_NOW,
    SERVICE_RESET_MANUAL,
    SUN_ENTITY,
)
from .coordinator import AdaptiveCoverCoordinator
from .entity import AdaptiveCoverEntity

_LOGGER = logging.getLogger(__name__)

TRANSITIONAL = ("opening", "closing")


def _quantize(value: int, step: int) -> int:
    if step <= 1:
        return value
    return int(round(value / step) * step)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the master switch and register entity services."""
    coordinator: AdaptiveCoverCoordinator = hass.data[DOMAIN][entry.entry_id]
    switch = AdaptiveCoverSwitch(coordinator)
    async_add_entities([switch])

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_RESET_MANUAL, {}, "async_reset_manual"
    )
    platform.async_register_entity_service(SERVICE_APPLY_NOW, {}, "async_apply_now")


class AdaptiveCoverSwitch(AdaptiveCoverEntity, SwitchEntity, RestoreEntity):
    """Enable/disable active control for a window and own its control state."""

    _attr_name = "Adaptive control"
    _attr_icon = "mdi:blinds-horizontal"

    def __init__(self, coordinator: AdaptiveCoverCoordinator) -> None:
        super().__init__(coordinator)
        coordinator.switch = self  # let the sensor surface manual state
        self._attr_unique_id = f"{self._entry.entry_id}_control"
        self._attr_is_on = True
        self._covers: list[str] = list(coordinator.options.get(CONF_COVERS, []))
        self._last_commanded: dict[str, int] = {}
        self._last_move: dict[str, datetime] = {}
        self._manual: dict[str, datetime] = {}
        self._manual_unsub: dict[str, object] = {}
        self._our_contexts: set[str] = set()
        self._unsubs: list[object] = []

    # --- lifecycle ---------------------------------------------------------

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            self._attr_is_on = last.state == "on"

        if self._covers:
            self._unsubs.append(
                async_track_state_change_event(
                    self.hass, self._covers, self._cover_changed
                )
            )
        self._unsubs.append(
            async_track_state_change_event(self.hass, [SUN_ENTITY], self._sun_changed)
        )
        if self._attr_is_on:
            # Scheduled, not awaited: a transiently-missing cover or service must
            # not fail entity setup — the next recompute will apply anyway.
            self.hass.async_create_task(self._async_apply())

    async def async_will_remove_from_hass(self) -> None:
        for unsub in self._unsubs:
            unsub()
        for unsub in self._manual_unsub.values():
            unsub()
        await super().async_will_remove_from_hass()

    @callback
    def _handle_coordinator_update(self) -> None:
        if self._attr_is_on:
            self.hass.async_create_task(self._async_apply())

    # --- switch on/off -----------------------------------------------------

    async def async_turn_on(self, **kwargs) -> None:
        self._attr_is_on = True
        self.async_write_ha_state()
        await self._async_apply()

    async def async_turn_off(self, **kwargs) -> None:
        self._attr_is_on = False
        self.async_write_ha_state()

    @property
    def manual_covers(self) -> list[str]:
        """Covers currently under manual control (read by the sensor)."""
        return sorted(self._manual)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "manually_controlled": sorted(self._manual),
            "covers": self._covers,
        }

    # --- entity services ---------------------------------------------------

    async def async_reset_manual(self) -> None:
        """Service: clear manual control and resume adaptation."""
        self.reset_manual()
        await self._async_apply(force=True)

    async def async_apply_now(self) -> None:
        """Service: re-apply the current recommendation immediately."""
        await self._async_apply(force=True)

    # --- control loop ------------------------------------------------------

    def _cover_position(self, cover: str) -> int | None:
        state = self.hass.states.get(cover)
        if state is None:
            return None
        pos = state.attributes.get(ATTR_CURRENT_POSITION)
        try:
            return int(pos) if pos is not None else None
        except (TypeError, ValueError):
            return None

    def _supports_set_position(self, cover: str) -> bool:
        state = self.hass.states.get(cover)
        if state is None:
            return True  # unknown yet; don't raise prematurely
        features = state.attributes.get(ATTR_SUPPORTED_FEATURES, 0) or 0
        return bool(features & CoverEntityFeature.SET_POSITION)

    async def _async_apply(self, *, force: bool = False) -> None:
        if not self._attr_is_on:
            return
        data = self.coordinator.data
        if data is None:
            return
        opts = self.coordinator.options
        step = int(opts[CONF_QUANTIZE_STEP])
        min_delta = int(opts[CONF_MIN_DELTA])
        cooldown = int(opts[CONF_COOLDOWN])
        target = _quantize(data.position, step)
        now = dt_util.utcnow()

        for cover in self._covers:
            if cover in self._manual:
                continue
            if not self._supports_set_position(cover):
                self._raise_unsupported(cover)
                continue
            current = self._cover_position(cover)
            last = self._last_commanded.get(cover)
            if not force:
                if current is not None and abs(target - current) < min_delta:
                    continue
                if last is not None and abs(target - last) < min_delta:
                    continue
                last_move = self._last_move.get(cover)
                if (
                    last_move is not None
                    and (now - last_move).total_seconds() < cooldown
                ):
                    continue
            await self._command(cover, target)

    async def _command(self, cover: str, position: int) -> None:
        context = Context()
        self._our_contexts.add(context.id)
        # Keep the set bounded.
        if len(self._our_contexts) > 64:
            self._our_contexts = set(list(self._our_contexts)[-32:])
        try:
            await self.hass.services.async_call(
                COVER_DOMAIN,
                SERVICE_SET_COVER_POSITION,
                {ATTR_ENTITY_ID: cover, ATTR_POSITION: position},
                blocking=False,
                context=context,
            )
        except ServiceNotFound:
            _LOGGER.warning(
                "cover.set_cover_position is unavailable; cannot drive %s", cover
            )
            return
        self._last_commanded[cover] = position
        self._last_move[cover] = dt_util.utcnow()

    def _raise_unsupported(self, cover: str) -> None:
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            f"no_set_position_{cover}",
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="no_set_position",
            translation_placeholders={"cover": cover},
        )

    # --- manual-override detection -----------------------------------------

    @callback
    def _cover_changed(self, event: Event) -> None:
        cover = event.data[ATTR_ENTITY_ID]
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in TRANSITIONAL:
            return  # ignore in-flight travel
        ctx = event.context
        if ctx is not None and (
            ctx.id in self._our_contexts or ctx.parent_id in self._our_contexts
        ):
            return  # our own command settling
        pos = new_state.attributes.get(ATTR_CURRENT_POSITION)
        if pos is None:
            return
        try:
            pos = int(pos)
        except (TypeError, ValueError):
            return
        last = self._last_commanded.get(cover)
        tol = int(self.coordinator.options[CONF_MANUAL_TOLERANCE])
        if last is not None and abs(pos - last) <= tol:
            return  # settled where we asked — not manual
        self._mark_manual(cover)

    @callback
    def _mark_manual(self, cover: str) -> None:
        self._manual[cover] = dt_util.now()
        if (unsub := self._manual_unsub.pop(cover, None)) is not None:
            unsub()
        timeout = int(self.coordinator.options[CONF_MANUAL_TIMEOUT])
        self._manual_unsub[cover] = async_call_later(
            self.hass, timeout, self._make_clear_cb(cover)
        )
        _LOGGER.debug("%s marked manually controlled", cover)
        self.async_write_ha_state()

    def _make_clear_cb(self, cover: str):
        @callback
        def _clear(_now) -> None:
            self._clear_manual(cover)

        return _clear

    @callback
    def _clear_manual(self, cover: str) -> None:
        self._manual.pop(cover, None)
        if (unsub := self._manual_unsub.pop(cover, None)) is not None:
            unsub()
        self.async_write_ha_state()
        if self._attr_is_on:
            self.hass.async_create_task(self._async_apply())

    @callback
    def reset_manual(self, cover: str | None = None) -> None:
        """Clear manual control for one cover or all of them."""
        targets = [cover] if cover else list(self._manual)
        for target in targets:
            self._clear_manual(target)

    @callback
    def _sun_changed(self, event: Event) -> None:
        old = event.data.get("old_state")
        new = event.data.get("new_state")
        if (
            old is not None
            and new is not None
            and old.state == "below_horizon"
            and new.state == "above_horizon"
        ):
            _LOGGER.debug("Sunrise — resetting manual control for all covers")
            self.reset_manual()
