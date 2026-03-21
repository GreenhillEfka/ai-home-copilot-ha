# DEPRECATION NOTICE — PilotClaw Phase 1 Cleanup
# File: custom_components/copilot_ha/entity_zone_sorter.py
# Status: DEPRECATED — do not use in new code
# 
# Use THIS file instead:
#   custom_components/copilot_ha/habitus_entity_sorting.py
#
# Migration:
#   OLD: from entity_zone_sorter import sort_entity_to_zone
#   NEW: from habitus_entity_sorting import sort_entity_to_zone
#
# Reason: habitus_entity_sorting.py has enhanced confidence scoring
#         and supersedes entity_zone_sorter.py (added via PR #148)
#
# Will be REMOVED in a future release after migration period.
