from __future__ import annotations

from custom_components.copilot_ha.habitus_zones_store_v2 import (
    default_module_overrides_for_zone,
    evaluate_action_policy,
    infer_module_id_for_action,
    resolve_module_override_for_action,
)


def test_default_zone_policy_is_suggestion_first():
    overrides = default_module_overrides_for_zone("zone:wohnzimmer", "living")
    light = overrides["light"]

    assert light["autonomy_mode"] == "learning"
    assert light["direct_execution_enabled"] is False
    assert light["approval_required"] is True


def test_learning_mode_requires_explicit_styx_instruction():
    overrides = default_module_overrides_for_zone("zone:wohnzimmer", "living")
    light = resolve_module_override_for_action("zone:wohnzimmer", "living", "light", overrides)
    decision = evaluate_action_policy("light", light)

    assert decision["execution_state"] == "awaiting_styx_instruction"
    assert decision["eligible_for_execution"] is False
    assert "learning_mode_requires_styx_instruction" in decision["blocked_reasons"]


def test_autonomous_mode_can_be_ready_without_instruction():
    overrides = default_module_overrides_for_zone(
        "zone:kueche",
        "kitchen",
        {
            "music": {
                "enabled": True,
                "autonomy_mode": "autonomous",
                "direct_execution_enabled": True,
                "approval_required": False,
            }
        },
    )
    music = resolve_module_override_for_action("zone:kueche", "kitchen", "music", overrides)
    decision = evaluate_action_policy("music", music)

    assert decision["execution_state"] == "ready_for_execution"
    assert decision["eligible_for_execution"] is True
    assert decision["decision_source"] == "policy_autonomous"


def test_off_mode_stays_blocked_even_with_instruction():
    decision = evaluate_action_policy(
        "tv",
        {
            "enabled": True,
            "autonomy_mode": "off",
            "direct_execution_enabled": True,
            "approval_required": False,
        },
        explicit_styx_instruction=True,
    )

    assert decision["execution_state"] == "blocked"
    assert decision["eligible_for_execution"] is False
    assert "autonomy_off" in decision["blocked_reasons"]


def test_cover_actions_remain_unmapped_policy_gap():
    module_id = infer_module_id_for_action(
        {
            "domain": "cover",
            "entity_id": "cover.wohnzimmer_blinds",
            "suggested_service": "close_cover",
        }
    )
    decision = evaluate_action_policy(module_id, None, explicit_styx_instruction=True)

    assert module_id is None
    assert decision["execution_state"] == "blocked"
    assert "module_unmapped" in decision["blocked_reasons"]
    assert "zone_policy_unresolved" in decision["blocked_reasons"]
