## MODIFIED Requirements

### Requirement: Minimal create step, full options flow

The config flow's create step SHALL collect the essentials needed for a working window — display name, cover entity(s), facing direction (16-point compass), and an optional fine-tune offset — so that adding the integration produces an immediately functional window without a separate configuration step. All advanced configuration (geometry, sun, sky, movement, manual override) SHALL remain in the options flow with working defaults.

#### Scenario: Adding a window yields a working configuration
- **WHEN** the user adds the integration and provides a name, one or more cover entities, and a facing direction
- **THEN** a window config entry SHALL be created with a resolved azimuth and SHALL begin adapting the cover with no further configuration required

#### Scenario: Advanced settings remain optional
- **WHEN** the user has completed the create step
- **THEN** all remaining settings SHALL be editable later via the options flow and SHALL use sane defaults until changed

### Requirement: Window-azimuth compass helper

The configuration SHALL set window azimuth from a 16-point compass selection plus an optional fine-tune offset in degrees, resolved as `azimuth = (compass_bearing + fine_tune) mod 360`. A raw numeric azimuth SHALL remain available as an advanced field and SHALL be used when no compass direction is chosen. Azimuth SHALL be stored in degrees relative to true north (matching `sun.sun`), with no magnetic-declination correction. The configuration SHALL NOT require a map-based helper.

#### Scenario: Compass plus fine-tune resolves the azimuth
- **WHEN** the user selects a compass direction (e.g. "South") and a fine-tune offset (e.g. +8°)
- **THEN** the system SHALL store the resolved azimuth in degrees (e.g. 188)

#### Scenario: Numeric azimuth used when no compass direction is chosen
- **WHEN** the user leaves the compass set to "custom" and sets the advanced numeric azimuth directly
- **THEN** the system SHALL store that numeric value as the azimuth
