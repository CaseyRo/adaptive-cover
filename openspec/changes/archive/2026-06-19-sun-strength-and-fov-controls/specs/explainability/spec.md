## ADDED Requirements

### Requirement: Sun-strength diagnostic sensor

Each window SHALL expose a **Sun strength** diagnostic sensor whose value is exactly the value the sky gate compares its thresholds against: the raw outdoor-brightness value on the brightness path, or `100 − cloud%` on the weather cloud-cover path. The sensor SHALL be created whenever any sky signal source (a brightness sensor or a weather entity) is configured, and SHALL NOT be created when none is. When the configured source is momentarily unavailable, the sensor SHALL report unknown rather than a stale value. Its unit SHALL be fixed per entity at setup (the source sensor's own unit on the brightness path; `%` on the cloud path). It SHALL carry the diagnostic entity category and update on every recompute. This sensor SHALL replace the former raw `Sky brightness` sensor (which reported the same value on the brightness path); the raw **Cloud cover** sensor SHALL remain as weather telemetry.

#### Scenario: Sun strength rises as skies clear (cloud path)
- **WHEN** a weather entity is the active sky signal and its cloud coverage falls from 70% to 20%
- **THEN** the Sun strength sensor SHALL rise from 30 to 80, moving the same direction as the shade/open thresholds

#### Scenario: Sun strength equals the brightness value (brightness path)
- **WHEN** an outdoor brightness sensor is the active sky signal
- **THEN** the Sun strength sensor SHALL report that sensor's value in its own unit, and no separate `Sky brightness` sensor SHALL exist

#### Scenario: No sky signal configured
- **WHEN** neither a brightness sensor nor a weather entity is configured
- **THEN** no Sun strength sensor SHALL be created for that window

## MODIFIED Requirements

### Requirement: Per-window reason sensor

Each window SHALL expose a sensor whose state is the recommended cover position (0–100) and whose attributes explain the decision. Attributes SHALL include at minimum: a human-readable `reason`, the profile angle, solar azimuth and elevation, whether the sun is in the field of view, the active sky signal and its value, the manual-override status, and the timestamp of the next scheduled evaluation. Where the reason refers to the sky decision, it SHALL express the compared value and threshold on the sun-strength axis (higher = more direct sun), not on a raw-input axis such as cloud cover.

#### Scenario: Reason explains a shading decision
- **WHEN** the system shades a window because the sun is in view and the sky is bright enough
- **THEN** the sensor state SHALL equal the recommended position and the `reason` attribute SHALL describe it (e.g. "shading 45% — sun in view, sun strength 72 ≥ 60")

#### Scenario: Reason explains a non-action
- **WHEN** the system leaves a window open because the sun-strength value is below the shade threshold
- **THEN** the `reason` attribute SHALL name the cause and the sun-strength value compared (e.g. "open — not bright enough, sun strength 28 ≤ open-below 30")
