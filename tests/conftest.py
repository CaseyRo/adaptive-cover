"""Pytest configuration for Adaptive Cover (CDiT) tests.

Uses ``pytest-homeassistant-custom-component`` (PHACC). The
``enable_custom_integrations`` fixture lets HA discover and load this
integration from ``custom_components/`` during HA-dependent tests.

The pure geometry tests (``test_geometry.py``) import
``custom_components.adaptive_cover.geometry`` directly and do not touch
Home Assistant, so they run even without a running ``hass``.
"""

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(request):
    """Activate PHACC's ``enable_custom_integrations`` for HA-backed tests.

    Pure-geometry tests don't need (or have) a ``hass`` fixture, so we only
    pull in ``enable_custom_integrations`` when the test actually uses ``hass``.
    """
    if "hass" in request.fixturenames:
        request.getfixturevalue("enable_custom_integrations")
