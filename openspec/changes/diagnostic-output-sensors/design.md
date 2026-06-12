## Context

All explanatory values (profile angle γ, sun position, sky signal, preview times) are computed each tick by `AdaptiveCoverCoordinator` and published in `AdaptiveCoverData`, but only surfaced as attributes of the single Status sensor (`sensor.py`). HA records attributes but cannot graph them; users field-testing the integration want to *see* how the decision evolved over a day. The sibling CDiT Adaptive Lighting fork ships standalone output sensors for exactly this purpose (`OUTPUT_SENSORS` table in its `const.py` + a thin reader entity), which is the pattern to mirror — adapted to this codebase's coordinator architecture.

## Goals / Non-Goals

**Goals:**
- Every value already in `AdaptiveCoverData` that explains the decision becomes its own history-graphable entity.
- Sky signal observable all day, not only when shading is wanted.
- Zero behavior change to positioning, gating, or the existing Status sensor.

**Non-Goals:**
- No new configuration options, config-flow steps, or stored data.
- No reason/text sensor (the reason stays an attribute; it is not graphable data).
- No restore-on-restart for diagnostic sensors (stale values are worse than one `unknown` tick — same decision as the AL fork).
- No changes to the AL fork itself.

## Decisions

1. **Coordinator entities, not dispatcher signals.** The AL fork uses a dispatcher because its switch drives updates; here a `DataUpdateCoordinator` already exists, so the new sensors are plain `CoordinatorEntity` readers like the Status sensor. Less machinery, same semantics.

2. **Data-driven description table in `const.py`** (`DIAGNOSTIC_SENSORS`): key, name, unit, icon, device class, and a value extractor per sensor — mirrors the AL fork's `OUTPUT_SENSORS` shape so the two codebases stay recognizably similar. One generic `AdaptiveCoverDiagnosticSensor` class consumes rows.

3. **One sky sensor per configured source, fixed unit.** HA long-term statistics break when a sensor's unit changes. `sky_kind` can flip at runtime (brightness sensor falls back to cloud cover), so a single "sky signal" sensor with a dynamic unit is wrong. Instead: create "Sky brightness" (lx) iff a brightness sensor is configured and "Cloud cover" (%) iff a weather entity is configured; each reports `unknown` when it is not the active signal or has no reading. Conditional creation matches the AL fork's `conditional: True` rows.

4. **Coordinator always reads the sky.** `_read_sky` moves out of the `wants_to_shade` branch and runs every update; the gate still only *evaluates* when shading is wanted. `AdaptiveCoverData` gains `sky_brightness`/`sky_cloud` resolved values (or keeps `sky_kind`/`sky_value` plus a second raw read — decided at implementation, whichever keeps the Status attributes byte-identical).

5. **Timestamps via `SensorDeviceClass.TIMESTAMP`** for sun enters/leaves/peak — HA renders these natively ("in 3 hours") and they remain attributes on Status for compatibility.

6. **`entity_category=DIAGNOSTIC`** on all new entities so the device page groups them under Diagnostics and they are excluded from auto dashboards. Sun azimuth/elevation duplicate `sun.sun`, but per-device copies make per-window dashboards self-contained and cost nothing.

7. **`state_class=MEASUREMENT`** on the numeric sensors (γ, azimuth, elevation, sky values) so HA records long-term statistics. Not on timestamps (not applicable).

8. **New `binary_sensor` platform** for "Sun in view" (`in_fov`), `device_class=None` with sun icon; added to `PLATFORMS` in `__init__.py`.

## Risks / Trade-offs

- [Entity count grows by ~7 per window] → All diagnostic-category; hidden from dashboards by default. Users wanted exactly this visibility.
- [Recorder volume increases] → Values change at most once per update interval; numeric states are cheap. Users can exclude entities via recorder config if needed.
- [`sky_value` semantics change inside `AdaptiveCoverData` if fields are added] → Keep existing fields untouched; only add. Status sensor assertions in existing tests must pass unmodified.
- [Unit-stability if a user reconfigures sources] → Entities are keyed by source kind (`sky_brightness` vs `sky_cloud`), never share a unique_id, so a reconfigure creates/removes entities instead of mutating units.

## Migration Plan

Pure addition: new entities appear after restart/reload of the integration. Rollback = downgrade; orphaned entities can be removed from the registry. No data migration.

## Open Questions

None — all decisions resolved above.
