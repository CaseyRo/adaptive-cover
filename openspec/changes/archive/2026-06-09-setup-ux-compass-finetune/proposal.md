## Why

The first real field test of v0.1.0 surfaced two setup-UX problems:

1. The create step asks for **only a name**, so the essentials (cover entity, facing direction) are hidden behind a secondary "Configure" button — adding the integration appears to do nothing, and users ask "why isn't there more?".
2. The two-pin **map azimuth helper** sounded good but is awkward in practice (two pins, fiddly, poor on a phone).

## What Changes

- **Guided create step**: the initial form collects the essentials — name, cover(s), facing direction (16-point compass), and an optional fine-tune offset — so adding the integration produces an *immediately working* window. Advanced settings stay in the options flow.
- **Azimuth = compass + fine-tune**: replace the two-pin map helper with a 16-point compass select plus a ±20° fine-tune slider (`azimuth = (compass + fine_tune) mod 360`). A raw numeric azimuth stays available as an advanced field.
- **Remove the map helper**: delete the `LocationSelector` two-pin fields and the now-unused `geometry.bearing()` helper.
- Coordinator/config-flow read `azimuth`/`covers` from entry **data** (set at create) merged under entry **options** (set when tuning), so the create step can seed a working config.
- Version bump **0.1.0 → 0.2.0**.

Not a breaking change: existing entries store `azimuth` as a number, which is still honoured.

## Capabilities

### Modified Capabilities
- `configuration`: the create step now collects the essentials (was name-only); the azimuth helper becomes compass + fine-tune (the map helper is removed).

## Impact

- `config_flow.py` (richer create step, compass+fine-tune resolution, remove `LocationSelector`/bearing), `coordinator.py` (merge `data` under `options`), `geometry.py` (remove `bearing`), `strings.json` + `translations/en.json`, `manifest.json` (version), `tests/` (config-flow + geometry), `CHANGELOG.md`.
