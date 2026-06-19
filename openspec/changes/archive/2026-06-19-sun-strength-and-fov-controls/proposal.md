## Why

A field test of v0.3.0 surfaced two confusing things about the configuration surface, both variations of the same problem — *the dial you turn is not next to the number you watch.*

1. **The sky thresholds feel inverted against the cloud-cover sensor.** The gate works on an internal "clearness" axis (higher = more direct sun). With a weather entity, clearness = `100 − cloud%`. So `Shade above 60` actually fires when the **Cloud cover** diagnostic drops *below* 40 — the threshold and the sensor you watch during setup move in opposite directions. (Only the cloud path is affected; a brightness sensor already reads on the same axis.) The spec even imagined cloud-space reason text (`"cloud 72% ≥ open-above 70%"`) while the code emits clearness-space text, so the inversion is baked into a spec/impl divergence too.

2. **The field-of-view (left/right) angles live in the options flow, but they are "tune while watching" values.** Narrowing one side because a neighbouring house blocks that arc is exactly the kind of knob you drag on a dashboard and observe over a day — the same justification the Shade/Open thresholds already won when they became number entities.

## What Changes

- **Expose the gate's real axis as a "Sun strength" diagnostic sensor.** It reports exactly what the gate compares against (brightness path → the raw sensor value; cloud path → `100 − cloud%`), so the number you watch always moves the *same* direction as your thresholds. This replaces the raw-input `Sky brightness` sensor (which was the same value on the brightness path); the **Cloud cover** sensor stays as raw weather telemetry.
- **Keep the `Shade above` / `Open below` names** — they read correctly against a sun-strength axis — but rewrite their help text and the gate's reason fragments to speak in **sun strength**, not "clearness/level/cloud". The explainability reason text is aligned to the same axis (fixing the spec/impl divergence).
- **Move `Field of view — left` / `— right` out of the options flow into live, restoring number entities** (`0–90°`, default `90`), mirroring the existing threshold controls. Existing entries keep their configured FOV (the control restores from the stored option on first run).
- **Add a small live-override path in the coordinator** so a number entity can drive a value that geometry reads each cycle (FOV is read from `opts`, not the stateful gate, so it needs this). Changing FOV also invalidates the cached daily sun-window preview.
- Version bump **0.3.0 → 0.4.0**.

Not a breaking change: stored `shade_above`/`open_below`/`fov_left`/`fov_right` values keep their meaning; the FOV controls initialise from the stored options.

## Capabilities

### Modified Capabilities

- `sky-gating`: names the user-facing tuning axis ("sun strength", higher = more direct sun) and requires that the value the thresholds compare against is exposed for the user to watch and tune by.
- `explainability`: adds a **Sun strength** diagnostic sensor (the gate's comparison value, fixed unit per source) replacing the raw `Sky brightness` sensor; reason text for sky decisions is expressed on the sun-strength axis.
- `configuration`: field-of-view left/right move from the options flow to live number-entity controls; sky-threshold help text is rewritten in sun-strength terms.

## Impact

- `custom_components/adaptive_cover/const.py` — `DIAGNOSTIC_SENSORS` (swap `sky_brightness` → `sun_strength`); `DOCS`/`SECTIONS` (drop FOV from the Sun section, rewrite threshold help)
- `custom_components/adaptive_cover/number.py` — add `Field of view — left/right` number entities (restoring), generalise beyond the two thresholds
- `custom_components/adaptive_cover/coordinator.py` — live-override store + `set_override`; geometry/preview read effective FOV; preview cache invalidated on FOV change; expose the gate's clearness value on `AdaptiveCoverData` for the new sensor
- `custom_components/adaptive_cover/sky.py` — reason fragments in "sun strength" wording
- `custom_components/adaptive_cover/config_flow.py` — remove FOV from the Sun section + `NUMBER_RANGES` usage there
- `strings.json` + `translations/en.json` — new sensor/number labels, rewritten threshold help, drop FOV from the Sun section
- `manifest.json` — version 0.3.0 → 0.4.0
- `tests/` — sky reason wording, new diagnostic sensor, FOV number entities + override path, config-flow no longer lists FOV
- `CHANGELOG.md`
