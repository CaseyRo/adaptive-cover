## Context

The sky gate (`sky.py`) reduces every sky signal to one internal axis it calls **clearness** (higher = more direct sun): for a brightness sensor that is the raw value; for the weather fallback it is `100 − cloud%`. The `shade_above`/`open_below` thresholds always live on this axis. But the diagnostic the user watches during setup is **Cloud cover** — the *inverted* axis — so on the cloud path the threshold and the watched number move in opposite directions. Separately, the field-of-view spans are "tune while watching" values stranded in the options flow. Both are the same defect: the dial is not next to the number you watch.

## Goals / Non-Goals

**Goals:** make the sky thresholds read in the same direction as the number you watch; let field-of-view be tuned live like the existing thresholds; do it without breaking stored configs.

**Non-Goals:** changing gate hysteresis logic or geometry math; collapsing the two FOV knobs into one "arc width" (explicitly kept as two — left and right are independently obstructed); re-litigating whether the thresholds should *also* leave the options flow (noted as an open question, not done here).

## Decisions

### D1 — Expose the gate's axis as a "Sun strength" sensor, don't flip the thresholds
Two ways to kill the inversion: (A) surface the clearness axis the gate already uses and tune against that, or (B) re-express thresholds in cloud-space when cloud is the active signal. B makes a stored number mean opposite things depending on which signal is active (fragile when a user later adds a brightness sensor) and forces per-signal labels. A keeps one consistent internal model and simply shows the user the axis the model already uses. **Chosen: A.**

Concretely, add a `sun_strength` diagnostic sensor whose value is the gate's clearness input:
- brightness path → the raw sensor value (lux / W·m²)
- cloud path → `100 − cloud%`

It is signal-agnostic (no `sky_kind`), created whenever a sky signal is configured, and reports unknown when none is. Its unit is fixed at setup from the active source (the source sensor's unit on the brightness path, `%` on the cloud path) — the same "unit fixed per entity" rule the diagnostic sensors already use, so history statistics stay consistent. On the brightness path `sun_strength` equals the old `Sky brightness` sensor, so that sensor is **replaced** (not duplicated). **Cloud cover** stays as raw weather telemetry — it is the input, not the dial.

### D2 — Keep the threshold names; fix the words around them
`Shade above` / `Open below` are already correct against a "sun strength" axis (shade when strength is above X; open when below X). Renaming them would churn entities and stored state for no gain. Instead:
- Rewrite the `DOCS` help to say "watch the **Sun strength** sensor — higher = more direct sun; with a weather entity this is `100 − cloud%`, so it rises as skies clear."
- Change the gate's reason fragments from "clearness {c}" / "level {c}" to "sun strength {c}", and align the explainability spec's example reason text to the same axis (today the spec says `"cloud 72% ≥ open-above 70%"` while the code emits clearness-space text — both move to sun-strength).

### D3 — Field of view becomes live number controls, via a coordinator override store
The thresholds are live because they feed a **stateful** `SkyGate` through `coordinator.set_threshold()`. FOV is different: it is read fresh from `opts` every cycle by `geometry.calculate_position` and by the daily preview, so there is no stateful holder to push into. Add a minimal **live-override store** on the coordinator:
- `self._overrides: dict[str, float]` plus `set_override(key, value)`.
- `_async_update_data` reads effective FOV as `self._overrides.get(key, opts[key])`; the preview does the same and `set_override` clears `_preview_cache_date` so the "sun enters/leaves" preview recomputes when the arc changes.
- Two `RestoreNumber` entities (`Field of view — left/right`, `0–90°`, step 1). On add, initialise from last restored value → else the stored option → else default `90`, and push into the override store. On set, push + request refresh. This mirrors `AdaptiveCoverThreshold` exactly.

FOV is **removed** from the options-flow Sun section (the user asked for it in controls *over* configuration, and a single source avoids the very "two places, which wins?" confusion this change is about). Stored `fov_left`/`fov_right` are preserved because the control seeds from the stored option on first run.

### D4 — One change, three capabilities
The two threads are independent but rhyme ("dial next to the number"). Kept as one change touching `sky-gating` (name the axis + require it be observable), `explainability` (the new sensor + reason wording), and `configuration` (FOV control surface + threshold help).

## Risks / Trade-offs

- **`sun_strength` unit when both sources are configured** → brightness wins, so the unit is the brightness unit and the cloud path is dormant; **Cloud cover** still shows raw cloud. Consistent with current precedence.
- **Replacing `Sky brightness`** → its entity id/unique-id changes to `sun_strength`. Acceptable pre-1.0; the value is identical on the brightness path. Note in the changelog.
- **FOV no longer in the options flow** → diverges from the thresholds' dual presence (options flow *and* number). Deliberate; flagged as the open question below rather than silently making the surface inconsistent.
- **Override store vs. just attributes** → a generic `_overrides` dict is barely more code than two attributes and lets any field graduate from config to control later (e.g. glare distance), so it is preferred.

## Open Questions

- Should `shade_above` / `open_below` *also* leave the options flow now that FOV does, so all live-tunable knobs live in exactly one place (controls)? Out of scope here; worth a follow-up once the FOV pattern is proven.
- Glare distance is an equally pure "tune while watching" comfort knob and a natural next candidate for the same override path — deferred.
