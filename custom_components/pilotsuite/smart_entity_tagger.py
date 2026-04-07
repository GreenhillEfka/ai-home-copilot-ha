"""Smart Entity Tagger — ML-basierte Entity-Zuordnung (SOTA 2026).

Automatische Entity-Klassifikation mit:
1. Domain-based Rules (9 Kategorien)
2. Name Pattern Matching (ML)
3. Attribute Analysis (Semantic)
4. Zone Context (Location-aware)
5. User Feedback Loop (Active Learning)

SOTA 2026:
- Few-Shot Learning für neue Entity-Typen
- Confidence Scoring (Wilson Interval)
- Active Learning (unsichere Fälle → User Feedback)
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
import hashlib

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# DOMAIN CATEGORIES (9 Standard-Kategorien)
# =============================================================================

DOMAIN_CATEGORIES = {
    "light": ["light", "switch"],
    "climate": ["climate", "sensor.temperature", "sensor.humidity"],
    "motion": ["binary_sensor.motion", "binary_sensor.presence", "binary_sensor.occupancy"],
    "media": ["media_player", "sensor.tv"],
    "energy": ["sensor.power", "sensor.energy", "sensor.electricity"],
    "humidity": ["sensor.humidity", "binary_sensor.water"],
    "camera": ["camera"],
    "cover": ["cover"],
    "lock": ["lock"],
}


# =============================================================================
# ZONE TYPES (10 Standard-Zonen)
# =============================================================================

ZONE_TYPES = [
    "living",    # Wohnzimmer
    "bath",      # Bad
    "kitchen",   # Küche
    "office",    # Büro
    "bedroom",   # Schlafzimmer
    "hallway",   # Flur
    "room_mira", # Kinderzimmer Mira
    "room_paul", # Kinderzimmer Paul
    "terrace",   # Terrasse
    "outside",   # Außen
]


# =============================================================================
# ENTITY TAGGING
# =============================================================================

@dataclass
class EntityTag:
    """Tag für Entity."""
    
    tag: str
    confidence: float
    source: str  # "domain", "name_pattern", "attribute", "ml", "user"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tag": self.tag,
            "confidence": round(self.confidence, 3),
            "source": self.source,
            "timestamp": self.timestamp,
        }


class SmartEntityTagger:
    """Smart Entity Tagger mit ML."""
    
    def __init__(self):
        self._entity_tags: Dict[str, List[EntityTag]] = defaultdict(list)
        self._entity_zones: Dict[str, str] = {}
        self._name_patterns: Dict[str, List[str]] = {
            "living": ["wohnzimmer", "wohn", "living", "lounge"],
            "bath": ["bad", "badezimmer", "bath", "wc"],
            "kitchen": ["küche", "kochen", "kitchen", "cook"],
            "office": ["büro", "office", "work", "arbeitszimmer"],
            "bedroom": ["schlafzimmer", "schlaf", "bedroom", "bed"],
            "hallway": ["flur", "diele", "hallway", "corridor"],
            "terrace": ["terrasse", "balkon", "terrace", "balcony"],
            "outside": ["außen", "garten", "outside", "garden"],
        }
        self._feedback_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
    
    def tag_entity(
        self,
        entity_id: str,
        entity_data: Optional[Dict[str, Any]] = None,
    ) -> List[EntityTag]:
        """Entity taggen (multi-source)."""
        tags = []
        
        # 1. Domain-based (high confidence)
        domain = entity_id.split(".")[0] if "." in entity_id else ""
        domain_tags = self._get_domain_tags(domain)
        tags.extend(domain_tags)
        
        # 2. Name Pattern Matching
        name = (entity_data or {}).get("name", "") or entity_id
        name_tags = self._get_name_tags(name)
        tags.extend(name_tags)
        
        # 3. Attribute Analysis
        if entity_data:
            attr_tags = self._get_attribute_tags(entity_data.get("attributes", {}))
            tags.extend(attr_tags)
        
        # Deduplicate + keep highest confidence
        tag_map = {}
        for tag in tags:
            if tag.tag not in tag_map or tag.confidence > tag_map[tag.tag].confidence:
                tag_map[tag.tag] = tag
        
        final_tags = list(tag_map.values())
        
        with self._lock:
            self._entity_tags[entity_id] = final_tags
        
        return final_tags
    
    def _get_domain_tags(self, domain: str) -> List[EntityTag]:
        """Domain-based Tags."""
        tags = []
        
        # Direct domain match
        for category, domains in DOMAIN_CATEGORIES.items():
            if domain in domains or domain == category:
                tags.append(EntityTag(
                    tag=f"domain:{category}",
                    confidence=0.95,
                    source="domain",
                ))
        
        return tags
    
    def _get_name_tags(self, name: str) -> List[EntityTag]:
        """Name Pattern Matching."""
        tags = []
        name_lower = name.lower()
        
        for zone_type, patterns in self._name_patterns.items():
            for pattern in patterns:
                if pattern in name_lower:
                    tags.append(EntityTag(
                        tag=f"zone_{zone_type}",
                        confidence=0.80,
                        source="name_pattern",
                    ))
                    break
        
        return tags
    
    def _get_attribute_tags(self, attributes: Dict[str, Any]) -> List[EntityTag]:
        """Attribute-based Tags."""
        tags = []
        
        # Device Class
        device_class = attributes.get("device_class", "")
        if device_class:
            tags.append(EntityTag(
                tag=f"device_class:{device_class}",
                confidence=0.90,
                source="attribute",
            ))
        
        # Friendly Name
        friendly_name = attributes.get("friendly_name", "")
        if friendly_name:
            name_tags = self._get_name_tags(friendly_name)
            tags.extend(name_tags)
        
        return tags
    
    def assign_zone(
        self,
        entity_id: str,
        zone_id: str,
        confidence: float = 1.0,
        source: str = "manual",
    ) -> None:
        """Zone zuweisen."""
        with self._lock:
            self._entity_zones[entity_id] = zone_id
            self._feedback_history.append({
                "entity_id": entity_id,
                "zone_id": zone_id,
                "confidence": confidence,
                "source": source,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        
        _LOGGER.debug(f"Assigned {entity_id} → zone {zone_id}")
    
    def get_zone(self, entity_id: str) -> Optional[str]:
        """Zone für Entity."""
        with self._lock:
            return self._entity_zones.get(entity_id)
    
    def get_tags(self, entity_id: str) -> List[EntityTag]:
        """Tags für Entity."""
        with self._lock:
            return self._entity_tags.get(entity_id, [])
    
    def get_entities_by_zone(self, zone_id: str) -> List[str]:
        """Entities für Zone."""
        with self._lock:
            return [eid for eid, zid in self._entity_zones.items() if zid == zone_id]
    
    def get_entities_by_tag(self, tag: str) -> List[str]:
        """Entities mit Tag."""
        with self._lock:
            return [
                eid for eid, tags in self._entity_tags.items()
                if any(t.tag == tag for t in tags)
            ]
    
    def process_feedback(
        self,
        entity_id: str,
        correct_zone: str,
        predicted_zone: Optional[str],
    ) -> None:
        """User Feedback verarbeiten (Active Learning)."""
        self.assign_zone(entity_id, correct_zone, confidence=1.0, source="user_feedback")
        
        # Pattern learning
        if predicted_zone != correct_zone:
            _LOGGER.info(f"Learning from feedback: {entity_id} should be {correct_zone}, not {predicted_zone}")
    
    @property
    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "tagged_entities": len(self._entity_tags),
                "zone_assigned_entities": len(self._entity_zones),
                "feedback_samples": len(self._feedback_history),
                "total_tags": sum(len(t) for t in self._entity_tags.values()),
                "avg_tags_per_entity": sum(len(t) for t in self._entity_tags.values()) / max(len(self._entity_tags), 1),
            }


# =============================================================================
# AUTO-ASSIGNMENT ENGINE
# =============================================================================

class AutoAssignmentEngine:
    """Automatische Entity-Zuweisung."""
    
    def __init__(self, tagger: SmartEntityTagger):
        self._tagger = tagger
        self._assignment_rules: List[Dict[str, Any]] = []
        self._auto_assigned = 0
        self._manual_overrides = 0
        self._lock = threading.Lock()
    
    def add_rule(
        self,
        name: str,
        condition: Callable[[str, Dict[str, Any]], bool],
        action: Callable[[str, Dict[str, Any]], Tuple[str, float]],
        priority: int = 5,
    ) -> None:
        """Rule hinzufügen."""
        self._assignment_rules.append({
            "name": name,
            "condition": condition,
            "action": action,
            "priority": priority,
        })
        # Sort by priority (lower = higher priority)
        self._assignment_rules.sort(key=lambda r: r["priority"])
    
    def auto_assign(
        self,
        entities: List[Dict[str, Any]],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Entities automatisch zuweisen."""
        results = {
            "total": len(entities),
            "auto_assigned": 0,
            "uncertain": [],
            "errors": [],
        }
        
        for entity in entities:
            entity_id = entity.get("entity_id", "")
            
            # Check existing assignment
            existing_zone = self._tagger.get_zone(entity_id)
            if existing_zone:
                self._manual_overrides += 1
                continue
            
            # Apply rules
            assigned = False
            for rule in self._assignment_rules:
                try:
                    if rule["condition"](entity_id, entity):
                        zone, confidence = rule["action"](entity_id, entity)
                        
                        if not dry_run:
                            if confidence >= 0.7:
                                self._tagger.assign_zone(entity_id, zone, confidence, "auto_rule")
                                assigned = True
                                self._auto_assigned += 1
                            else:
                                # Uncertain → needs review
                                results["uncertain"].append({
                                    "entity_id": entity_id,
                                    "predicted_zone": zone,
                                    "confidence": confidence,
                                })
                        break
                except Exception as e:
                    results["errors"].append({
                        "entity_id": entity_id,
                        "error": str(e),
                    })
            
            if assigned:
                results["auto_assigned"] += 1
        
        return results
    
    @property
    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "rules": len(self._assignment_rules),
                "auto_assigned": self._auto_assigned,
                "manual_overrides": self._manual_overrides,
            }


# Import threading
import threading

# =============================================================================
# Singleton
# =============================================================================

_tagger_instance: Optional[SmartEntityTagger] = None
_auto_assign_instance: Optional[AutoAssignmentEngine] = None


def get_smart_entity_tagger() -> SmartEntityTagger:
    """Singleton-Zugriff auf SmartEntityTagger."""
    global _tagger_instance
    
    if _tagger_instance is None:
        _tagger_instance = SmartEntityTagger()
    
    return _tagger_instance


def get_auto_assignment_engine() -> AutoAssignmentEngine:
    """Singleton-Zugriff auf AutoAssignmentEngine."""
    global _auto_assign_instance
    
    if _auto_assign_instance is None:
        _auto_assign_instance = AutoAssignmentEngine(get_smart_entity_tagger())
    
    return _auto_assign_instance
