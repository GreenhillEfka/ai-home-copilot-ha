"""Contract bridge — imports Core contract classes for type-safe HA handling.

This module provides a single import surface for HA code to work with
Core contract dataclasses without direct filesystem coupling.

Usage:
    from .contracts_bridge import ProposalIntent, ActionIntent, HabitatModuleCommand
"""
from __future__ import annotations

import logging
from typing import Any, Mapping

# Core contracts are vendored into HA for type safety without runtime coupling.
# These stubs mirror the Core dataclass API surface used by HA handlers.

_LOGGER = logging.getLogger(__name__)

__all__ = [
    "ProposalIntent",
    "ActionIntent",
    "HabitatModuleCommand",
    "NeuronInput",
    "HabitatModuleEvent",
]


class ProposalIntent:
    """Suggestion-first outbound intent from Core → HA.

    Mirrors copilot_core.habitat.contracts.ProposalIntent API surface.
    """

    def __init__(
        self,
        module_id: str,
        action_type: str,
        title: str,
        summary: str,
        proposal_id: str | None = None,
        zone_id: str | None = None,
        target: Mapping[str, Any] | None = None,
        payload: Mapping[str, Any] | None = None,
        confidence: float = 0.0,
        explanation: str = "",
        autonomy_mode: str = "learning",
        approval_required: bool = True,
        requires_confirmation: bool = True,
        **metadata: Any,
    ) -> None:
        self.module_id = module_id
        self.action_type = action_type
        self.title = title
        self.summary = summary
        self.proposal_id = proposal_id or f"proposal:{id(self):x}"
        self.zone_id = zone_id
        self.target = dict(target or {})
        self.payload = dict(payload or {})
        self.confidence = max(0.0, min(1.0, confidence))
        self.explanation = explanation
        self.autonomy_mode = autonomy_mode
        self.approval_required = approval_required
        self.requires_confirmation = requires_confirmation
        self._metadata = dict(metadata)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProposalIntent":
        """Construct from Core webhook payload."""
        return cls(
            module_id=str(data.get("module_id", "unknown")),
            action_type=str(data.get("action_type", "unknown")),
            title=str(data.get("title", "")),
            summary=str(data.get("summary", "")),
            proposal_id=data.get("proposal_id"),
            zone_id=data.get("zone_id"),
            target=data.get("target", {}),
            payload=data.get("payload", {}),
            confidence=float(data.get("confidence", 0.0)),
            explanation=str(data.get("explanation", "")),
            autonomy_mode=str(data.get("autonomy_mode", "learning")),
            approval_required=bool(data.get("approval_required", True)),
            requires_confirmation=bool(data.get("requires_confirmation", True)),
        )

    def can_auto_execute(self) -> bool:
        """Return True only for explicitly autonomous, approval-free proposals."""
        return (
            self.autonomy_mode == "autonomous"
            and not self.approval_required
            and not self.requires_confirmation
        )

    def to_action_intent(self, *, approved: bool = False) -> "ActionIntent":
        """Derive ActionIntent from this proposal."""
        return ActionIntent(
            module_id=self.module_id,
            action_type=self.action_type,
            proposal_id=self.proposal_id,
            zone_id=self.zone_id,
            target=self.target,
            payload=self.payload,
            confidence=self.confidence,
            explanation=self.explanation,
            autonomy_mode=self.autonomy_mode,
            approval_required=self.approval_required,
            requires_confirmation=self.requires_confirmation,
            approved=approved,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "module_id": self.module_id,
            "action_type": self.action_type,
            "title": self.title,
            "summary": self.summary,
            "zone_id": self.zone_id,
            "target": self.target,
            "payload": self.payload,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "autonomy_mode": self.autonomy_mode,
            "approval_required": self.approval_required,
            "requires_confirmation": self.requires_confirmation,
        }


class ActionIntent:
    """Execution-capable intent derived from proposal or direct decision.

    Mirrors copilot_core.habitat.contracts.ActionIntent API surface.
    """

    def __init__(
        self,
        module_id: str,
        action_type: str,
        action_id: str | None = None,
        proposal_id: str | None = None,
        zone_id: str | None = None,
        target: Mapping[str, Any] | None = None,
        payload: Mapping[str, Any] | None = None,
        confidence: float = 0.0,
        explanation: str = "",
        autonomy_mode: str = "learning",
        approval_required: bool = True,
        requires_confirmation: bool = True,
        approved: bool = False,
        **metadata: Any,
    ) -> None:
        self.module_id = module_id
        self.action_type = action_type
        self.action_id = action_id or f"action:{id(self):x}"
        self.proposal_id = proposal_id
        self.zone_id = zone_id
        self.target = dict(target or {})
        self.payload = dict(payload or {})
        self.confidence = max(0.0, min(1.0, confidence))
        self.explanation = explanation
        self.autonomy_mode = autonomy_mode
        self.approval_required = approval_required
        self.requires_confirmation = requires_confirmation
        self.approved = approved

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ActionIntent":
        """Construct from Core webhook payload."""
        return cls(
            module_id=str(data.get("module_id", "unknown")),
            action_type=str(data.get("action_type", "unknown")),
            action_id=data.get("action_id"),
            proposal_id=data.get("proposal_id"),
            zone_id=data.get("zone_id"),
            target=data.get("target", {}),
            payload=data.get("payload", {}),
            confidence=float(data.get("confidence", 0.0)),
            explanation=str(data.get("explanation", "")),
            autonomy_mode=str(data.get("autonomy_mode", "learning")),
            approval_required=bool(data.get("approval_required", True)),
            requires_confirmation=bool(data.get("requires_confirmation", True)),
            approved=bool(data.get("approved", False)),
        )

    def can_execute(self) -> bool:
        """Respect suggest-first semantics unless approved or autonomous."""
        if self.autonomy_mode == "off":
            return False
        if self.requires_confirmation and not self.approved:
            return False
        if self.approval_required and not self.approved:
            return False
        if self.approved:
            return True
        return self.autonomy_mode == "autonomous"

    def to_module_command(self) -> "HabitatModuleCommand":
        """Convert to module-facing command."""
        return HabitatModuleCommand.from_action_intent(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "proposal_id": self.proposal_id,
            "module_id": self.module_id,
            "action_type": self.action_type,
            "zone_id": self.zone_id,
            "target": self.target,
            "payload": self.payload,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "autonomy_mode": self.autonomy_mode,
            "approved": self.approved,
        }


