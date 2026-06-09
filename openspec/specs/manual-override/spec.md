# Manual Override

## Purpose

Detect human-initiated cover movement robustly despite slow cover travel, back off from commanding a manually controlled cover, and automatically (or on demand) reset manual control.

## Requirements

### Requirement: Detect human-initiated movement with travel tolerance

The system SHALL detect when a cover is moved by someone other than the integration and mark that cover "manually controlled." Detection SHALL be robust to the slow travel of covers: the system SHALL ignore transitional states (`opening` / `closing`) and intermediate positions produced by its own in-flight command, and SHALL only treat a cover as manually controlled when it settles at a position that differs from the integration's last commanded position by more than a configurable tolerance band, via a state change the integration did not originate.

#### Scenario: Settled at an uncommanded position
- **WHEN** a cover settles (state `open`/`closed`, not moving) at a position differing from the last commanded position by more than the tolerance band, from a context the integration did not create
- **THEN** the system SHALL mark that cover manually controlled and SHALL stop adapting it

#### Scenario: Own command travel is not mistaken for manual control
- **WHEN** the integration commands a position and the cover reports transitional positions and `opening`/`closing` states while travelling toward it
- **THEN** the system SHALL NOT mark the cover manually controlled

#### Scenario: Settling within tolerance is not manual
- **WHEN** a cover settles within the tolerance band of the last commanded position
- **THEN** the system SHALL treat the position as its own and SHALL NOT mark it manually controlled

### Requirement: Back off while manually controlled

While a cover is marked manually controlled, the system SHALL NOT command it, regardless of the computed target, until control is reset.

#### Scenario: No adaptation during manual control
- **WHEN** a cover is manually controlled and a new target is computed
- **THEN** the system SHALL skip commanding that cover and SHALL reflect the manual state in the reason sensor

### Requirement: Automatic reset of manual control

The system SHALL automatically return a manually controlled cover to automatic control after a configurable timeout, and SHALL also reset manual control at the next sunrise. A service SHALL be provided to reset manual control on demand.

#### Scenario: Timeout returns control
- **WHEN** the configured manual-control timeout elapses for a cover
- **THEN** the system SHALL clear the manual flag and resume adaptation on the next recompute

#### Scenario: Sunrise resets control
- **WHEN** the sun rises
- **THEN** the system SHALL clear manual control for all covers so each day starts in automatic mode

#### Scenario: Manual reset service
- **WHEN** the reset service is called for a window or cover
- **THEN** the system SHALL clear manual control immediately and resume adaptation
