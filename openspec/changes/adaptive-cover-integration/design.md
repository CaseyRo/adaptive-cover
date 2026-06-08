## Context

Adaptive (sun-tracking) covers are a high-delight, high-frustration feature in Home Assistant. The existing options sit at two extremes: the original community **template sensor** (a wall of Jinja trigonometry that users copy and fear to touch), and **`basbruss/adaptive-cover`** (a mature HACS integration that does everything — vertical/horizontal/tilt, basic/climate/security strategies, an aggregation hub, 7–10 entities per window, ~15 parameters — and carries ~84 open issues as evidence of that surface area).

We have already run the "descale a beloved-but-bloated integration" play successfully with our **`adaptive_lighting` CDiT fork** (`../adaptive_lighting`): opinionated for a single household, fewer knobs, deliberately not config-compatible with upstream, with a clean `const.py` → `config_flow` schema pipeline, `OptionsFlowWithReload`, and a `uv`/`pytest`/devcontainer/HACS harness. That repo is the architectural template for this one.

Constraints and givens:
- The real driver for leaving the prior Node-RED implementation is **WAF**: the household interface is HA → Homebridge → Apple Home, not Node-RED. Whatever we ship must be invisible and forgiving to a non-technical user in Apple Home.
- HA provides solar **azimuth + elevation for free** via `sun.sun`. We do not compute solar position.
- The prior Node-RED flow already discovered the key UX insight — emit a **reason**, not just a number — but used a less-transferable person/eye model and recomputed too eagerly for slow hardware.

## Goals / Non-Goals

**Goals:**
- One genuinely-required human input per window (**window azimuth**); sane defaults for all geometry and policy.
- **Explainability by default**: every decision carries a human-readable reason; a preview lets users verify azimuth without waiting for the sun.
- **WAF-safe control**: the user can grab a blind in Apple Home and the integration will not fight them; automatic control resumes on its own.
- **Quiet hardware**: covers are slow and loud — never hum, chase, or creep.
- ~2 entities per window (switch + reason sensor; optionally a few `number` tuners), versus 7–10 elsewhere.
- Reuse the `adaptive_lighting` repo harness and patterns wholesale.

**Non-Goals:**
- Tilt/Venetian and horizontal/awning covers (vertical/simple only for v1; expandable later).
- Config compatibility or migration from `basbruss/adaptive-cover` or the template sensor.
- A climate/heating strategy matrix, multi-strategy priority engine, or an aggregation "all blinds" hub (v1 keeps per-window scope).
- Exposing entities to Apple Home / Homebridge — that is the operator's HA configuration concern, explicitly out of scope of the plugin.
- Computing solar position ourselves.

## Decisions

