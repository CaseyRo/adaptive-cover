## ADDED Requirements

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

### Requirement: Sky signal sampled on every recompute

The system SHALL read the configured sky signal on every recompute — not only when the geometry wants to shade — so the sky signal sensor reflects current conditions all day. Gating behavior SHALL be unchanged: the sky gate SHALL still only influence the recommended position when the geometry wants to shade.

#### Scenario: Sky value available while the window is open
- **WHEN** the sun is not in the field of view (no shading wanted) and a weather entity with cloud coverage is configured
- **THEN** the sky signal sensor SHALL still report the current cloud coverage

#### Scenario: Gating unchanged when shading is not wanted
- **WHEN** the sun is not in the field of view and the sky is clear
- **THEN** the recommended position SHALL be the open/max position exactly as before, unaffected by the sky reading
