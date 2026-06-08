## 1. Scaffold & harness (from `adaptive_lighting`)

- [x] 1.1 Copy repo harness from `../adaptive_lighting`: `pyproject.toml` (uv), `.ruff.toml`, `.pre-commit-config.yaml`, `.devcontainer.json`, `scripts/` (`develop`, `lint`, `setup-devcontainer`), `tests/` skeleton, `config/` dev HA instance, `.gitignore`, `.gitattributes`
- [x] 1.2 Add `hacs.json` and a HACS-valid repo layout; set `domain: adaptive_cover`
- [x] 1.3 Create `custom_components/adaptive_cover/manifest.json` (domain, name "Adaptive Cover (CDiT)", `config_flow: true`, `dependencies: ["cover", "sun"]`, `iot_class: calculated`, `homeassistant: 2025.1.0`, codeowners) + Apache-2.0 `LICENSE`
- [x] 1.4 Verify the dev HA boots with the integration loaded — **runtime-verified on `realnasivm` against HA 2026.6.1** in an isolated container: integration loads, entry sets up, coordinator computes (`position=49, reason="shading 49% (γ=64°)"`), all 4 entities created, switch drives the cover (100→50, quantized)

## 2. Geometry engine (pure, unit-tested first)

- [x] 2.1 Implement `geometry.py`: profile angle `γ = atan(tan(elev)/cos(azi − win_azi))` and `position% = clamp(glare_distance·tan(γ)/height, min, max)·100`
- [x] 2.2 Implement the field-of-view gate (azimuth-in-range with 360° wrap) and `min_elevation` / sun-down gating returning `position_after_sunset`
- [x] 2.3 Implement the sun-window preview: approximate entry/exit/peak times for today from the same engine (`sun_window_interval` over sun samples)
- [x] 2.4 Unit tests (golden cases): high vs low sun, off-FOV, sunset, min/max clamps, larger `glare_distance` ⇒ more open, FOV wrap, closed-form cross-check, preview "never enters" — 28 assertions verified green via direct execution (formal `uv run pytest` is task 8.5)

## 3. Sky gating

- [x] 3.1 Implement signal resolution: outdoor brightness sensor → weather cloud-cover fallback → always-allow (`coordinator._read_sky`)
- [x] 3.2 Implement hysteresis dead-band (separate shade/open thresholds, hold-in-band), gate suppresses shading only (`sky.SkyGate`)
- [x] 3.3 Implement optional indoor-lux governor: bounded ≤1-step trim, daytime-gated, behind cooldown (`sky.apply_governor`)
- [x] 3.4 Unit tests: precedence, dead-band hold, "too dim ⇒ open", governor trim; unit-agnostic brightness vs inverted cloud — `tests/test_sky.py`, 12 assertions verified green via direct execution

## 4. Coordinator & movement policy

- [x] 4.1 Implement `coordinator.py` (DataUpdateCoordinator) recompute on `interval` tick, per window
- [x] 4.2 Implement anti-hum policy: quantize step, min-delta suppression, per-cover cooldown; track `last_commanded` (`switch._async_apply`, `_quantize`)
- [x] 4.3 Implement multi-cover-per-window dispatch (same target, independent bookkeeping)
- [x] 4.4 Detect covers without `set_position` via `supported_features` and raise a clear repair issue (v1 requires position-capable covers; no two-state fallback — design Q3 deferred to v1.x)
- [x] 4.5 Unit tests written (`tests/test_movement.py`): pure `_quantize`, quantized command, no-command-at-target, cooldown defer-then-allow, unsupported-cover repair issue — syntax-clean; PHACC execution tracked under 8.5

## 5. Master switch & manual-override (WAF)

- [x] 5.1 Implement `switch.py` per-window master switch; on ⇒ command covers, off ⇒ observe-only
- [x] 5.2 Port `adaptive_lighting` manual-control machinery to covers (manual dict, auto-reset timers, our-context tracking)
- [x] 5.3 Implement cover-travel-tolerant detection: ignore `opening`/`closing` and intermediate positions; mark manual only on settle outside `manual_tolerance` from last command, from a non-self context
- [x] 5.4 Implement auto-reset (timeout + sunrise) and `reset_manual_control` / `apply_now` services
- [x] 5.5 Unit tests written (`tests/test_manual_override.py`): within-tolerance not manual, outside-tolerance manual, transitional ignored, no-command-while-manual, reset service, timeout reset, sunrise reset — syntax-clean; PHACC execution tracked under 8.5

## 6. Explainability entities

- [x] 6.1 Implement `sensor.py` reason sensor: state = recommended position, attributes = reason, profile angle, sun azi/elev, in-FOV, sky signal+value, manual status
- [x] 6.2 Ensure the sensor computes and publishes even when the master switch is off (reads coordinator data directly)
- [x] 6.3 Expose the sun-window preview as sensor attributes (`sun_enters`/`sun_leaves`/`sun_peak`)
- [x] 6.4 Implement `number.py` with exactly two live-tunable entities — `shade_above` and `open_below` (RestoreNumber → `coordinator.set_threshold` → refresh)

## 7. Configuration & options flow

- [x] 7.1 Implement `const.py`: `CONF_`/`DEFAULTS` constants, `SECTIONS` layout, parallel `DOCS[]` help text (the design's field table; named `DEFAULTS`/`SECTIONS` rather than `VALIDATION_TUPLES`)
- [x] 7.2 Implement `config_flow.py`: single-field `async_step_user` (name) + `OptionsFlowWithReload` with sections Window · Geometry · Sun · Sky · Movement · Manual override
- [x] 7.3 Write `strings.json` + `translations/en.json` with section/field labels and the approximate, plain-language help texts
- [x] 7.4 Window-azimuth helper: 16-point compass selector mapping to degrees (default path)
- [ ] 7.5 Exact azimuth helper — *PARTIAL: numeric azimuth shipped; the "map pin + heading dial" needs a custom frontend element (stock config-flow selectors can't render a heading dial, and `LocationSelector` returns lat/lon only). Deferred to v1.x as a frontend card; flagged to user*
- [x] 7.6 Tests written (`tests/test_config_flow.py`): create-from-name, options defaults + facing→azimuth, options reload applies, defaults produce working behaviour — syntax-clean; PHACC execution tracked under 8.5

## 8. Docs, attribution & release

- [x] 8.1 Drop the README into repo root as `README.md` (screenshots/real entity names to be added after first run)
- [x] 8.2 Add `LICENSE` (Apache-2.0, matching the `adaptive_lighting` scaffold) and credit wording in README + `manifest.json`: basbruss/adaptive-cover (MIT) and the forum template credited as inspiration, not borrowed code (Q5)
- [x] 8.3 Add `CHANGELOG.md` (HACS release/version tag is a git/publish step, N/A in this non-git workspace)
- [ ] 8.4 Field test against a real south-facing blind across a full day; capture the reason sensor timeline and tune defaults — *needs hardware + running HA*
- [x] 8.5 **`uv run pytest` → 39 passed** (HA 2026.2.3 via PHACC on the Mac); **`ruff check` → all checks passed**, **`ruff format` → clean**. (`./scripts/lint`/pre-commit itself needs a git repo, which is created at deploy time.) Test-writing surfaced + fixed 3 real bugs: `NumberSelector` rejecting `unit_of_measurement=None` (options form wouldn't render), the switch failing entity setup on a missing cover service, and an unguarded `ServiceNotFound`
