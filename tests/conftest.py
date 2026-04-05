"""Compatibility test package for module import compatibility.

Older tests import from `tests.conftest` while the main fixtures live in
`custom_components/copilot_ha/tests/conftest.py`.
"""

from custom_components.copilot_ha.tests.conftest import *  # noqa: F401,F403
