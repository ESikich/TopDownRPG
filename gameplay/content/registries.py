# gameplay/content/registries.py
"""Content registries for game data"""
from typing import Dict, Any
import json
import os

class ContentRegistry:
    def __init__(self):
        self.items: Dict[str, Dict[str, Any]] = {}
        self.monsters: Dict[str, Dict[str, Any]] = {}
        self.spells: Dict[str, Dict[str, Any]] = {}
        self.loot_tables: Dict[str, Dict[str, Any]] = {}
        self._load_all_content()
    
    def _load_all_content(self):
        """Load all content from JSON files"""
        content_dir = "gameplay/data"
        
        # Create default data if files don't exist
        if not os.path.exists(content_dir):
            self._create_default_content()
            return
        
        self._load_json_file(f"{content_dir}/items.json", self.items)
        self._load_json_file(f"{content_dir}/monsters.json", self.monsters)
        self._load_json_file(f"{content_dir}/spells.json", self.spells)
        self._load_json_file(f"{content_dir}/loot_tables.json", self.loot_tables)
    
    def _load_json_file(self, filepath: str, target_dict: Dict):
        """Load JSON file into target dictionary"""
        try:
            with open(filepath, 'r') as f:
                target_dict.update(json.load(f))
        except FileNotFoundError:
            print(f"Warning: {filepath} not found, using defaults")
        except json.JSONDecodeError as e:
            print(f"Error loading {filepath}: {e}")
    
    def _create_default_content(self):
        """Create default content for testing"""
        self.items = {
            "sword": {
                "name": "Iron Sword",
                "glyph": "/",
                "color": "gray",
                "components": {
                    "CWeapon": {
                        "damage_dice": "1d6+STR",
                        "damage_type": "Physical",
                        "reach": 1
                    }
                }
            },
            "leather_armor": {
                "name": "Leather Armor",
                "glyph": "[",
                "color": "brown",
                "components": {
                    "CArmor": {
                        "soak_dice": "1d2",
                        "resist": {"Physical": 0.1}
                    }
                }
            }
        }
        
        self.monsters = {
            "slime": {
                "name": "Green Slime",
                "glyph": "s",
                "color": "green",
                "components": {
                    "CHealth": {"hp": 15, "max_hp": 15},
                    "CStats": {
                        "strength": 8, "agility": 6, "intellect": 2,
                        "accuracy": 5, "evasion": 2, "crit_chance": 5.0, "crit_mult": 2.0
                    },
                    "CAI": {"behavior": "chase"}
                }
            }
        }
        
        self.spells = {
            "firebolt": {
                "name": "Firebolt",
                "mp_cost": 3,
                "damage_dice": "1d8+INT/2",
                "damage_type": "Fire",
                "target_type": "single",
                "range": 5
            }
        }

# Global registry instance
content_registry = ContentRegistry()