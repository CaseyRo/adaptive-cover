## ADDED Requirements

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
