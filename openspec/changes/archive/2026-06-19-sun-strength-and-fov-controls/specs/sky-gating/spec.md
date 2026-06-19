## ADDED Requirements

### Requirement: Single user-facing tuning axis ("sun strength")

The sky gate SHALL present a single user-facing axis for tuning, named **sun strength**, on which higher always means more direct sun. The shade and open thresholds SHALL be defined on this axis (shade when sun strength is at/above the shade threshold; open when at/below the open threshold), regardless of which underlying signal is active. For a brightness sensor, sun strength SHALL equal the raw sensor value; for the weather cloud-cover fallback, sun strength SHALL equal `100 − cloud%`. The value the thresholds compare against SHALL be observable by the user (see the `explainability` capability) so the dial and the watched number move in the same direction.

#### Scenario: Cloud path reads on the same direction as the thresholds
- **WHEN** a weather entity reports `cloud_coverage` of 25%
- **THEN** the sun-strength value SHALL be 75, and with a shade threshold of 60 the gate SHALL allow shading (75 ≥ 60)

#### Scenario: Brightness path reads on the same direction as the thresholds
- **WHEN** an outdoor brightness sensor reports a value of 75 in its own unit
- **THEN** the sun-strength value SHALL be 75 and the same threshold comparison SHALL apply

### Requirement: Reason text expressed on the sun-strength axis

When the sky gate explains a decision, the reason fragment SHALL express the compared value and threshold on the sun-strength axis (e.g. "sun strength 28 ≤ open-below 30"), not on a raw-input axis such as cloud cover, so the explanation matches the direction of the threshold the user set.

#### Scenario: Non-action reason names the sun-strength comparison
- **WHEN** the sun is in the field of view but the sun-strength value is below the shade threshold
- **THEN** the reason fragment SHALL state the sun-strength value and the open/shade threshold it was compared against (e.g. "not bright enough — sun strength 28 ≤ 30")
