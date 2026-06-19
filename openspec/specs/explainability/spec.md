# Explainability

## Purpose

Expose, per window, a reason sensor whose state is the recommended position and whose attributes explain the decision; ensure it computes regardless of control state; and provide a sun-window preview for setup verification.

## Requirements

### Requirement: Per-window reason sensor

Each window SHALL expose a sensor whose state is the recommended cover position (0–100) and whose attributes explain the decision. Attributes SHALL include at minimum: a human-readable `reason`, the profile angle, solar azimuth and elevation, whether the sun is in the field of view, the active sky signal and its value, the manual-override status, and the timestamp of the next scheduled evaluation. Where the reason refers to the sky decision, it SHALL express the compared value and threshold on the sun-strength axis (higher = more direct sun), not on a raw-input axis such as cloud cover.

#### Scenario: Reason explains a shading decision
- **WHEN** the system shades a window because the sun is in view and the sky is bright enough
- **THEN** the sensor state SHALL equal the recommended position and the `reason` attribute SHALL describe it (e.g. "shading 45% — sun in view, sun strength 72 ≥ 60")

#### Scenario: Reason explains a non-action
- **WHEN** the system leaves a window open because the sun-strength value is below the shade threshold
- **THEN** the `reason` attribute SHALL name the cause and the sun-strength value compared (e.g. "open — not bright enough, sun strength 28 ≤ open-below 30")

### Requirement: Sun-strength sensor

Each window SHALL expose a **Sun strength** sensor whose value is exactly the value the sky gate compares its thresholds against: the raw outdoor-brightness value on the brightness path, or `100 − cloud%` on the weather cloud-cover path. The sensor SHALL be created whenever any sky signal source (a brightness sensor or a weather entity) is configured, and SHALL NOT be created when none is. When the configured source is momentarily unavailable, the sensor SHALL report unknown rather than a stale value. Its unit SHALL be fixed per entity at setup (the source sensor's own unit on the brightness path; `%` on the cloud path). Because it is the axis the cover acts on and the value the user tunes against, it SHALL be a primary sensor (no diagnostic entity category) surfaced alongside the Status sensor rather than grouped with the diagnostic telemetry, and SHALL update on every recompute. This sensor SHALL replace the former raw `Sky brightness` sensor (which reported the same value on the brightness path); the raw **Cloud cover** sensor SHALL remain as weather telemetry.

#### Scenario: Sun strength is a primary sensor, not diagnostic
- **WHEN** a window with a configured sky source is set up
- **THEN** the Sun strength sensor SHALL carry no diagnostic entity category, so it appears with the primary sensors rather than in the diagnostic group

#### Scenario: Sun strength rises as skies clear (cloud path)
- **WHEN** a weather entity is the active sky signal and its cloud coverage falls from 70% to 20%
- **THEN** the Sun strength sensor SHALL rise from 30 to 80, moving the same direction as the shade/open thresholds

#### Scenario: Sun strength equals the brightness value (brightness path)
- **WHEN** an outdoor brightness sensor is the active sky signal
- **THEN** the Sun strength sensor SHALL report that sensor's value in its own unit, and no separate `Sky brightness` sensor SHALL exist

#### Scenario: No sky signal configured
- **WHEN** neither a brightness sensor nor a weather entity is configured
- **THEN** no Sun strength sensor SHALL be created for that window

### Requirement: Standalone diagnostic output sensors

Each window SHALL expose standalone, read-only diagnostic sensor entities — in addition to the reason sensor's attributes — so each explanatory value is individually recordable and graphable in history. The set SHALL include: profile angle (°), sun azimuth (°), sun elevation (°), and the sun-window preview times (sun enters, sun leaves, sun peak) as timestamp sensors. When a sky signal source is configured, the sky signal value SHALL also be exposed as a sensor whose unit is fixed per entity (lx for a brightness sensor, % for weather cloud cover). All diagnostic sensors SHALL carry the diagnostic entity category and SHALL update on every recompute. A sensor whose underlying value was not computed (e.g. profile angle after sunset) SHALL report unknown rather than a stale value.

#### Scenario: Profile angle is graphable during a shading day
- **WHEN** the sun is in the window's field of view and geometry runs
- **THEN** the profile angle sensor SHALL report γ in degrees, matching the value in the reason sensor's attributes

#### Scenario: Values not computed report unknown
- **WHEN** the sun is below the horizon and geometry does not run
- **THEN** the profile angle sensor SHALL report unknown

#### Scenario: Sky sensor only exists when a source is configured
- **WHEN** neither a brightness sensor nor a weather entity is configured
- **THEN** no sky signal sensor SHALL be created for that window

#### Scenario: Preview times exposed as timestamps
- **WHEN** the daily preview computes an entry, exit, and peak time
- **THEN** the sun-enters, sun-leaves, and sun-peak sensors SHALL report those times as timestamp states

### Requirement: Sun-in-view binary sensor

Each window SHALL expose a binary sensor that is on when the sun is within the window's field of view (and above the minimum elevation), mirroring the `in_field_of_view` attribute of the reason sensor.

#### Scenario: Sun enters the field of view
- **WHEN** a recompute finds the sun inside the configured field of view and above the minimum elevation
- **THEN** the sun-in-view binary sensor SHALL be on

#### Scenario: Sun outside the field of view
- **WHEN** a recompute finds the sun outside the field of view or below the minimum elevation
- **THEN** the sun-in-view binary sensor SHALL be off

### Requirement: Sensor computes regardless of control state

The reason sensor SHALL update on every recompute whether or not the master switch is on, so the recommended position can be observed and trusted before active control is enabled.

#### Scenario: Observation with control disabled
- **WHEN** the master switch is off
- **THEN** the reason sensor SHALL still publish the position the system *would* command, with reason text intact

### Requirement: Sky signal sampled on every recompute

The system SHALL read the configured sky signal on every recompute — not only when the geometry wants to shade — so the sky signal sensor reflects current conditions all day. Gating behavior SHALL be unchanged: the sky gate SHALL still only influence the recommended position when the geometry wants to shade.

#### Scenario: Sky value available while the window is open
- **WHEN** the sun is not in the field of view (no shading wanted) and a weather entity with cloud coverage is configured
- **THEN** the sky signal sensor SHALL still report the current cloud coverage

#### Scenario: Gating unchanged when shading is not wanted
- **WHEN** the sun is not in the field of view and the sky is clear
- **THEN** the recommended position SHALL be the open/max position exactly as before, unaffected by the sky reading

### Requirement: Sun-window preview for setup verification

The system SHALL expose, per window, a preview of when direct sun is expected to enter and leave the window today (an approximate start/end time and peak), derived from the same geometry engine, so a user can confirm the window azimuth was entered correctly without waiting for the event.

#### Scenario: Preview confirms a plausible azimuth
- **WHEN** a window azimuth and field of view are configured such that the sun enters during the day
- **THEN** the preview SHALL report an approximate entry and exit time and a peak time for today

#### Scenario: Preview flags an implausible azimuth
- **WHEN** the configured azimuth and field of view are such that the sun never enters the window today
- **THEN** the preview SHALL indicate that no direct sun is expected, signalling a likely setup error
