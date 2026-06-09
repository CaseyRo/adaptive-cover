## Why

Sun-tracking ("adaptive") covers are genuinely magical — blinds that quietly position themselves to keep direct sun off your desk, the floor, and the heat out — but every existing Home Assistant option is either heavy or hard to live with. The dominant HACS integration (`basbruss/adaptive-cover`) is feature-complete to a fault: three cover modes, a climate/security/basic strategy matrix, 7–10 entities per window, ~15 setup parameters, and 84 open issues. The original community template sensor is a wall of Jinja trig. The result is the recurring complaint: *amazing when it works, frustrating to set up and debug.*

We already proved a leaner philosophy works in our `adaptive_lighting` CDiT fork (opinionated, single-household, fewer knobs, explainable). This change applies that exact philosophy to covers: **one required input, the geometry hidden behind sane defaults, a human-readable reason for every decision, and a manual-override that never fights the person holding the blind.**

## What Changes

- **New custom integration** `custom_components/adaptive_cover/`, scaffolded after the `adaptive_lighting` CDiT fork (config-flow, `VALIDATION_TUPLES` + `DOCS[]`, `OptionsFlowWithReload`, HACS/uv/pytest/devcontainer harness) — **fresh code, not a fork of `basbruss/adaptive-cover`** (it shares structure, almost no math).
- **Scope: vertical / "simple" covers only** — covers that travel open↔closed by position. No tilt/Venetian, no awning/horizontal, no rotation. Deliberately expandable later.
- **Model A geometry** (floor-penetration): `position% = clamp(glare_distance · tan(profile_angle) / window_height, 0, 1) · 100`. Sun azimuth + elevation come free from `sun.sun`; the only input that needs human thought is **window azimuth**.
- **Sky gating, lux-first**: prefer an outdoor illuminance/irradiance sensor ("only shade when it's actually bright"); fall back to a weather entity's cloud-cover %. **Hysteresis** (separate shade/open thresholds + dead-band) so passing clouds can't make slow, loud covers flap. Optional **indoor-lux governor** as a bounded comfort trim.
- **Active control with a master switch** per window (switch on ⇒ the integration drives the cover), mirroring `adaptive_lighting`.
- **Manual-override (WAF)**: detect cover changes the integration did not command — with **cover-travel tolerance** (ignore in-flight `opening`/`closing`, compare settled position to last command ± band) — mark "manually controlled," back off, and **auto-reset** (timeout or next sunrise).
- **Anti-hum movement policy**: quantize to steps, minimum delta, per-cover cooldown, tick-based recompute — covers are slow and loud, so this is essential, not cosmetic.
- **Explainability as a first-class feature**: a `sensor` per window whose state is the recommended position and whose attributes carry the `reason`, profile angle, sun azimuth/elevation, FOV state, sky signal, and manual-override status — working even when the master switch is off ("what *would* it do"). Plus a **"sun enters ~HH:MM–HH:MM today" preview** to verify the azimuth was entered correctly without waiting.
- **Window-azimuth UX**: 16-way compass buttons as the zero-friction default, plus an exact helper (in-flow map: drop a point inside the room + one outside the window ⇒ compute true-north bearing server-side).
- **A thorough README** for the HA community, with explicit credit to `basbruss/adaptive-cover`, the original HA community forum template, and our `adaptive_lighting` fork.

No breaking changes (greenfield integration). It is intentionally **not** a config-compatible replacement for `basbruss/adaptive-cover`.

## Capabilities

### New Capabilities
- `cover-positioning`: the geometry engine — Model A profile-angle calculation, field-of-view gate, sun up/down gating, position-after-sunset, min/max clamps. Produces a target position from sun + window geometry.
- `sky-gating`: deciding *whether* shading is warranted — outdoor lux/irradiance preferred, weather cloud-cover fallback, hysteresis dead-band, optional indoor-lux comfort governor.
- `cover-control`: applying targets to real covers — per-window master switch, recompute interval, and the anti-hum movement policy (quantize, min-delta, cooldown).
- `manual-override`: detecting and respecting human-initiated cover movement with cover-travel tolerance, plus auto-reset back to automatic control.
- `explainability`: the per-window reason sensor (state + diagnostic attributes) and the "when does sun hit this window today" preview used to verify setup.
- `configuration`: the config + options flow — single-field create step, sectioned `OptionsFlowWithReload`, `VALIDATION_TUPLES`/`DOCS[]` schema source, and the window-azimuth compass/map helper.

### Modified Capabilities
<!-- None — greenfield integration, no existing specs in openspec/specs/. -->

## Impact

- **New code**: `custom_components/adaptive_cover/` (`__init__.py`, `geometry.py`, `config_flow.py`, `const.py`, `coordinator.py`/control, `switch.py`, `sensor.py`, `number.py`, `manifest.json`, `strings.json`, `translations/`, `services.yaml`).
- **New repo scaffolding** copied from `adaptive_lighting`: `hacs.json`, `pyproject.toml` (uv), `.ruff.toml`, `.pre-commit-config.yaml`, `tests/`, `scripts/develop`, `.devcontainer.json`, `config/` dev HA instance.
- **New docs**: root `README.md` (community-facing, with credits) — drafted here as `README.draft.md`, dropped into repo root at apply time.
- **HA dependencies**: `cover` domain; reads `sun.sun`, optional `weather.*`, optional illuminance `sensor.*`. Minimum HA version aligned with `adaptive_lighting` (≥ 2025.1.0).
- **External**: no third-party Python requirements expected (pure-stdlib trig). Optional companion azimuth helper is in-flow (HA map selector); no hosted service required.
