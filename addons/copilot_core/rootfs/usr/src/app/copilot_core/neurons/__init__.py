"""Neurons module for PilotSuite neural orchestration.

This module provides the base classes and implementations for:
- Context Neurons: Objective environmental factors (presence, time, light, weather)
- State Neurons: Smoothed, inertial state values (energy, stress, routine)
- Mood Neurons: Aggregated outputs that trigger suggestions

The neural model follows:
    State (objective) → Neuron (evaluates aspect) → Mood (aggregates meaning) → Decision
"""
from .base import (
    BaseNeuron, NeuronState, NeuronConfig, NeuronType, MoodType,
    ContextNeuron, StateNeuron, MoodNeuron
)
from .context import (
    PresenceNeuron, TimeOfDayNeuron, LightLevelNeuron, WeatherNeuron,
    create_context_neuron, CONTEXT_NEURON_CLASSES
)
from .state import (
    EnergyLevelNeuron, StressIndexNeuron, RoutineStabilityNeuron,
    SleepDebtNeuron, AttentionLoadNeuron, ComfortIndexNeuron,
    create_state_neuron, STATE_NEURON_CLASSES
)
from .mood import (
    RelaxMoodNeuron, FocusMoodNeuron, ActiveMoodNeuron, SleepMoodNeuron,
    AwayMoodNeuron, AlertMoodNeuron, SocialMoodNeuron, RecoveryMoodNeuron,
    create_mood_neuron, MOOD_NEURON_CLASSES
)

__all__ = [
    # Base classes
    "BaseNeuron",
    "NeuronState", 
    "NeuronConfig",
    "NeuronType",
    "MoodType",
    "ContextNeuron",
    "StateNeuron",
    "MoodNeuron",
    # Context neurons
    "PresenceNeuron",
    "TimeOfDayNeuron",
    "LightLevelNeuron",
    "WeatherNeuron",
    "create_context_neuron",
    "CONTEXT_NEURON_CLASSES",
    # State neurons
    "EnergyLevelNeuron",
    "StressIndexNeuron",
    "RoutineStabilityNeuron",
    "SleepDebtNeuron",
    "AttentionLoadNeuron",
    "ComfortIndexNeuron",
    "create_state_neuron",
    "STATE_NEURON_CLASSES",
    # Mood neurons
    "RelaxMoodNeuron",
    "FocusMoodNeuron",
    "ActiveMoodNeuron",
    "SleepMoodNeuron",
    "AwayMoodNeuron",
    "AlertMoodNeuron",
    "SocialMoodNeuron",
    "RecoveryMoodNeuron",
    "create_mood_neuron",
    "MOOD_NEURON_CLASSES",
]