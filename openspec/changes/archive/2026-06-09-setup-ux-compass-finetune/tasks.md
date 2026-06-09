## 1. Guided create step

- [x] 1.1 Rebuild `async_step_user`: form with Name + Cover(s) (EntitySelector) + Facing (16-point SelectSelector) + Fine-tune (±20° NumberSelector slider); resolve `azimuth = (compass[facing] + fine_tune) mod 360`; store `{covers, azimuth}` in entry `data`
- [x] 1.2 Add a shared `_resolve_azimuth(facing, fine_tune, fallback)` helper used by both the create step and the options flow

## 2. Options flow + data/options merge

- [x] 2.1 Window section: add the Fine-tune field; `facing` keeps the "custom" option; resolve azimuth from compass+fine-tune unless facing is "custom" (then use the numeric field)
- [x] 2.2 Remove the two `LocationSelector` map fields and the bearing call from `_flatten`
- [x] 2.3 Read config from `{**DEFAULTS, **entry.data, **entry.options}` in `coordinator.options` and in the options-flow prefill, so create-time `data` seeds a working config and options override it

## 3. Remove dead map code

- [x] 3.1 Delete `geometry.bearing()` and its test `test_bearing_cardinal_directions`
- [x] 3.2 Remove the `LocationSelector`/`bearing` imports and the map-pin strings from `strings.json` + `translations/en.json`

## 4. Strings & translations

- [x] 4.1 Add create-step (`config.step.user`) labels/descriptions for name, covers, facing, fine-tune
- [x] 4.2 Add the Fine-tune field label/description to the options Window section; drop the inside/outside map-pin strings

## 5. Tests

- [x] 5.1 Update `test_config_flow.py`: create step now requires name+cover+facing (+ optional fine-tune) and yields a working entry; compass+fine-tune resolves azimuth (e.g. South +8 → 188); remove the two-pin map test
- [x] 5.2 Remove the bearing test from `test_geometry.py`
- [x] 5.3 `uv run pytest` green; `ruff check` + `ruff format` clean

## 6. Release

- [x] 6.1 Bump `manifest.json` 0.1.0 → 0.2.0; update `CHANGELOG.md`
- [x] 6.2 Verify in an isolated HA boot (realnasivm): create flow yields a working window; options edit reloads
