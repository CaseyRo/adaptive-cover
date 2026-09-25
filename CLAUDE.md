# CLAUDE.md

Adaptive Cover (CDiT): a Home Assistant custom integration (`domain:
adaptive_cover`, HACS custom repo `CaseyRo/adaptive-cover`) that positions
blinds to keep direct sun off a room. One config entry per window. Built for a
single household and deliberately opinionated; README.md is the user-facing
description and CHANGELOG.md the release history.

## Commands

Tooling is `uv`. Set up with `./scripts/setup-devcontainer`.

| Task | Command |
|---|---|
| Tests (what CI runs) | `PYTHONPATH=. uv run --group test --python 3.13 pytest -q` |
| Lint (pre-commit: ruff + ruff-format) | `./scripts/lint` |
| Local HA with the integration loaded | `./scripts/develop` |

CI: `pytest.yml` (tests) and `validate.yml` (hassfest + HACS). Ruff config is
`.ruff.toml`; `CPY001` (copyright header) findings are pre-existing noise.

## Layout

`custom_components/adaptive_cover/`:
- `geometry.py`, `sky.py`: the math, free of HA imports so it unit-tests in
  isolation. Keep it that way.
- `coordinator.py`: the recompute loop per entry; stored in
  `entry.runtime_data`.
- `switch.py` (master + manual override), `sensor.py` (reason sensor +
  diagnostic outputs), `binary_sensor.py`, `number.py` (four live controls:
  sun-strength shade-above/open-below, field-of-view left/right).
- `config_flow.py`: config + options flow. The options flow is an
  `OptionsFlowWithReload`, so the minimum HA is 2025.8 (`hacs.json`).

Versions: `manifest.json` `version` is the release version; keep
`pyproject.toml` in step.

## Planning

OpenSpec (`openspec/`, schema `spec-driven`). Long-lived specs live in
`openspec/specs/`; completed changes in `openspec/changes/archive/`. The
`/opsx:*` commands and `openspec-*` skills are installed at user scope, not in
this repo.
