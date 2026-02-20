# Next Task: Multi-User Preference Learning

## Status: READY TO START

## Scope
- Learn preferences per user, not just global
- User identification via HA person entities
- Per-user mood profiles
- Per-user habit patterns
- Privacy: User consent before learning

## Files to create/modify
- Core: `copilot_core/preference/` - preference storage per user
- HA: `custom_components/ai_home_copilot/preference_context.py`
- API: `GET /api/v1/preferences/{user_id}`
- API: `POST /api/v1/preferences/{user_id}/learn`

## Model: qwen3-coder-next:cloud (via Ollama)

## Estimated complexity: Medium (2-3 hours)
