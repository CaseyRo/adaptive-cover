# Explainability

## Purpose

Expose, per window, a reason sensor whose state is the recommended position and whose attributes explain the decision; ensure it computes regardless of control state; and provide a sun-window preview for setup verification.

## Requirements

### Requirement: Per-window reason sensor

Each window SHALL expose a sensor whose state is the recommended cover position (0–100) and whose attributes explain the decision. Attributes SHALL include at minimum: a human-readable `reason`, the profile angle, solar azimuth and elevation, whether the sun is in the field of view, the active sky signal and its value, the manual-override status, and the timestamp of the next scheduled evaluation.

#### Scenario: Reason explains a shading decision
- **WHEN** the system shades a window because the sun is in view and the sky is bright enough
- **THEN** the sensor state SHALL equal the recommended position and the `reason` attribute SHALL describe it (e.g. "shading 45% — sun in view, clear enough")

#### Scenario: Reason explains a non-action
- **WHEN** the system leaves a window open because the sky signal is below the shade threshold
- **THEN** the `reason` attribute SHALL name the cause and the value compared (e.g. "open — too cloudy (cloud 72% ≥ open-above 70%)")

### Requirement: Sensor computes regardless of control state

The reason sensor SHALL update on every recompute whether or not the master switch is on, so the recommended position can be observed and trusted before active control is enabled.

#### Scenario: Observation with control disabled
- **WHEN** the master switch is off
- **THEN** the reason sensor SHALL still publish the position the system *would* command, with reason text intact

### Requirement: Sun-window preview for setup verification

The system SHALL expose, per window, a preview of when direct sun is expected to enter and leave the window today (an approximate start/end time and peak), derived from the same geometry engine, so a user can confirm the window azimuth was entered correctly without waiting for the event.

#### Scenario: Preview confirms a plausible azimuth
- **WHEN** a window azimuth and field of view are configured such that the sun enters during the day
- **THEN** the preview SHALL report an approximate entry and exit time and a peak time for today

#### Scenario: Preview flags an implausible azimuth
- **WHEN** the configured azimuth and field of view are such that the sun never enters the window today
- **THEN** the preview SHALL indicate that no direct sun is expected, signalling a likely setup error
