## ADDED Requirements

### Requirement: Field of view tuned as live controls

The left and right field-of-view spans SHALL be exposed as live, per-window number-entity controls (range `0–90°`), not as options-flow fields, so they can be tuned from a dashboard while observing cover behaviour — for example narrowing one side because a neighbouring structure blocks that arc. Each control SHALL restore its last value across restarts and SHALL take effect on the next recompute without an options-flow round trip. On first run for an existing entry, a control SHALL initialise from the value previously stored in options (falling back to the default of `90°`), so upgrading does not change a window's configured field of view.

#### Scenario: Narrowing one side retunes live
- **WHEN** the user sets the right field-of-view control to 60° on a window facing an obstruction to its right
- **THEN** the system SHALL, on the next recompute, treat the sun as out of view past 60° to the right and update the sun-window preview accordingly, with no options-flow edit

#### Scenario: Existing field of view preserved on upgrade
- **WHEN** an entry that previously stored `fov_left`/`fov_right` in options is loaded after the controls are introduced
- **THEN** each field-of-view control SHALL initialise from the stored value rather than the default

## MODIFIED Requirements

### Requirement: Sectioned options flow with live reload

The options flow SHALL group fields into collapsible sections (Window, Geometry, Sun, Sky, Movement, Manual override) and SHALL reload the entry on save so changes re-apply live. The field set and validation SHALL be driven by a single source (`SECTIONS` + per-field metadata) with per-field help text from a parallel `DOCS` mapping. Values that are tuned while observing behaviour — the sky shade/open thresholds and the left/right field-of-view spans — SHALL be exposed as live number-entity controls rather than as options-flow fields. The sky-threshold help text SHALL describe the thresholds on the sun-strength axis (higher = more direct sun; on the cloud path, `100 − cloud%`) so it matches the direction of the Sun strength sensor the user watches.

#### Scenario: Editing an option re-applies immediately
- **WHEN** the user changes a value in the options flow and saves
- **THEN** the entry SHALL reload and the new value SHALL take effect on the next recompute without a restart

#### Scenario: Every field shows help text
- **WHEN** the user opens any options section
- **THEN** each field SHALL display its help text describing the approximate, plain-language meaning of the value

#### Scenario: Field of view is not in the options flow
- **WHEN** the user opens the Sun section of the options flow
- **THEN** the left/right field-of-view spans SHALL NOT appear there, being exposed as number-entity controls instead

### Requirement: One meaningful input, defaults for the rest

Beyond the cover entity selection, the only configuration value that SHALL require human judgement is the window azimuth. Window height, glare distance, field of view, minimum elevation, sky thresholds, movement policy, and manual-override timeout SHALL all have sane defaults that produce reasonable behaviour unconfigured. Defaults for values exposed as live controls (sky thresholds, field of view) SHALL apply until the corresponding control is changed.

#### Scenario: Defaults produce working behaviour
- **WHEN** the user configures only the cover entity and window azimuth and leaves everything else at defaults
- **THEN** the integration SHALL adapt the cover using default geometry, field of view (`90°` each side), and policy values without further input
