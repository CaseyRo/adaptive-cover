# Cover Control

## Purpose

Govern when and how computed targets are sent to cover entities: a master switch gating active control, fixed-interval recompute, an anti-hum movement policy, and support for multiple covers per window.

## Requirements

### Requirement: Master switch gates active control

Each configured window SHALL expose a master switch. When the switch is on, the system SHALL actively command the window's cover entities toward the computed target. When the switch is off, the system SHALL NOT command the cover, while still computing and publishing the recommended position for observation.

#### Scenario: Control enabled drives the cover
- **WHEN** the master switch is on and a new target differs from the cover's position beyond the movement policy thresholds
- **THEN** the system SHALL call `cover.set_cover_position` toward the target

#### Scenario: Control disabled observes only
- **WHEN** the master switch is off
- **THEN** the system SHALL NOT command the cover, but the recommended-position sensor SHALL continue to update

### Requirement: Recompute on a fixed interval

The system SHALL recompute targets on a configurable interval (tick), not on every incoming sun attribute update, to bound how often slow covers can be asked to move.

#### Scenario: Periodic recompute
- **WHEN** the configured `interval` elapses
- **THEN** the system SHALL recompute the target for each window and apply the movement policy

### Requirement: Anti-hum movement policy

Before commanding a cover, the system SHALL apply a movement policy that prevents excessive, audible, or trivial motion: quantize the target to a configurable step; suppress moves smaller than a configurable minimum delta; and enforce a per-cover cooldown between commanded moves.

#### Scenario: Target is quantized to the step
- **WHEN** the raw target is 47% and the quantize step is 5%
- **THEN** the commanded position SHALL be 45%

#### Scenario: Sub-threshold change is suppressed
- **WHEN** the quantized target differs from the last commanded position by less than the minimum delta
- **THEN** the system SHALL NOT command the cover

#### Scenario: Cooldown defers a move
- **WHEN** a new qualifying target arrives within the cooldown window of the last commanded move
- **THEN** the system SHALL defer the command until the cooldown elapses

### Requirement: Multiple covers per window

A window MAY target more than one cover entity. The system SHALL apply the same computed target to all covers assigned to that window.

#### Scenario: Two blinds on one window move together
- **WHEN** a window is configured with two cover entities and the master switch is on
- **THEN** the system SHALL command both covers to the same target subject to the movement policy
