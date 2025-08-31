# core/input.py
"""Input handling system"""
import pygame
from typing import Dict, List, Optional
import toml
from core.types import Direction

class InputHandler:
    def __init__(self):
        self.keybinds = self._load_keybinds()
        
    def _load_keybinds(self) -> Dict[str, List[str]]:
        try:
            with open('config/keybinds.toml', 'r') as f:
                config = toml.load(f)
                keybinds = {}
                for category, bindings in config.items():
                    for action, keys in bindings.items():
                        keybinds[action] = keys
                return keybinds
        except FileNotFoundError:
            # Default keybinds if file not found
            return {
                'up': ['w', 'up'],
                'down': ['s', 'down'], 
                'left': ['a', 'left'],
                'right': ['d', 'right'],
                'wait': ['space'],
                'inventory': ['i'],
                'spellbook': ['c'],
                'descend': ['period'],
                'restart': ['r'],
                'pause': ['escape']
            }
    
    def get_action(self, key_name: str) -> Optional[str]:
        """Get action name for a key"""
        for action, keys in self.keybinds.items():
            if key_name in keys:
                return action
        return None
    
    def get_direction(self, action: str) -> Optional[Direction]:
        """Convert action to direction"""
        direction_map = {
            'up': Direction.UP,
            'down': Direction.DOWN,
            'left': Direction.LEFT,
            'right': Direction.RIGHT
        }
        return direction_map.get(action)