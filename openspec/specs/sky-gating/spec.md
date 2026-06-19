# Sky Gating

## Purpose

Decide whether shading is warranted from a "sky" signal (outdoor brightness preferred over cloud cover), apply hysteresis to avoid toggling, restrict the gate to suppressing shading only, and optionally accept an indoor-lux comfort governor.

## Requirements

### Requirement: Brightness-first sky signal

The system SHALL decide whether shading is warranted from a "sky" signal, preferring a configured outdoor illuminance or irradiance sensor over a weather entity's cloud-cover percentage. When an outdoor brightness sensor is configured, the system SHALL use it; otherwise it SHALL fall back to the cloud-cover attribute of a configured weather entity; if neither is configured, shading geometry SHALL always be allowed to act when the sun is in the field of view.

#### Scenario: Outdoor lux sensor takes precedence
- **WHEN** both an outdoor illuminance sensor and a weather entity are configured
- **THEN** the system SHALL evaluate the sky gate from the illuminance sensor and ignore cloud cover

#### Scenario: Cloud-cover fallback
- **WHEN** no outdoor brightness sensor is configured but a weather entity is
- **THEN** the system SHALL evaluate the sky gate from the weather entity's cloud-cover percentage

### Requirement: Hysteresis dead-band on the sky gate

The system SHALL apply two separate thresholds (a "shade-when-brighter-than" and an "open-when-dimmer-than") with a dead-band between them, so that a signal hovering near a single value cannot toggle the cover. Once shading, the system SHALL keep shading until the signal crosses the open threshold; once open, it SHALL keep open until the signal crosses the shade threshold.

#### Scenario: Passing cloud inside the dead-band holds state
- **WHEN** the sky signal moves but stays within the dead-band between the open and shade thresholds
- **THEN** the system SHALL retain its previous shade/open state and SHALL NOT command the cover

### Requirement: Sky gate suppresses shading only

The sky gate SHALL only be able to *prevent* shading (keep the cover at the default/open position); it SHALL NOT, on its own, close a cover. The geometry engine remains the sole source of closing positions.

#### Scenario: Too dim to bother shading
- **WHEN** the sun is within the field of view but the sky signal is below the shade threshold
- **THEN** the system SHALL target the default open position with reason "not bright enough"

### Requirement: Optional indoor-lux comfort governor

The system MAY accept an optional indoor illuminance sensor that acts as a bounded governor: when the measured room brightness exceeds a configured cap, the system SHALL nudge the target more closed (within limits); when below a floor, it MAY nudge more open. The governor SHALL be daytime-gated and damped (bounded step per cycle plus the standard cooldown) to avoid oscillation, and SHALL never override the manual-override or sky gate.

#### Scenario: Bright room trims the cover further closed
- **WHEN** an indoor-lux sensor is configured and reports brightness above the configured cap during the day
- **THEN** the system SHALL reduce the target position by at most one bounded governor step and note "room-lux trim" in the reason

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
