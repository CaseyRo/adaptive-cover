# Changelog

All notable changes to Adaptive Cover (CDiT) are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/), and the
project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
  compass selector for window azimuth.

### Known limitations / planned
- Vertical/simple covers only (no tilt or awning).
- Covers without `set_position` are detected and surfaced as a repair issue;
  open/close-only support is planned for a later release.
- The exact "map pin + heading dial" azimuth helper needs a custom frontend
  element (stock config-flow selectors can't render a heading dial); the v1
  surface is numeric azimuth + the 16-point compass.

[Unreleased]: https://github.com/CaseyRo/adaptive-cover
