"""Legacy compatibility shim for PilotSuite HA.

Keeps old copilot_ha references working by forwarding to the current
pilotsuite integration package.
"""

from custom_components.pilotsuite import *  # noqa: F403,F401
from custom_components.pilotsuite import async_setup, async_setup_entry, async_unload_entry
