## 1. Coordinator: always-on sky reading

- [x] 1.1 Move the `_read_sky` call out of the `wants_to_shade` branch in `coordinator.py` so `sky_kind`/`sky_value` are populated on every update; gate evaluation stays inside the branch
- [x] 1.2 Verify existing Status-sensor attribute output is unchanged for the shading path (existing tests pass unmodified)

## 2. Diagnostic sensor entities

- [x] 2.1 Add `DIAGNOSTIC_SENSORS` description table to `const.py` (profile angle, sun azimuth, sun elevation, sun enters/leaves/peak; sky brightness and cloud cover rows marked conditional on their source)
- [x] 2.2 Implement generic `AdaptiveCoverDiagnosticSensor` in `sensor.py` (CoordinatorEntity reader, `entity_category=DIAGNOSTIC`, `state_class=MEASUREMENT` for numerics, `device_class=TIMESTAMP` for preview times, `unknown` when value is None)
- [x] 2.3 Create conditional sky sensors only when their source is configured (brightness sensor → lx entity, weather entity → % entity); each reports unknown when not the active reading

## 3. Sun-in-view binary sensor

- [x] 3.1 Add `binary_sensor.py` platform exposing `in_fov` as "Sun in view" with diagnostic entity category
- [x] 3.2 Add `binary_sensor` to `PLATFORMS` in `__init__.py`

## 4. Tests

- [x] 4.1 Test diagnostic sensors publish values matching coordinator data (γ, azimuth, elevation, timestamps) and report unknown after sunset
- [x] 4.2 Test sky sensors: created only when source configured; cloud value present even when sun not in FOV (always-on read); position/gating unchanged
- [x] 4.3 Test binary sensor on/off follows `in_fov`
- [x] 4.4 Full suite passes (`pytest`)

## 5. Docs

- [x] 5.1 README: document the new diagnostic entities and what each means
- [x] 5.2 CHANGELOG entry
