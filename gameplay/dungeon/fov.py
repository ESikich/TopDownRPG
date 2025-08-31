# gameplay/dungeon/fov.py
"""Field of Vision calculation using simple raycast approach"""
from typing import Set
from core.types import Point
import math

def compute_visible(grid, origin_x: int, origin_y: int, radius: int) -> Set[Point]:
    """Compute visible tiles using simple raycast FOV"""
    visible = set()
    visible.add((origin_x, origin_y))
    
    # Simple approach: cast rays in all directions
    for angle in range(0, 360, 2):  # Every 2 degrees
        rad = math.radians(angle)
        dx = math.cos(rad)
        dy = math.sin(rad)
        
        # Cast ray outward
        for step in range(1, radius + 1):
            x = int(origin_x + dx * step)
            y = int(origin_y + dy * step)
            
            # Check bounds
            if not (0 <= x < len(grid[0]) and 0 <= y < len(grid)):
                break
            
            # Add to visible
            visible.add((x, y))
            
            # Stop if we hit an opaque tile
            if grid[y][x].opaque:
                break
    
    return visible