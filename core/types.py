# core/types.py
"""Core type definitions"""
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional
from enum import Enum

Point = Tuple[int, int]
Color = Tuple[int, int, int]

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

@dataclass
class Rect:
    x: int
    y: int
    width: int
    height: int
    
    @property
    def center_x(self) -> int:
        return self.x + self.width // 2
    
    @property
    def center_y(self) -> int:
        return self.y + self.height // 2
    
    def intersects(self, other: 'Rect') -> bool:
        return not (self.x + self.width + 1 < other.x or 
                   other.x + other.width + 1 < self.x or 
                   self.y + self.height + 1 < other.y or 
                   other.y + other.height + 1 < self.y)