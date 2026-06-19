## Why

Field testing showed the adaptive positioning "magic" works, but users can't see *how* it worked: every explanatory value (profile angle, sun position, sky signal, sun-window preview) lives only in attributes of the single Status sensor, and attributes can't be graphed in HA history. The sibling CDiT Adaptive Lighting fork solved the same problem with standalone read-only output sensors, and that pattern proved itself — Adaptive Cover should match it.

## What Changes

- Add standalone, per-window diagnostic sensors that publish values already computed by the coordinator:
  - Profile angle (°) — the core geometry output γ
  - Sun azimuth (°) and sun elevation (°)
  - Sky signal value — conditional on configuration; one stable-unit entity per source (lx for a brightness sensor, % for weather cloud cover)
  - Sun enters / sun leaves / sun peak — timestamp sensors from the daily preview
- Add a binary sensor "Sun in view" exposing `in_fov`.
- Coordinator reads the sky signal on **every** update (today it only reads it when the geometry wants to shade), so the sky sensor is meaningful all day. Gating behavior is unchanged: the gate still only applies when shading is wanted.
- New sensors carry `entity_category: diagnostic` so they group under "Diagnostic" on the device page and stay out of auto-generated dashboards.
- The existing Status sensor and all its attributes remain unchanged (backward compatible).

## Capabilities

### New Capabilities

(none — this extends the existing explainability capability)

### Modified Capabilities

- `explainability`: adds a requirement that each explanatory value is also exposed as a standalone, history-graphable entity (diagnostic sensors + binary sensor), and that the sky signal is sampled on every recompute rather than only when shading is wanted.

## Impact

- `custom_components/adaptive_cover/sensor.py` — new diagnostic sensor entities (data-driven, reading `coordinator.data`)
- `custom_components/adaptive_cover/binary_sensor.py` — new platform for "Sun in view"
- `custom_components/adaptive_cover/coordinator.py` — sky signal read unconditionally; `AdaptiveCoverData` unchanged in shape
- `custom_components/adaptive_cover/__init__.py` — `PLATFORMS` gains `binary_sensor`
- `custom_components/adaptive_cover/const.py` — sensor description table
- `tests/` — new sensor/binary-sensor platform tests; coordinator sky-read test
- No config-flow, options, or stored-data changes; no migration needed
