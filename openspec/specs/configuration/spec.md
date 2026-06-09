# Configuration

## Purpose

Provide a low-friction setup: a minimal create step with a full options flow, sane defaults so only window azimuth needs human judgement, a sectioned options flow with live reload, and a compass/map helper for setting window azimuth.

## Requirements

### Requirement: Minimal create step, full options flow

The config flow SHALL create a window entry from a single required field (the window's display name). All other configuration SHALL live in an options flow so a window can be added in seconds and refined later.

#### Scenario: Add a window with only a name
- **WHEN** the user adds the integration and provides only a name
- **THEN** a window config entry SHALL be created and its options SHALL be editable afterwards

### Requirement: One meaningful input, defaults for the rest

Beyond the cover entity selection, the only configuration value that SHALL require human judgement is the window azimuth. Window height, glare distance, field of view, minimum elevation, sky thresholds, movement policy, and manual-override timeout SHALL all have sane defaults that produce reasonable behaviour unconfigured.

#### Scenario: Defaults produce working behaviour
- **WHEN** the user configures only the cover entity and window azimuth and leaves all advanced sections at defaults
- **THEN** the integration SHALL adapt the cover using default geometry and policy values without further input

### Requirement: Sectioned options flow with live reload

The options flow SHALL group fields into collapsible sections (Window, Geometry, Sun, Sky, Movement, Manual override, Diagnostics) and SHALL reload the entry on save so changes re-apply live. The field set and validation SHALL be driven by a single source (a `VALIDATION_TUPLES` list) with per-field help text from a parallel `DOCS` mapping.

#### Scenario: Editing an option re-applies immediately
- **WHEN** the user changes a value in the options flow and saves
- **THEN** the entry SHALL reload and the new value SHALL take effect on the next recompute without a restart

#### Scenario: Every field shows help text
- **WHEN** the user opens any options section
- **THEN** each field SHALL display its help text describing the approximate, plain-language meaning of the value

### Requirement: Window-azimuth compass helper

The configuration SHALL offer a low-friction way to set window azimuth: a 16-point compass selection (mapping cardinal/intercardinal directions to degrees) as the default, plus an exact helper that places a single map pin on the window and sets its facing direction via a heading dial / degree input. Azimuth values SHALL be stored in degrees relative to true north (matching `sun.sun`), with no magnetic-declination correction required.

#### Scenario: Compass direction maps to degrees
- **WHEN** the user selects a 16-point compass direction (e.g. "South-South-West")
- **THEN** the system SHALL store the corresponding azimuth in degrees

#### Scenario: Map pin plus heading dial sets the azimuth
- **WHEN** the user drops a map pin on the window and sets the facing direction with the heading dial
- **THEN** the system SHALL store the chosen heading as a true-north azimuth in degrees
