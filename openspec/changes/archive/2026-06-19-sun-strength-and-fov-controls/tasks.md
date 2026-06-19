## 1. Sun-strength axis (kill the inversion)

- [x] 1.1 Expose the gate's clearness value on `AdaptiveCoverData` (e.g. `sun_strength`), computed every recompute via `sky.clearness(value, kind)` when a sky signal is active, else `None`
- [x] 1.2 `const.py` `DIAGNOSTIC_SENSORS`: replace the `sky_brightness` row with a `sun_strength` row — signal-agnostic (no `sky_kind`), created when any sky signal is configured, unit fixed at setup (source unit on the brightness path, `%` on the cloud path), `attr: "sun_strength"`
- [x] 1.3 Keep the `cloud_cover` row as raw weather telemetry (unchanged)
- [x] 1.4 `sky.py`: change reason fragments from "clearness {c}" / "level {c}" to "sun strength {c}" (shade + open branches)

## 2. Threshold help & reason wording

- [x] 2.1 Rewrite `DOCS[CONF_SHADE_ABOVE]` / `DOCS[CONF_OPEN_BELOW]` in sun-strength terms ("watch the Sun strength sensor; higher = more direct sun; cloud path = 100 − cloud%")
- [x] 2.2 Mirror the rewritten help into `strings.json` + `translations/en.json` (`sections/sky/data_description`)

## 3. Field of view → live number controls

- [x] 3.1 `number.py`: add `Field of view — left` / `— right` `RestoreNumber` entities (min 0, max 90, step 1, unit °); generalise the platform so it is no longer hard-coded to the two thresholds
- [x] 3.2 Init order on `async_added_to_hass`: last restored value → stored option (`coordinator.options[key]`) → default 90; push into the coordinator override store
- [x] 3.3 `coordinator.py`: add `self._overrides: dict[str, float]` + `set_override(key, value)`; `set_override` clears `_preview_cache_date`
- [x] 3.4 `_async_update_data` + `_compute_preview`: read effective `fov_left`/`fov_right` as `self._overrides.get(key, opts[key])`
- [x] 3.5 Remove `CONF_FOV_LEFT` / `CONF_FOV_RIGHT` from `SECTIONS["sun"]` and drop the Sun-section FOV strings from `strings.json` + `translations/en.json`

## 4. Strings & translations

- [x] 4.1 Add labels/descriptions for the `Field of view — left/right` number entities
- [x] 4.2 Add label/description for the `Sun strength` diagnostic sensor; remove the `Sky brightness` sensor strings

## 5. Tests

- [x] 5.1 `test_sky.py`: reason fragments now say "sun strength"; hysteresis behaviour unchanged
- [x] 5.2 `test_diagnostics.py`: `sun_strength` sensor present and equal to `100 − cloud%` (cloud path) / raw value (brightness path); `sky_brightness` gone; `cloud_cover` unchanged
- [x] 5.3 New: FOV number entities exist, restore over the stored option, and drive geometry/preview via the override store (changing the control changes the recommended position / preview)
- [x] 5.4 `test_config_flow.py`: the Sun section no longer lists `fov_left`/`fov_right`; stored FOV still honoured by the control
- [x] 5.5 `uv run pytest` green; `ruff check` + `ruff format` clean

## 6. Release

- [x] 6.1 Bump `manifest.json` 0.3.0 → 0.4.0; update `CHANGELOG.md` (note the `Sky brightness` → `Sun strength` sensor rename and FOV moving to controls)
- [x] 6.2 Verified via the HA test harness (in-process boot): a cloud-path window's `Sun strength` sensor rose 30→80 as cloud fell 70→20, crossing the shade threshold in the same direction as the dial; narrowing the right FOV control 90°→60° dropped the sun out of view live ("open — not in field of view")
