# util/pathfinding.py
"""A* pathfinding utilities"""
import heapq
from typing import List, Optional, Tuple, Callable
from core.types import Point

def find_path(start: Point, goal: Point, grid=None, world=None) -> Optional[List[Point]]:
    """Find path using A* algorithm"""
    def heuristic(a: Point, b: Point) -> float:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def get_neighbors(pos: Point) -> List[Point]:
        x, y = pos
        neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            new_pos = (x + dx, y + dy)
            
            # Check bounds
            if grid and (new_pos[0] < 0 or new_pos[1] < 0 or 
                        new_pos[1] >= len(grid) or new_pos[0] >= len(grid[0])):
                continue
            
            # Check walkable
            if grid and not grid[new_pos[1]][new_pos[0]].walkable:
                continue
            
            # Check entity blocking
            if world and world.is_blocked(new_pos[0], new_pos[1], grid):
                continue
            
            neighbors.append(new_pos)
        
        return neighbors
    
    # A* algorithm
    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}
    
    while open_set:
        current = heapq.heappop(open_set)[1]
        
        if current == goal:
            # Reconstruct path
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return list(reversed(path))
        
        for neighbor in get_neighbors(current):
            tentative_g_score = g_score[current] + 1
            
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    
    return None  # No path found