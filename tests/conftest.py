"""Pytest configuration for PilotSuite Styx tests.

Note: Path setup and HA stubs are handled by the root conftest.py.
Do NOT add custom_components/copilot_ha directly to sys.path here —
it causes `import core` to find copilot_ha/core/ instead of the
project root core/ package.
"""

pytest_plugins = []