### D1 — Fresh integration scaffolded from `adaptive_lighting`, not a fork of `basbruss/adaptive-cover`
Covers share `adaptive_lighting`'s *structure* (per-entry master switch, manual-control detection, `VALIDATION_TUPLES`→flow, coordinator/recompute loop, packaging) but almost none of `basbruss`'s *math or feature surface*. Forking `basbruss` would mean inheriting three modes and 84 issues only to delete most of it.
- **Chosen**: new `custom_components/adaptive_cover/`, copy the `adaptive_lighting` harness and patterns, port the manual-control machinery, write fresh geometry.
- **Alternatives**: (a) fork `basbruss` and strip — rejected, net deletion + inherited debt; (b) ship a blueprint — rejected, weak UI, hard to surface reasoning, no live-tunable state; (c) keep Node-RED — rejected, fails WAF (not the household's interface).

### D2 — Model A (floor penetration), not Model B (person/eye)
Model A: "limit how far direct sun reaches across the floor." Model B (the Node-RED flow): "don't dazzle a seated person at depth + eye height."
- **Chosen**: Model A. It needs fewer inputs, generalises to any room, and yields a single intuitive knob (`glare_distance`). Formula: `γ = atan(tan(elev)/cos(azi − win_azi))`, `pos% = clamp(glare_distance·tan(γ)/height, min, max)·100`.
- **Alternatives**: Model B — more accurate for a tuned room but requires per-room furniture inputs and doesn't transfer; revisit as an optional mode later.

### D3 — Vertical/simple covers only
Keeps geometry to one formula and the config to one mental model. Tilt and awning each add their own parameter family and math.
- **Chosen**: support covers with position (open↔closed). Covers that only support open/close (no `set_position`) are a known edge case (see R4).

### D4 — Sky gate is brightness-first, with hysteresis; cloud cover is a fallback proxy
Cloud-cover % is subjective (60% vs 80%) and laggy. The real question is "is there enough direct sun to bother?" — best answered by an outdoor lux/irradiance sensor.
- **Chosen**: prefer outdoor brightness sensor → cloud-cover fallback → (neither) always-allow. **Hysteresis** dead-band (separate shade/open thresholds) so passing clouds can't flap slow covers. Thresholds exposed as live-tunable `number` entities so the subjective call is a slider, not a setup guess. The gate can only *suppress* shading, never close.
- **Alternatives**: single cloud threshold (rejected — flaps, subjective); soft-fade closure scaled by clearness (deferred to v2 polish; hysteresis + slider solve the actual pain first).

### D5 — Indoor-lux as a bounded governor, never the primary controller
An optional room-lux sensor closes the loop on the thing users actually feel (room brightness), but closed-loop control of a 20-second actuator from a noisy signal oscillates, and a room sensor is confounded by lamps — **including the lamps `adaptive_lighting` is driving next door**.
- **Chosen**: indoor lux is an optional, daytime-gated, bounded trim (≤ one step per cycle, plus cooldown); outdoor brightness remains the sky gate.
- **Alternatives**: full closed-loop on indoor lux (rejected — oscillation + artificial-light cross-talk).

### D6 — Active control via a per-window master switch (mirror `adaptive_lighting`)
The "magic" comes from the integration moving the cover itself, as AL moves lights.
- **Chosen**: `switch.adaptive_cover_<window>`; on ⇒ command covers, off ⇒ observe-only (sensor still computes). Operator may bridge this switch to Apple Home themselves (out of scope).
- **Alternatives**: publish a recommended-position sensor only and let users wire their own automations (the `basbruss` default) — rejected, pushes complexity back onto the user and breaks the "it just works" promise.

### D7 — Manual-override detection with cover-travel tolerance (the WAF core)
Port AL's `manual_control` machinery, but covers add a hazard lights don't: a commanded cover reports a stream of intermediate positions and `opening`/`closing` states while travelling, which naive detection mistakes for manual control → the integration backs off from its own command (deadlock).
- **Chosen**: track `last_commanded_position`; ignore transitional states; treat as manual only when the cover *settles* outside a tolerance band from the last command via a context we did not originate. Auto-reset on timeout and at sunrise; provide a reset service.
- **Alternatives**: event-context-only detection (fragile across HA versions); position-equality detection (false-positives on every travel) — both rejected.

### D8 — Anti-hum movement policy is a first-class pillar
- **Chosen**: recompute on a fixed `interval` tick (not per sun-attribute update); **quantize** to a step; suppress sub-**min-delta** moves; enforce a per-cover **cooldown**. This is essential complexity for slow/loud hardware, not optional polish.

### D9 — Explainability surface = reason sensor + preview
- **Chosen**: one `sensor.adaptive_cover_<window>` per window; state = recommended position, attributes = `reason`, profile angle, sun azi/elev, in-FOV, sky signal+value, manual status, next-eval. Updates even when the switch is off. A **"sun enters ~HH:MM–HH:MM today"** preview (same engine) verifies azimuth instantly and catches the most common setup error.

### D10 — Config flow mirrors `adaptive_lighting`
- **Chosen**: `async_step_user` = a single `CONF_NAME` field; everything else in an `OptionsFlowWithReload` grouped into sections (Window · Geometry · Sun · Sky · Movement · Manual override · Diagnostics). One source of truth: `VALIDATION_TUPLES` (field, default, validator) + parallel `DOCS[]` help text rendered in the UI. Drop AL's daytime/sunrise-sunset-schedule machinery (covers care about geometry, not a brightness schedule); add Geometry + Manual-override sections.

### D11 — Window-azimuth UX: 16-way default + in-HA "one pin + heading dial" helper
The one input that needs a human to *do* something. An in-HA map approach beats a phone magnetometer: works on the setup laptop, gives **true north** directly (HA's sun azimuth is true north; a phone gives **magnetic** and needs per-location declination correction), and needs no iOS permission/HTTPS gesture.
- **Chosen** *(resolves Q1)*: 16-point compass selection (±11°, good enough — azimuth is an approximation like height) as the default; an exact helper that drops **one map pin on the window** (`LocationSelector` → `{latitude, longitude}`, confirmed available) plus a **heading dial / degree input** for the facing direction. One map, one explicit heading — simpler to render than two synchronized map widgets.
- **Alternatives**: two map points inside→outside computing the bearing server-side (more intuitive but two map widgets in one form — rejected for v1 UX simplicity); phone magnetometer web app (declination + iOS-permission + accuracy footguns); hosted companion `/compass` page (extra deploy to maintain).

### Proposed `const.py` field set (VALIDATION_TUPLES sketch)

| Section | Field (`CONF_`) | Default | Notes / help-text gist |
|---|---|---|---|
| Window | `covers` | `[]` | Cover entities this window controls |
| Window | `azimuth` | `180` | Which way the glass faces; 16-way or map helper |
| Geometry | `window_height` | `2.1` m | Top of glass above floor — approximate |
| Geometry | `glare_distance` | `0.5` m | How far sun may reach across the floor |
| Sun | `fov_left` / `fov_right` | `90` / `90` | Azimuth span the window "sees" |
| Sun | `min_elevation` | `5`° | Ignore sun below this |
| Sun | `position_after_sunset` | `100` | Night/open position |
| Sun | `min_position` / `max_position` | `0` / `100` | Travel clamps |
| Sky | `brightness_sensor` | `""` | Outdoor lux/irradiance (preferred) |
| Sky | `weather_entity` | `""` | Cloud-cover fallback |
| Sky | `shade_above` / `open_below` | e.g. `35k`/`15k` lux or `40%`/`70%` cloud | Hysteresis pair (live-tunable `number`) |
| Sky | `indoor_lux_sensor` | `""` | Optional governor |
| Sky | `indoor_lux_cap` | `0` (off) | Comfort cap for the governor |
| Movement | `interval` | `120` s | Recompute tick |
| Movement | `quantize_step` | `5` % | Snap target |
| Movement | `min_delta` | `5` % | Suppress tiny moves |
| Movement | `cooldown` | `120` s | Min time between moves |
| Manual override | `manual_tolerance` | `5` % | Travel/settle tolerance band |
| Manual override | `manual_timeout` | `7200` s | Auto-reset after |
| Diagnostics | `reason_verbosity` | normal | Reason detail level |

### Module layout (mirrors `adaptive_lighting`)
```
custom_components/adaptive_cover/
├── __init__.py        entry setup/unload, PLATFORMS=["switch","sensor","number"]
├── geometry.py        pure trig: profile angle, position, sun-window preview (the only "math")
├── coordinator.py     DataUpdateCoordinator: tick, compute, movement policy, manual state
├── config_flow.py     single-name step + sectioned OptionsFlowWithReload over VALIDATION_TUPLES
├── const.py           CONF_/DEFAULT_ + VALIDATION_TUPLES + DOCS[]
├── switch.py          per-window master switch; ports manual-control machinery
├── sensor.py          reason sensor (state=position, attrs=why) + preview
├── number.py          live-tunable sky thresholds (shade_above/open_below) & co.
├── manifest.json      domain, deps ["cover"], version, codeowners, attribution links
├── strings.json / translations/   section + field labels & help text
└── services.yaml      reset_manual_control, (re)apply now
```

## Risks / Trade-offs

- **R1 — Indoor-lux closed-loop oscillation** → keep it a bounded, daytime-gated trim (≤1 step/cycle) behind the standard cooldown and dead-band; outdoor brightness stays the primary gate.
- **R2 — Manual-detection false positives from cover travel** (the classic deadlock) → ignore `opening`/`closing` and intermediate positions; compare only settled position to `last_commanded_position ± manual_tolerance`; covered by D7 and explicit spec scenarios.
- **R3 — Artificial-light cross-talk with `adaptive_lighting`** on a shared room-lux sensor → prefer outdoor brightness for the gate; document the confound; daytime-gate the governor.
- **R4 — Covers without `set_position`** (open/close only) → detect via `supported_features`; degrade to a two-state policy (open vs shade-to-min) or mark unsupported with a clear repair issue, rather than silently failing.
- **R5 — Weather cloud-cover is laggy/missing** → graceful fallback chain (sensor → weather → always-allow); never hard-fail when an optional input is absent.
- **R6 — Quantize vs coarse-reporting covers** → quantize step ≥ the cover's effective resolution; min-delta prevents oscillation around a value the hardware can't hit.
- **R7 — Magnetic vs true north** if any compass path is used → map helper yields true north directly; if a magnetometer is ever added, correct with HA's known lat/lon declination.
- **R8 — Multiple covers per window with different travel speeds** → per-cover cooldown and manual state; same target, independent movement bookkeeping.

## Migration Plan

Greenfield — no migration. Rollout: (1) scaffold harness from `adaptive_lighting`; (2) implement `geometry.py` + unit tests (golden cases: high/low sun, off-FOV, sunset, clamps); (3) coordinator + movement policy; (4) switch + manual-override; (5) sensor + preview; (6) config/options flow + azimuth helper; (7) README + HACS metadata; (8) field test against a real south-facing blind through a full day. Rollback is removal of the custom component (no shared state, no data migration).

## Resolved Decisions (from Q&A)

- **Q1 → "one pin + heading dial".** Default stays the 16-point compass. The exact helper drops one map pin on the window (`LocationSelector`) plus a heading dial/degree input — not the two-point bearing. (See D11.)
- **Q2 → only the two sky thresholds become `number` entities** (`shade_above`, `open_below`). Everything else stays options-flow-only, preserving ~2–3 entities per window. Glare distance and manual timeout are *not* live numbers in v1.
- **Q3 → defer open/close-only covers to v1.x.** v1 requires position-capable covers (`set_position`); open/close-only covers are detected via `supported_features` and surfaced as a clear repair issue rather than silently mishandled (R4). No two-state fallback in v1.
- **Q4 → unit-agnostic brightness slot.** The brightness sensor slot accepts any illuminance/irradiance sensor; thresholds are set in that sensor's own scale (lux or W/m² — both "higher = brighter"). No `device_class` interpretation. The separate weather/cloud slot retains its inverted handling (higher cloud = open more).
- **Q5 → license is Apache-2.0**, matching the `adaptive_lighting` scaffold we derive from (itself Apache-2.0 via `basnijholt`). `basbruss/adaptive-cover` (MIT) and the forum template are credited as **inspiration**, not borrowed code. Both licenses are permissive and compatible.

## Open Questions

- *(none blocking — all v1 decisions resolved above; revisit the two-point map bearing and open/close-only fallback as v1.x enhancements)*
