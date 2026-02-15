"""State Neurons - Smoothed, inertial state values.

State neurons maintain smoothed values that change slowly over time.
They represent internal state derived from context over time:
- EnergyLevel
- StressIndex
- RoutineStability
- SleepDebt
- AttentionLoad
- ComfortIndex
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
from collections import deque

from .base import BaseNeuron, NeuronConfig, NeuronType, StateNeuron

_LOGGER = logging.getLogger(__name__)


class EnergyLevelNeuron(StateNeuron):
    """Evaluates overall energy level based on activity and time.
    
    Inputs:
        - Recent activity level
        - Time since last rest
        - Day/night cycle alignment
        - Motion sensor activity
    
    Output: 0.0 (exhausted) to 1.0 (energetic)
    """
    
    def __init__(self, config: NeuronConfig, history_hours: int = 24):
        super().__init__(config)
        self.history_hours = history_hours
        self._activity_history: deque = deque(maxlen=history_hours * 6)  # 10-min intervals
    
    def evaluate(self, context: Dict[str, Any]) -> float:
        """Evaluate energy level from activity history."""
        states = context.get("states", {})
        time_context = context.get("time", {})
        
        # Get recent activity
        activity_level = 0.0
        
        # Check motion sensors
        motion_entities = [
            eid for eid in self.config.entity_ids
            if "motion" in eid.lower() or "binary_sensor" in eid
        ]
        
        active_motion = sum(
            1 for eid in motion_entities
            if states.get(eid, {}).get("state") == "on"
        )
        
        if motion_entities:
            activity_level = active_motion / len(motion_entities)
        
        # Time-based energy (lower at night)
        hour = datetime.now().hour
        if 6 <= hour < 10:  # Morning
            time_energy = 0.7
        elif 10 <= hour < 14:  # Midday
            time_energy = 0.9
        elif 14 <= hour < 18:  # Afternoon
            time_energy = 0.6
        elif 18 <= hour < 22:  # Evening
            time_energy = 0.4
        else:  # Night
            time_energy = 0.2
        
        # Combine with smoothing
        energy = 0.4 * activity_level + 0.6 * time_energy
        
        return round(energy, 3)
    
    @classmethod
    def from_config(cls, config: NeuronConfig) -> "EnergyLevelNeuron":
        history = config.weights.get("history_hours", 24)
        return cls(config, history_hours=history)


class StressIndexNeuron(StateNeuron):
    """Evaluates stress level based on various indicators.
    
    Inputs:
        - Calendar load (upcoming events)
        - Deviation from routine
        - Environmental factors (noise, temperature)
        - Notification frequency
    
    Output: 0.0 (relaxed) to 1.0 (stressed)
    """
    
    def evaluate(self, context: Dict[str, Any]) -> float:
        """Evaluate stress level."""
        stress_factors = []
        
        # Calendar load
        calendar = context.get("calendar", {})
        upcoming_events = calendar.get("upcoming_count_1h", 0)
        if upcoming_events > 3:
            stress_factors.append(0.8)
        elif upcoming_events > 1:
            stress_factors.append(0.4)
        else:
            stress_factors.append(0.1)
        
        # Routine deviation (from context)
        routine_deviation = context.get("routine_deviation", 0.0)
        stress_factors.append(min(1.0, routine_deviation * 2))
        
        # Environmental stress (noise, temp deviation)
        env_stress = 0.0
        states = context.get("states", {})
        
        # Check noise level
        noise_entities = [
            eid for eid in self.config.entity_ids
            if "noise" in eid.lower()
        ]
        for eid in noise_entities:
            state = states.get(eid, {})
            try:
                noise = float(state.get("state", 0))
                if noise > 60:  # dB
                    env_stress = max(env_stress, (noise - 60) / 40)
            except (ValueError, TypeError):
                pass
        
        stress_factors.append(env_stress)
        
        # Average stress factors
        return round(sum(stress_factors) / len(stress_factors), 3) if stress_factors else 0.3
    
    @classmethod
    def from_config(cls, config: NeuronConfig) -> "StressIndexNeuron":
        return cls(config)


class RoutineStabilityNeuron(StateNeuron):
    """Evaluates how stable/predictable the current routine is.
    
    Inputs:
        - Pattern deviation from historical behavior
        - Time-based routine matching
        - Activity consistency
    
    Output: 0.0 (chaotic) to 1.0 (stable routine)
    """
    
    def __init__(self, config: NeuronConfig, lookback_days: int = 7):
        super().__init__(config)
        self.lookback_days = lookback_days
        # State neurons have more smoothing
        config.smoothing_factor = min(config.smoothing_factor, 0.15)
    
    def evaluate(self, context: Dict[str, Any]) -> float:
        """Evaluate routine stability."""
        # Check if current time matches expected patterns
        time_context = context.get("time", {})
        patterns = context.get("patterns", {})
        
        # Get expected activities for this time
        hour = datetime.now().hour
        day_of_week = datetime.now().weekday()
        
        expected = patterns.get(f"expected_{day_of_week}_{hour}", {})
        actual = context.get("current_activity", {})
        
        if not expected:
            # No historical data - moderate stability
            return 0.5
        
        # Compare expected vs actual
        stability = 1.0
        
        for key, expected_value in expected.items():
            actual_value = actual.get(key)
            if actual_value is not None:
                # Calculate deviation
                if isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
                    deviation = abs(expected_value - actual_value) / max(expected_value, 1)
                    stability -= deviation * 0.1
        
        return max(0.0, min(1.0, stability))
    
    @classmethod
    def from_config(cls, config: NeuronConfig) -> "RoutineStabilityNeuron":
        lookback = config.weights.get("lookback_days", 7)
        return cls(config, lookback_days=lookback)


class SleepDebtNeuron(StateNeuron):
    """Evaluates accumulated sleep debt.
    
    Inputs:
        - Recent sleep duration vs target
        - Sleep quality indicators
        - Time since last good sleep
    
    Output: 0.0 (well rested) to 1.0 (severely sleep deprived)
    """
    
    def __init__(self, config: NeuronConfig, target_sleep_hours: float = 7.5):
        super().__init__(config)
        self.target_sleep_hours = target_sleep_hours
        self._sleep_history: deque = deque(maxlen=7)  # Last 7 days
    
    def evaluate(self, context: Dict[str, Any]) -> float:
        """Evaluate sleep debt."""
        sleep_data = context.get("sleep", {})
        
        # Get last night's sleep
        last_sleep_hours = sleep_data.get("last_night_hours", self.target_sleep_hours)
        sleep_quality = sleep_data.get("quality", 1.0)
        
        # Calculate debt
        sleep_deficit = max(0, self.target_sleep_hours - last_sleep_hours)
        
        # Factor in quality
        effective_deficit = sleep_deficit * (2 - sleep_quality)
        
        # Normalize to 0-1 (max deficit: 3 hours = severe)
        debt = min(1.0, effective_deficit / 3.0)
        
        return round(debt, 3)
    
    @classmethod
    def from_config(cls, config: NeuronConfig) -> "SleepDebtNeuron":
        target = config.weights.get("target_sleep_hours", 7.5)
        return cls(config, target_sleep_hours=target)


class AttentionLoadNeuron(StateNeuron):
    """Evaluates current attention/cognitive load.
    
    Inputs:
        - Active media/entertainment
        - Number of running devices
        - Recent interactions
    
    Output: 0.0 (focused/calm) to 1.0 (overloaded)
    """
    
    def evaluate(self, context: Dict[str, Any]) -> float:
        """Evaluate attention load."""
        states = context.get("states", {})
        load = 0.0
        
        # Count active media players
        media_entities = [
            eid for eid in self.config.entity_ids
            if eid.startswith("media_player.")
        ]
        
        playing_count = sum(
            1 for eid in media_entities
            if states.get(eid, {}).get("state") == "playing"
        )
        
        if playing_count > 2:
            load += 0.4
        elif playing_count > 0:
            load += 0.2
        
        # Count active lights (visual load)
        light_entities = [
            eid for eid in self.config.entity_ids
            if eid.startswith("light.")
        ]
        
        lights_on = sum(
            1 for eid in light_entities
            if states.get(eid, {}).get("state") == "on"
        )
        
        if lights_on > 10:
            load += 0.3
        elif lights_on > 5:
            load += 0.15
        
        # Notifications (from context)
        recent_notifications = context.get("recent_notifications", 0)
        load += min(0.3, recent_notifications * 0.1)
        
        return min(1.0, load)
    
    @classmethod
    def from_config(cls, config: NeuronConfig) -> "AttentionLoadNeuron":
        return cls(config)


class ComfortIndexNeuron(StateNeuron):
    """Evaluates environmental comfort.
    
    Inputs:
        - Temperature vs target
        - Humidity vs target
        - Light level appropriateness
        - Air quality
    
    Output: 0.0 (uncomfortable) to 1.0 (comfortable)
    """
    
    def __init__(
        self,
        config: NeuronConfig,
        target_temp: float = 22.0,
        target_humidity: float = 50.0
    ):
        super().__init__(config)
        self.target_temp = target_temp
        self.target_humidity = target_humidity
    
    def evaluate(self, context: Dict[str, Any]) -> float:
        """Evaluate comfort index."""
        states = context.get("states", {})
        comfort_scores = []
        
        # Temperature comfort
        temp_entities = [
            eid for eid in self.config.entity_ids
            if "temperature" in eid.lower() or "temp" in eid.lower()
        ]
        
        for eid in temp_entities:
            state = states.get(eid, {})
            try:
                temp = float(state.get("state", self.target_temp))
                # Comfort zone: 18-26°C, optimal 20-24°C
                if 20 <= temp <= 24:
                    temp_comfort = 1.0
                elif 18 <= temp <= 26:
                    temp_comfort = 0.7
                else:
                    temp_comfort = max(0, 1 - abs(temp - self.target_temp) / 10)
                comfort_scores.append(temp_comfort)
            except (ValueError, TypeError):
                pass
        
        # Humidity comfort
        humidity_entities = [
            eid for eid in self.config.entity_ids
            if "humidity" in eid.lower()
        ]
        
        for eid in humidity_entities:
            state = states.get(eid, {})
            try:
                humidity = float(state.get("state", self.target_humidity))
                # Comfort zone: 30-60%, optimal 40-50%
                if 40 <= humidity <= 50:
                    humid_comfort = 1.0
                elif 30 <= humidity <= 60:
                    humid_comfort = 0.7
                else:
                    humid_comfort = max(0, 1 - abs(humidity - self.target_humidity) / 50)
                comfort_scores.append(humid_comfort)
            except (ValueError, TypeError):
                pass
        
        # Average all comfort factors
        if comfort_scores:
            return round(sum(comfort_scores) / len(comfort_scores), 3)
        
        return 0.5  # No data, assume moderate comfort
    
    @classmethod
    def from_config(cls, config: NeuronConfig) -> "ComfortIndexNeuron":
        target_temp = config.weights.get("target_temp", 22.0)
        target_humidity = config.weights.get("target_humidity", 50.0)
        return cls(config, target_temp=target_temp, target_humidity=target_humidity)


# Register all state neurons
STATE_NEURON_CLASSES = {
    "energy_level": EnergyLevelNeuron,
    "stress_index": StressIndexNeuron,
    "routine_stability": RoutineStabilityNeuron,
    "sleep_debt": SleepDebtNeuron,
    "attention_load": AttentionLoadNeuron,
    "comfort_index": ComfortIndexNeuron,
}


def create_state_neuron(name: str, config: NeuronConfig) -> StateNeuron:
    """Factory function to create state neurons by name."""
    neuron_class = STATE_NEURON_CLASSES.get(name)
    if neuron_class:
        return neuron_class.from_config(config)
    raise ValueError(f"Unknown state neuron type: {name}")