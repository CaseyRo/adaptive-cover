## Context

v0.1.0 shipped with a name-only create step (mirrored from `adaptive_lighting`) and a two-pin map azimuth helper. The first field test showed both are awkward: the create step hides the cover/azimuth that covers *need* to function, and the two pins are fiddly. This change reworks just the configuration surface.

## Goals / Non-Goals

**Goals:** an "Add" flow that yields a working window from one short form; an intuitive, fully-native azimuth input.

**Non-Goals:** changing the geometry/control engine; a custom frontend element (compass widget / map line) — see D2.

## Decisions

### D1 — Guided create form (one richer screen), not name-only
Covers can't act without a cover entity and a direction, so those belong in the create step. The step collects **name + cover(s) + facing + fine-tune**; everything else stays in the options flow with defaults.

### D2 — Azimuth = compass + fine-tune; the map helper is removed
Of the three ideas raised (visual compass widget, a "line" on one map, 16-points + fine-tune), only the last is buildable with stock config-flow selectors — HA has no rotary/compass widget and no map line/vector selector (`LocationSelector` is a lone pin), so a compass widget or map line would need a custom frontend element. **16-point `SelectSelector` + a ±20° `NumberSelector` fine-tune** is native and the clearest UX: pick the rough direction, nudge it. `azimuth = (compass[facing] + fine_tune) mod 360`. The ±20° range comfortably covers the 22.5° gap between compass points. The two-pin map and `geometry.bearing()` are removed as dead weight.

### D3 — Essentials live in entry `data`, tuning in `options`
A config flow's `async_create_entry` can set `data` but not `options`. So the create step seeds `{covers, azimuth}` into `data`; the options flow writes the full set into `options`. The coordinator and options flow read `{**DEFAULTS, **entry.data, **entry.options}` so options override the create-time seed.

## Risks / Trade-offs

- **Stored-azimuth compatibility** → existing entries keep a numeric `azimuth`; the merge reads it unchanged. No migration.
- **Fine-tune range too small** → ±20° > half the 22.5° inter-point gap, so any true azimuth is reachable; the raw numeric field in Advanced covers exact needs.
- **Removing `bearing()`** → it's currently only used by the map helper; deleting it (and its test) avoids dead code. Re-add if a future map feature needs it.

## Open Questions

- None blocking. A custom compass-card frontend element remains a possible future enhancement (out of scope here).
