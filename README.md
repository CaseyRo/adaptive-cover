# Adaptive Cover (CDiT)

**Sun-tracking blinds for Home Assistant that you can actually set up in a minute — and debug at a glance.**

Adaptive Cover positions your blinds automatically to keep direct sun off the room: it reads the sun from Home Assistant, works out where the light is falling, and moves the cover just enough to hold the sunlight back. When the sun moves on, the blind opens back up. It feels like magic — and unlike most adaptive-cover setups, it tells you *why* it did what it did, and it never fights you when you move the blind yourself.

> **Philosophy:** one input that needs thought (which way the window faces), sane defaults for everything else, a plain-language reason for every decision, and a blind that always yields to the human holding it. Built by the same hands as our [Adaptive Lighting (CDiT) fork](https://github.com/CaseyRo/adaptive-lighting), and deliberately opinionated for a single household.

---

## What it does

```
        ╲  sunlight                  Home Assistant already knows where the
         ╲                           sun is (sun.sun). You tell it which way
  top ────╲──────────  ▲             the window faces. That's the only input
  │ blind   ╲          │             that needs a human.
  │ covers   ╲         │ height
  ├───────────╲──────  ┤  ← the blind drops to exactly here, so direct
  │ open strip  ╲      │     sun reaches no further than your chosen line
  floor ─────────╲────────────────
  wall  |◄─ glare ─►|  ← sunlight stops here; the room beyond stays shaded
            distance
```

- **Limits how far sun reaches into the room.** You pick a line (the *glare distance*); the blind keeps direct sun from crossing it. Small line = cool, shaded room. Large line = bright and sunny with the view kept open.
- **Only acts when it's actually bright.** Point it at an outdoor light/irradiance sensor and it shades only when the sun is genuinely strong — no sensor? It falls back to your weather integration's cloud cover.
- **Never hums or chases.** Covers are slow and loud, so it snaps to sensible steps, ignores trivial changes, and waits between moves.
- **Tells you why.** Every window gets a sensor whose state is the position and whose attributes read like a sentence: *"shading 45% — sun in view, clear enough."*
- **Yields to you (the WAF feature).** Move a blind yourself — in the app, on the wall, in Apple Home — and Adaptive Cover notices, backs off, and stops touching it. It quietly takes over again the next morning.

## What it is — and isn't (v1)

| ✅ In scope | ❌ Not in scope (yet) |
|---|---|
| Vertical / "simple" blinds that open↔close by position | Venetian/tilt slats, awnings/horizontal covers |
| One window, one (or several) covers | A climate/heating strategy engine |
| Sun-geometry shading + brightness gating | An "all blinds" aggregation hub |
| Manual-override that respects you | Migrating from other adaptive-cover setups |

It is **not** a drop-in replacement for [`basbruss/adaptive-cover`](https://github.com/basbruss/adaptive-cover) — that's a much broader integration. This one trades breadth for being small, explainable, and forgiving.

## Installation

### HACS — custom repository (recommended)

This integration is distributed as a **HACS custom repository** (it is not in the HACS default list). Adding it is a one-time step:

1. Make sure [HACS](https://hacs.xyz) is installed.
2. In Home Assistant: **HACS** → top-right **⋮** → **Custom repositories**.
3. **Repository:** `https://github.com/CaseyRo/adaptive-cover` — **Type:** `Integration` — click **Add**.
4. Search HACS for **Adaptive Cover (CDiT)**, open it, and click **Download**.
5. **Restart Home Assistant.**
6. **Settings → Devices & Services → Add Integration →** search **Adaptive Cover**.

HACS then notifies you of updates like any other integration.

### Manual install

1. Download the latest release, or copy this repo.
2. Copy `custom_components/adaptive_cover/` into your Home Assistant `config/custom_components/` folder.
3. **Restart Home Assistant**, then add it via **Settings → Devices & Services → Add Integration → Adaptive Cover**.

## Quick start

1. **Install it** (see Installation above), then **Settings → Devices & Services → Add Integration → Adaptive Cover.** Fill the short form: a name, the cover(s), and **which way the window faces** — pick the nearest of 16 compass points, then nudge ±20° if it sits between them. That's a working window.
2. **Tune later if you want (optional).** Open the entry's **Configure** for the rest — height, glare distance, brightness thresholds, movement, override — all with sane defaults until you touch them.
3. **Check the preview.** The window's sensor shows *"direct sun enters ~09:40–13:20 today"* — if that looks wrong (e.g. "no direct sun expected" for your sunny south window), your azimuth is off. Fix it now, no waiting for the afternoon.
4. **Flip the master switch on** when you're happy. Watch the reason sensor for a day before you forget it exists.

## The two things people get wrong everywhere else

**"How cloudy is too cloudy?"** — 60% bugs you, 80% bugs your neighbour. So we don't make you guess in a setup box: the brightness thresholds are **live slider entities** you nudge on an annoying day while watching the blind react, and there's a **dead-band** so a single drifting cloud can't make the blind flap up and down. Better still, give it an **outdoor light sensor** and the question becomes "is it actually bright?" instead of "what's the forecast."

**"Which way does my window face?"** — the one input that needs a human. Just **pick the nearest of 16 compass points and nudge ±20°** — South, then +8° if it leans a bit west. It's an approximation, not a survey, and the *"sun enters ~HH:MM"* preview tells you immediately if you got the direction wrong. (No fiddly maps, no phone-compass calibration.)

## Entities (per window)

| Entity | What it's for |
|---|---|
| `switch.adaptive_cover_<window>` | Master on/off. On = it drives the blind. Off = it just *shows* what it would do. |
| `sensor.adaptive_cover_<window>` | The brain, readable: position + `reason`, sun angles, the active sky signal, manual status, and today's sun-entry preview. |
| `number.*` (a few) | Live-tunable brightness thresholds, so calibrating is a slider, not a re-setup. |

Two everyday entities per window — not ten.

### Diagnostic sensors (the "how the magic worked" set)

Every explanatory value is *also* its own entity, so you can graph a day of
decisions instead of squinting at attributes. They live under **Diagnostic** on
the device page (hidden from auto-dashboards) and update on every recompute:

| Entity | What it shows |
|---|---|
| `… profile angle` | γ, the projected sun angle the geometry actually uses (°). Unknown when geometry didn't run (sun down / out of view). |
| `… sun azimuth` / `… sun elevation` | The sun position this window computed with (°). |
| `… sky brightness` *or* `… cloud cover` | The live sky signal — created only for the source you configured, in that source's own unit, and read **all day** (not just when shading is wanted). |
| `… sun enters` / `… sun leaves` / `… sun peak` | Today's direct-sun window as real timestamps ("in 3 hours"). |
| `binary_sensor.… sun in view` | On while the sun is inside the window's field of view — the trace of *when* the geometry considered the sun relevant. |

Stack `profile angle` + `sun in view` + the status sensor's position in one
history graph and the whole day explains itself.

## Debugging is reading, not guessing

When someone asks *"why is the blind half-down on a sunny day?"*, open the sensor:

```
sensor.adaptive_cover_living_room
  state: 45
  reason: "shading 45% — sun in view, clear enough"
  profile_angle: 22°
  sun_azimuth: 167°   in_fov: true
  sun_elevation: 31°
  sky: "clear (38% cloud < shade-below 50%)"
  manual_override: false
  next_eval: in 2 min
```

No mental trig. The integration already did the explaining.

## Credits & inspiration

This project stands on a lot of good prior work, and we want to name it:

- **[`basbruss/adaptive-cover`](https://github.com/basbruss/adaptive-cover)** — the reference HACS integration for adaptive covers. It's broader and more configurable than this one; if you want tilt, awnings, climate strategies, or an aggregation hub, go there. Adaptive Cover (CDiT) is the deliberately-minimal cousin.
- **The original Home Assistant community template sensor** — *["Automatic Blinds / Sunscreen control based on the sun's position"](https://community.home-assistant.io/t/automatic-blinds-sunscreen-control-based-on-sun-platform/)* — the forum post that first worked out the sun-to-blind geometry that everything here (and `basbruss`) builds on.
- **[Adaptive Lighting](https://github.com/basnijholt/adaptive-lighting)** by [@basnijholt](https://github.com/basnijholt) and our **[Adaptive Lighting (CDiT) fork](https://github.com/CaseyRo/adaptive-lighting)** — the architectural template for this integration: the per-entry master switch, manual-control detection, the `const.py → config flow` pattern, and the "fewer knobs, opinionated for one household" philosophy. If you like this, you'll like that.

Geometry, control loop, and the explainability/WAF design here are original to this project; the gratitude for the ideas above is not.

## License

**Apache-2.0** — matching the [Adaptive Lighting (CDiT)](https://github.com/CaseyRo/adaptive-lighting) scaffold this integration derives its structure from. The projects credited above are acknowledged as inspiration; their own licenses (`basbruss/adaptive-cover` is MIT) govern their respective code.
