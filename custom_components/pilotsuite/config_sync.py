"""Configuration Synchronization for Multi-Home Setup.

Handles synchronization of configuration data between multiple home instances,
including automations, zones, entities, and user preferences.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

_LOGGER = logging.getLogger(__name__)


class ConfigSync:
    """Handles configuration synchronization between homes."""
    
    def __init__(self):
        """Initialize config sync."""
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self._config_versions: Dict[str, str] = {}  # home_id -> version_hash
    
    def get_config_hash(self, config: Dict[str, Any]) -> str:
        """Generate hash for configuration data."""
        config_json = json.dumps(config, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(config_json.encode('utf-8')).hexdigest()[:16]
    
    def fetch_local_config(self, home_id: str) -> Dict[str, Any]:
        """Fetch local configuration for a home."""
        config = {
            "automations": [],
            "zones": [],
            "entities": [],
            "user_preferences": {},
            "location_settings": {},
            "schedules": [],
        }
        
        # Try to load from disk if available
        config_file = f"/data/multihome/configs/{home_id}.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception as e:
                _LOGGER.error(f"Failed to load config for {home_id}: {e}")
        
        self._config_cache[home_id] = config
        self._config_versions[home_id] = self.get_config_hash(config)
        return config
    
    def save_local_config(self, home_id: str, config: Dict[str, Any]) -> bool:
        """Save configuration locally."""
        try:
            config_dir = "/data/multihome/configs"
            os.makedirs(config_dir, exist_ok=True)
            
            config_file = f"{config_dir}/{home_id}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            self._config_cache[home_id] = config
            self._config_versions[home_id] = self.get_config_hash(config)
            _LOGGER.info(f"Saved config for home {home_id}")
            return True
        except Exception as e:
            _LOGGER.error(f"Failed to save config for {home_id}: {e}")
            return False
    
    def detect_config_changes(
        self,
        source_home_id: str,
        target_home_id: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any], List[str]]:
        """Detect configuration changes between two homes."""
        source_config = self.fetch_local_config(source_home_id)
        target_config = self.fetch_local_config(target_home_id)
        
        added = []
        modified = []
        removed = []
        
        # Compare sections
        for section in ["automations", "zones", "entities", "schedules"]:
            source_items = {item.get("id"): item for item in source_config.get(section, [])}
            target_items = {item.get("id"): item for item in target_config.get(section, [])}
            
            # Find added items
            for item_id in source_items:
                if item_id not in target_items:
                    added.append(f"{section}.{item_id}")
                elif source_items[item_id] != target_items[item_id]:
                    modified.append(f"{section}.{item_id}")
            
            # Find removed items
            for item_id in target_items:
                if item_id not in source_items:
                    removed.append(f"{section}.{item_id}")
        
        # Compare user preferences
        source_prefs = source_config.get("user_preferences", {})
        target_prefs = target_config.get("user_preferences", {})
        
        for key in source_prefs:
            if key not in target_prefs:
                added.append(f"preferences.{key}")
            elif source_prefs[key] != target_prefs[key]:
                modified.append(f"preferences.{key}")
        
        for key in target_prefs:
            if key not in source_prefs:
                removed.append(f"preferences.{key}")
        
        changes = {
            "added": added,
            "modified": modified,
            "removed": removed,
            "source_version": self._config_versions.get(source_home_id),
            "target_version": self._config_versions.get(target_home_id),
        }
        
        _LOGGER.info(f"Detected config changes: {len(added)} added, {len(modified)} modified, {len(removed)} removed")
        return source_config, target_config, changes
    
    def get_config_diff_report(
        self,
        home_id_1: str,
        home_id_2: str
    ) -> Dict[str, Any]:
        """Generate a configuration difference report between two homes."""
        config1 = self.fetch_local_config(home_id_1)
        config2 = self.fetch_local_config(home_id_2)
        
        _, _, changes = self.detect_config_changes(home_id_1, home_id_2)
        
        return {
            "home_1": home_id_1,
            "home_2": home_id_2,
            "home_1_version": self._config_versions.get(home_id_1),
            "home_2_version": self._config_versions.get(home_id_2),
            "changes": changes,
            "summary": {
                "total_added": len(changes["added"]),
                "total_modified": len(changes["modified"]),
                "total_removed": len(changes["removed"]),
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }


# Singleton instance
_config_sync: Optional[ConfigSync] = None


def get_config_sync() -> ConfigSync:
    """Get or create the config sync singleton."""
    global _config_sync
    if _config_sync is None:
        _config_sync = ConfigSync()
    return _config_sync
