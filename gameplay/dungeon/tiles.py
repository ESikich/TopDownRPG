# gameplay/dungeon/tiles.py
"""Tile definitions and properties"""
from enum import Enum
from dataclasses import dataclass

class TileType(Enum):
    WALL = "wall"
    FLOOR = "floor"
    DOOR = "door"
    STAIRS_DOWN = "stairs_down"
    WATER = "water"
    SAND = "sand"
    GRASS = "grass"

@dataclass
class Tile:
    tile_type: TileType
    walkable: bool
    opaque: bool
    color: tuple = (255, 255, 255)
    glyph: str = "?"
    
    @classmethod
    def wall(cls):
        return cls(TileType.WALL, False, True, (128, 128, 128), "#")
    
    @classmethod
    def floor(cls):
        return cls(TileType.FLOOR, True, False, (255, 255, 255), ".")
    
    @classmethod
    def door(cls):
        return cls(TileType.DOOR, False, True, (139, 69, 19), "+")
    
    @classmethod
    def stairs_down(cls):
        return cls(TileType.STAIRS_DOWN, True, False, (255, 255, 255), ">")
    
    @classmethod
    def water(cls):
        return cls(TileType.WATER, True, False, (0, 255, 255), "~")