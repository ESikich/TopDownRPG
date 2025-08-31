# util/pathfinding.py
"""A* pathfinding utilities"""
import heapq
from typing import Dict, List, Optional, Tuple, Protocol, Sequence
from core.types import Point


# Minimal structural typing so we don't import heavy modules here
class _TileLike(Protocol):
    walkable: bool


class _WorldLike(Protocol):
    def is_blocked(self, x: int, y: int, grid: Sequence[Sequence[_TileLike]]) -> bool: ...


Grid = Sequence[Sequence[_TileLike]]
OpenItem = Tuple[float, Point]  # (f_score, node)


def find_path(
    start: Point,
    goal: Point,
    grid: Optional[Grid] = None,
    world: Optional[_WorldLike] = None,
) -> Optional[List[Point]]:
    """Find a path using the A* algorithm (4-way movement, Manhattan heuristic)."""

    def heuristic(a: Point, b: Point) -> float:
        # Manhattan distance as float to keep all scores homogeneous
        return float(abs(a[0] - b[0]) + abs(a[1] - b[1]))

    def in_bounds(p: Point) -> bool:
        if grid is None:
            return True
        if not grid:  # empty grid defensive check
            return False
        h = len(grid)
        w = len(grid[0])
        return 0 <= p[0] < w and 0 <= p[1] < h

    def passable(p: Point) -> bool:
        if grid is not None:
            if not grid[p[1]][p[0]].walkable:
                return False
        if world is not None and grid is not None:
            if world.is_blocked(p[0], p[1], grid):
                return False
        return True

    def get_neighbors(pos: Point) -> List[Point]:
        x, y = pos
        neighbors: List[Point] = []
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            np = (x + dx, y + dy)
            if in_bounds(np) and passable(np):
                neighbors.append(np)
        return neighbors

    # A* data
    open_heap: List[OpenItem] = [(0.0, start)]
    came_from: Dict[Point, Point] = {}
    g_score: Dict[Point, float] = {start: 0.0}
    f_score: Dict[Point, float] = {start: heuristic(start, goal)}

    while open_heap:
        _, current = heapq.heappop(open_heap)

        if current == goal:
            # Reconstruct path (includes start and goal)
            path: List[Point] = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        for neighbor in get_neighbors(current):
            tentative_g = g_score[current] + 1.0  # uniform edge cost

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + heuristic(neighbor, goal)
                f_score[neighbor] = f
                heapq.heappush(open_heap, (f, neighbor))

    return None  # No path found
