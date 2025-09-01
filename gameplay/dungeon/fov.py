from __future__ import annotations

from typing import Iterable, Set, Tuple, Sequence, Protocol, runtime_checkable, Final
from core.types import Point


@runtime_checkable
class _HasOpaque(Protocol):
    """Structural type for a tile in the grid.

    Any object with a boolean `.opaque` attribute is accepted. This avoids
    coupling `compute_visible` to a concrete tile class.
    """
    opaque: bool


def _bresenham(x0: int, y0: int, x1: int, y1: int) -> Iterable[Tuple[int, int]]:
    """Yield integer lattice points from (x0, y0) to (x1, y1) using Bresenham's algorithm.

    Notes
    -----
    - Includes both endpoints.
    - 8-connected (allows diagonal movement).
    - Deterministic ordering of steps that matches the common integer Bresenham.
    """
    dx: int = abs(x1 - x0)
    sx: int = 1 if x0 < x1 else -1
    dy: int = -abs(y1 - y0)   # negative so `err = dx + dy` works uniformly
    sy: int = 1 if y0 < y1 else -1
    err: int = dx + dy
    x, y = x0, y0

    while True:
        yield x, y
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def compute_visible(
    grid: Sequence[Sequence[_HasOpaque]],
    ox: int,
    oy: int,
    radius: int,
) -> Set[Point]:
    """Compute visible tiles from (ox, oy) with Euclidean clamp and strict corner rules.

    Visibility rules:
      1) Euclidean radius clamp for LOS **tiles themselves** (the set we consider).
      2) Bresenham line-of-sight marching with **strict diagonal-corner blocking**:
         - When the ray takes a diagonal step from (prev_x, prev_y) to (x, y),
           visibility is blocked if either of the two orthogonal neighbors
           `(prev_x, y)` or `(x, prev_y)` is opaque.
      3) The **first blocking wall** encountered along a ray is revealed, then tracing stops.
      4) Corridor-wall reveal (unbounded): for every visible **floor** tile, reveal any
         **orthogonally adjacent** wall tiles, even if those lie outside the radius.

    Parameters
    ----------
    grid
        2D rectangular grid indexed as `grid[y][x]` whose cells expose `.opaque: bool`.
        Out-of-bounds is treated as opaque.
    ox, oy
        Origin x/y in grid coordinates.
    radius
        Euclidean radius used to limit which target tiles we attempt LOS against.

    Returns
    -------
    Set[Point]
        Set of visible points `(x, y)` using `core.types.Point`.

    Complexity
    ----------
    Let W×H be the map size and R the radius. The first pass visits O(R^2) targets and
    marches a Bresenham line for each (worst-case O(R)), so O(R^3) in the worst case.
    The corridor-wall pass is O(|vis|). In practice R is small enough that this is
    fast for roguelike FOV.
    """
    H: int = len(grid)
    W: int = len(grid[0]) if H else 0

    def in_bounds(x: int, y: int) -> bool:
        return 0 <= x < W and 0 <= y < H

    def opaque(x: int, y: int) -> bool:
        # Treat out-of-bounds as opaque to naturally block LOS at edges.
        return not in_bounds(x, y) or grid[y][x].opaque

    vis: Set[Point] = set()

    # Early outs for invalid origin or negative radius.
    if not in_bounds(ox, oy) or radius < 0:
        return vis

    vis.add((ox, oy))

    R2: int = radius * radius

    # -------- First pass: LOS with strict corner handling --------
    xmin: int = max(0, ox - radius)
    xmax: int = min(W - 1, ox + radius)
    ymin: int = max(0, oy - radius)
    ymax: int = min(H - 1, oy + radius)

    for ty in range(ymin, ymax + 1):
        for tx in range(xmin, xmax + 1):
            if (tx, ty) == (ox, oy):
                continue

            dx: int = tx - ox
            dy: int = ty - oy
            if dx * dx + dy * dy > R2:
                # Outside Euclidean clamp: we neither trace nor add.
                continue

            target_is_wall: bool = grid[ty][tx].opaque

            # Origin-adjacent strict diagonal rule:
            # If heading diagonally to a floor, and either orthogonal step from the origin is blocked,
            # the diagonal is not allowed to "squeeze" through.
            if dx != 0 and dy != 0 and not target_is_wall:
                stepx: int = 1 if dx > 0 else -1
                stepy: int = 1 if dy > 0 else -1
                if opaque(ox + stepx, oy) or opaque(ox, oy + stepy):
                    continue

            prev_x, prev_y = ox, oy
            for x, y in _bresenham(ox, oy, tx, ty):
                if (x, y) == (ox, oy):
                    continue

                # Strict diagonal-corner blocking while marching:
                # When moving diagonally, check the two orthogonal neighbors that would be "cut" by the step.
                corner_blocked: bool = (x != prev_x and y != prev_y) and (
                    opaque(prev_x, y) or opaque(x, prev_y)
                )
                if corner_blocked:
                    # If the corner block occurs *on the target* and that target is a wall,
                    # we still reveal that wall per the spec, then stop.
                    if (x, y) == (tx, ty) and target_is_wall:
                        vis.add((x, y))
                    break

                # If this tile is opaque, reveal it and stop marching this ray.
                if grid[y][x].opaque:
                    vis.add((x, y))
                    break

                # Otherwise it's visible floor; keep marching.
                vis.add((x, y))
                prev_x, prev_y = x, y

    # -------- Second pass: corridor-wall reveal (unbounded) --------
    ADJ4: Final[Tuple[Tuple[int, int], ...]] = ((1, 0), (-1, 0), (0, 1), (0, -1))

    # Gather floors among visible points, then reveal orthogonally adjacent walls.
    floors: Tuple[Point, ...] = tuple(
        (x, y) for (x, y) in vis if in_bounds(x, y) and not grid[y][x].opaque
    )
    for fx, fy in floors:
        for ax, ay in ADJ4:
            nx, ny = fx + ax, fy + ay
            if in_bounds(nx, ny) and grid[ny][nx].opaque:
                vis.add((nx, ny))

    return vis
