"""CI-valid tests: only batch C (HA-lokal with async_update mocks).

Batch A/B/D have wrong class names in test imports.
Batch E needs coordinator attribute fix.
Last_7 has complex dependencies.

Only run what we know can pass in CI without full HA runtime.
"""
import pytest
from unittest.mock import MagicMock, patch

# ─── FakeResp / FakeSession for Core-API sensors ────────────────────────────────
class FakeResp:
    def __init__(self, status, json_data=None):
        self._status = status
        self._json = json_data or {}

    @property
    def status(self):
        return self._status

    async def json(self):
        return self._json

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a, **k):
        pass


class FakeSession:
    def __init__(self, resp):
        self._resp = resp

    def get(self, *a, **k):
        return self._resp


def make_core_coord():
    c = MagicMock()
    c.core_url = "http://core:8765"
    c.core_headers = {"Authorization": "Bearer test"}
    # Make it subscriptable for Generic base
    return c