class HabitatModuleCommand:
    """Module-facing command emitted after proposal/action evaluation.

    Mirrors copilot_core.habitat.contracts.HabitatModuleCommand API surface.
    """

    def __init__(
        self,
        module_id: str,
        command_name: str,
        command_id: str | None = None,
        zone_id: str | None = None,
        proposal_id: str | None = None,
        action_id: str | None = None,
        target: Mapping[str, Any] | None = None,
        payload: Mapping[str, Any] | None = None,
        command_mode: str = "suggest",
        explanation: str = "",
        approved: bool = False,
        **metadata: Any,
    ) -> None:
        self.module_id = module_id
        self.command_name = command_name
        self.command_id = command_id or f"cmd:{id(self):x}"
        self.zone_id = zone_id
        self.proposal_id = proposal_id
        self.action_id = action_id
        self.target = dict(target or {})
        self.payload = dict(payload or {})
        self.command_mode = command_mode
        self.explanation = explanation
        self.approved = approved

    @classmethod
    def from_proposal_intent(cls, proposal: ProposalIntent) -> "HabitatModuleCommand":
        return cls(
            module_id=proposal.module_id,
            command_name=proposal.action_type,
            zone_id=proposal.zone_id,
            proposal_id=proposal.proposal_id,
            target=proposal.target,
            payload=proposal.payload,
            command_mode="suggest",
            explanation=proposal.explanation,
            approved=False,
            metadata={
                "title": proposal.title,
                "summary": proposal.summary,
                "confidence": proposal.confidence,
                "autonomy_mode": proposal.autonomy_mode,
            },
        )

    @classmethod
    def from_action_intent(cls, action: ActionIntent) -> "HabitatModuleCommand":
        return cls(
            module_id=action.module_id,
            command_name=action.action_type,
            zone_id=action.zone_id,
            proposal_id=action.proposal_id,
            action_id=action.action_id,
            target=action.target,
            payload=action.payload,
            command_mode="execute" if action.can_execute() else "suggest",
            explanation=action.explanation,
            approved=action.approved,
            metadata={
                "confidence": action.confidence,
                "autonomy_mode": action.autonomy_mode,
            },
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "HabitatModuleCommand":
        return cls(
            module_id=str(data.get("module_id", "unknown")),
            command_name=str(data.get("command_name", "unknown")),
            command_id=data.get("command_id"),
            zone_id=data.get("zone_id"),
            proposal_id=data.get("proposal_id"),
            action_id=data.get("action_id"),
            target=data.get("target", {}),
            payload=data.get("payload", {}),
            command_mode=str(data.get("command_mode", "suggest")),
            explanation=str(data.get("explanation", "")),
            approved=bool(data.get("approved", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "command_id": self.command_id,
            "module_id": self.module_id,
            "command_name": self.command_name,
            "zone_id": self.zone_id,
            "proposal_id": self.proposal_id,
            "action_id": self.action_id,
            "target": self.target,
            "payload": self.payload,
            "command_mode": self.command_mode,
            "explanation": self.explanation,
            "approved": self.approved,
        }


class NeuronInput:
    """Normalized input contract from HA event → Core neuron pipeline."""

    def __init__(
        self,
        module_id: str,
        signal: str,
        value: Any,
        zone_id: str | None = None,
        entity_id: str | None = None,
        confidence: float = 1.0,
        **metadata: Any,
    ) -> None:
        self.module_id = module_id
        self.signal = signal
        self.value = value
        self.zone_id = zone_id
        self.entity_id = entity_id
        self.confidence = max(0.0, min(1.0, confidence))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "NeuronInput":
        return cls(
            module_id=str(data.get("module_id", "unknown")),
            signal=str(data.get("signal", "")),
            value=data.get("value"),
            zone_id=data.get("zone_id"),
            entity_id=data.get("entity_id"),
            confidence=float(data.get("confidence", 1.0)),
        )


class HabitatModuleEvent:
    """Raw event from HA module → Core normalization."""

    def __init__(
        self,
        module_id: str,
        event_type: str,
        entity_id: str | None = None,
        zone_id: str | None = None,
        state: Any = None,
        **metadata: Any,
    ) -> None:
        self.module_id = module_id
        self.event_type = event_type
        self.entity_id = entity_id
        self.zone_id = zone_id
        self.state = state

    def to_neuron_input(self, **kwargs) -> NeuronInput:
        return NeuronInput(
            module_id=self.module_id,
            signal=self.event_type,
            value=self.state,
            zone_id=self.zone_id,
            entity_id=self.entity_id,
            **kwargs,
        )
