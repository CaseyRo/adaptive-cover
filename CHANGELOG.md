# Changelog

All notable changes to Adaptive Cover (CDiT) are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/), and the
project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.3.0]

### Added
- **Diagnostic output sensors** (field-test feedback: "the magic worked — now
  show me *how*"). Each window now exposes standalone, history-graphable
  entities for the values that explain every decision: profile angle (γ), sun
  azimuth/elevation, the live sky signal (sky brightness in the source's own
  unit, or cloud cover %, created only for the configured source), and today's
  sun enters/leaves/peak as timestamp sensors. All carry the *diagnostic*
  entity category, mirroring the output-sensor pattern from the CDiT Adaptive
  Lighting fork.
- **`binary_sensor.<window>_sun_in_view`** — on while the sun is inside the
  window's field of view, so history shows exactly when geometry was active.

### Changed
- The sky signal is now read on **every** recompute (previously only when the
  geometry wanted to shade), so the sky sensors are meaningful all day. Gating
  behavior is unchanged; the Status sensor's `sky_signal`/`sky_value`
  attributes are now populated all day too.

## [0.2.0]

### Changed
- **Guided setup**: the "Add" step now collects the essentials — name, cover(s),
  facing direction (16-point compass), and an optional ±20° fine-tune — so a
  window works immediately instead of asking only for a name. (First field test
  showed the name-only step read as "is it broken?".)
- **Azimuth via compass + fine-tune**, replacing the two-pin map helper (which
  was awkward in practice). `azimuth = (compass + fine_tune) mod 360`; a raw
  numeric azimuth remains in the options Window section (used when facing is
  "Custom"). The map helper and `geometry.bearing()` are removed.
- Essentials are seeded into entry `data` at create time; readers merge
  `{defaults, data, options}` so options override.

## [0.1.0]

### Added
- Initial integration scaffolded after the adaptive_lighting CDiT fork.
- **Geometry engine** (`geometry.py`) — Model A floor-penetration positioning:
  profile angle, field-of-view gate, sun/sunset gating, min/max clamps, and a
  sun-window preview for setup verification. Pure and unit-tested.
- **Sky gating** (`sky.py`) — brightness-first signal (outdoor lux/irradiance)
  with weather cloud-cover fallback, a hysteresis dead-band so passing clouds
  can't make covers flap, and an optional bounded indoor-lux comfort governor.
- **Coordinator** — fixed-interval recompute publishing an explainable
  recommendation (position + reason + diagnostics).
- **Master switch** — per-window active control with the anti-hum movement
  policy (quantize / min-delta / cooldown) and multi-cover support.
- **Manual override (WAF)** — travel-tolerant detection that yields when a
  human moves a blind, with auto-reset on timeout and at sunrise, plus
  `reset_manual_control` and `apply_now` services.
- **Reason sensor** — recommended position as state, the "why" plus today's
  sun-entry preview as attributes; updates even when control is off.
- **Two live sky-threshold number entities** (`shade_above`, `open_below`).
- **Config + options flow** — single-field create step, sectioned
  `OptionsFlowWithReload`, help text from a single source, and a 16-point
  compass selector for window azimuth, plus a two-pin map helper (a pin inside
  the room + one outside the window → true-north bearing) for an exact azimuth.

### Known limitations / planned
- Vertical/simple covers only (no tilt or awning).
- Covers without `set_position` are detected and surfaced as a repair issue;
  open/close-only support is planned for a later release.
- A literal heading *dial* for azimuth isn't a stock config-flow selector, so
  the map helper uses two pins (bearing) rather than a single pin + dial.

[Unreleased]: https://github.com/CaseyRo/adaptive-cover
