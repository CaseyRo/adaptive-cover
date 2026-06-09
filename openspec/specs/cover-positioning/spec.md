# Cover Positioning

## Purpose

Compute target cover positions from sun geometry (the Model A floor-penetration model), gating shading by field of view and sun elevation, applying sunset behaviour, and clamping every target to user-defined limits.

## Requirements

### Requirement: Model A target position from sun geometry

The system SHALL compute a target cover position for a vertical/simple cover using the Model A floor-penetration model, reading solar azimuth and elevation from `sun.sun` and combining them with the window's azimuth, height, and configured glare distance.

The profile (vertical shadow) angle SHALL be computed as `γ = atan( tan(elevation) / cos(azimuth − window_azimuth) )`, and the open position as `position% = clamp( glare_distance · tan(γ) / window_height , min_position, max_position ) · 100`, where 100% is fully open.

#### Scenario: High sun is shaded less than low sun
- **WHEN** the sun is within the window's field of view and high in the sky (large profile angle)
- **THEN** the computed position SHALL be more open than for the same window when the sun is low (small profile angle), because low sun penetrates further into the room

#### Scenario: Larger glare distance opens the cover more
- **WHEN** two windows share all parameters except `glare_distance`
- **THEN** the window with the larger `glare_distance` SHALL be commanded to a more-open position, since direct sun is permitted to reach further across the floor

### Requirement: Field-of-view gate

The system SHALL only apply sun-shading geometry when the solar azimuth lies within the window's field of view, defined by `window_azimuth` and the configurable `fov_left` / `fov_right` spans. When the sun is outside the field of view, the system SHALL treat the window as not sunlit and resolve to the default/open position.

#### Scenario: Sun behind the building leaves the cover open
- **WHEN** the solar azimuth is outside `[window_azimuth − fov_left, window_azimuth + fov_right]` (wrapping at 360°)
- **THEN** the system SHALL set the reason to "not in field of view" and target the default open position

### Requirement: Sun elevation gating

The system SHALL not apply shading geometry when the sun is below a configurable minimum elevation (sun is down or grazing the horizon), to avoid extreme `tan(γ)` values and night-time activity.

#### Scenario: Sun below minimum elevation
- **WHEN** the solar elevation is below `min_elevation`
- **THEN** the system SHALL not compute a shading position and SHALL resolve to the day/sunset default instead

### Requirement: Position after sunset

The system SHALL apply a configurable `position_after_sunset` once the sun is down, independent of the geometry calculation.

#### Scenario: Cover returns to its night position at sunset
- **WHEN** the sun transitions below the horizon
- **THEN** the system SHALL target `position_after_sunset` (default: fully open) and set the reason to "after sunset"

### Requirement: Min/max position clamps

The system SHALL clamp every computed target to the configured `min_position` and `max_position` so a cover is never driven past user-defined limits.

#### Scenario: Computed value below the minimum is clamped
- **WHEN** the geometry yields a target below `min_position`
- **THEN** the commanded target SHALL be `min_position` and the reason SHALL note the clamp
