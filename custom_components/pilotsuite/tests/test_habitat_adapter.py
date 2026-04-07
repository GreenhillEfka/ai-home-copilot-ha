from custom_components.copilot_ha.habitat_adapter import (
    build_call_service_forward_item,
    build_state_changed_forward_item,
    normalize_received_webhook_payload,
)


def test_build_state_changed_forward_item_attaches_normalized_contracts():
    item = build_state_changed_forward_item(
        item_id="evt-1",
        ts="2026-03-18T20:00:00+00:00",
        entity_id="light.living_room_main",
        old_state="off",
        new_state="on",
        zone_ids=["zone:living"],
        state_attributes={"brightness_pct": 65},
        neuron_tags=["ambient_need"],
        occurred_at_ms=1710000000000,
    )

    assert item["adapter"]["contract_version"] == "ha.input.v1"
    assert item["habitat_event"]["module_id"] == "light"
    assert item["habitat_event"]["zone_id"] == "zone:living"
    assert item["neuron_input"]["signal"] == "state_changed"
    assert item["neuron_input"]["metadata"]["state_attributes"]["brightness_pct"] == 65


def test_build_call_service_forward_item_attaches_neuron_input():
    item = build_call_service_forward_item(
        item_id="evt-2",
        ts="2026-03-18T20:05:00+00:00",
        domain="light",
        service="turn_on",
        entity_ids=["light.living_room_main"],
        zone_ids=["zone:living"],
        occurred_at_ms=1710000005000,
    )

    assert item["habitat_event"]["event_type"] == "call_service"
    assert item["neuron_input"]["signal"] == "light.turn_on"
    assert item["neuron_input"]["metadata"]["entity_ids"] == ["light.living_room_main"]


def test_normalize_received_webhook_payload_builds_proposal_and_command():
    payload = normalize_received_webhook_payload(
        "suggestion",
        {
            "title": "Wohnzimmer dimmen",
            "summary": "Abends das Hauptlicht dimmen.",
            "entity_id": "light.living_room_main",
            "service": "light.turn_on",
            "service_data": {"brightness_pct": 35},
            "zone_ids": ["zone:living"],
            "confidence": 0.84,
        },
    )

    assert payload["adapter"]["direction"] == "core_to_homeassistant"
    assert payload["proposal_intent"]["module_id"] == "light"
    assert payload["proposal_intent"]["action_type"] == "light.turn_on"
    assert payload["module_command"]["command_mode"] == "suggest"
    assert payload["module_command"]["target"]["entity_id"] == "light.living_room_main"
