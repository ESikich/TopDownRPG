# gameplay/dungeon/generator.py
"""Dungeon generation system"""

import random
from typing import Any, Dict, List, Mapping, Optional, Tuple, TypeAlias

from core.types import Rect
from gameplay.dungeon.tiles import Tile, TileType  # assuming Tile has .wall(), .floor(), .stairs_down()

# ---- Type aliases for clarity ----
Coord: TypeAlias = Tuple[int, int]
Grid:  TypeAlias = List[List[Tile]]
RoomList: TypeAlias = List[Rect]
PlacementMap: TypeAlias = Dict[str, List[Coord]]


class DungeonGenerator:
    def __init__(self, rng: Optional[random.Random] = None) -> None:
        self.rng: random.Random = rng or random.Random()

    def generate(
        self,
        width: int,
        height: int,
        params: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a complete dungeon layout."""
        params = dict(params or {})  # local, mutable copy if needed

        # Initialize grid with walls
        grid: Grid = [[Tile.wall() for _ in range(width)] for _ in range(height)]

        # Generate rooms
        rooms: RoomList = self._generate_rooms(width, height, params)

        # Carve out rooms
        for room in rooms:
            for y in range(room.y, room.y + room.height):
                for x in range(room.x, room.x + room.width):
                    if 0 <= x < width and 0 <= y < height:
                        grid[y][x] = Tile.floor()

        # Connect rooms with corridors
        self._connect_rooms(grid, rooms, width, height)

        # Place special features
        placements: PlacementMap = self._place_features(grid, rooms, width, height)

        return {
            "grid": grid,
            "rooms": rooms,
            "placements": placements,
        }

    def _generate_rooms(
        self,
        width: int,
        height: int,
        params: Mapping[str, Any],
    ) -> RoomList:
        """Generate non-overlapping rooms."""
        rooms: RoomList = []

        max_attempts: int = int(params.get("max_room_attempts", 50))
        min_size: int = int(params.get("min_room_size", 4))
        max_size: int = int(params.get("max_room_size", 8))
        max_rooms: int = int(params.get("max_rooms", 8))

        for _ in range(max_attempts):
            if len(rooms) >= max_rooms:
                break

            room_width = self.rng.randint(min_size, max_size)
            room_height = self.rng.randint(min_size, max_size)

            # keep a one-tile border to avoid carving outside bounds
            if room_width >= width - 2 or room_height >= height - 2:
                continue

            room_x = self.rng.randint(1, max(1, width - room_width - 1))
            room_y = self.rng.randint(1, max(1, height - room_height - 1))

            new_room = Rect(room_x, room_y, room_width, room_height)

            # Check for overlaps
            if all(not new_room.intersects(existing) for existing in rooms):
                rooms.append(new_room)

        return rooms

    def _connect_rooms(
        self,
        grid: Grid,
        rooms: RoomList,
        width: int,
        height: int,
    ) -> None:
        """Connect rooms with corridors."""
        if len(rooms) < 2:
            return

        # Connect consecutive rooms
        for i in range(len(rooms) - 1):
            self._carve_corridor(grid, rooms[i], rooms[i + 1], width, height)

        # Optionally connect last to first for a cycle
        if len(rooms) > 2:
            self._carve_corridor(grid, rooms[-1], rooms[0], width, height)

        # Add some extra connections
        for _ in range(max(0, len(rooms) // 3)):
            room1 = self.rng.choice(rooms)
            room2 = self.rng.choice(rooms)
            if room1 is not room2:
                self._carve_corridor(grid, room1, room2, width, height)

    def _carve_corridor(
        self,
        grid: Grid,
        room1: Rect,
        room2: Rect,
        width: int,
        height: int,
    ) -> None:
        """Carve L-shaped corridor between rooms."""
        x1, y1 = room1.center_x, room1.center_y
        x2, y2 = room2.center_x, room2.center_y

        if self.rng.choice([True, False]):
            # Horizontal first, then vertical
            self._carve_horizontal_corridor(grid, x1, x2, y1, width, height)
            self._carve_vertical_corridor(grid, x2, y1, y2, width, height)
        else:
            # Vertical first, then horizontal
            self._carve_vertical_corridor(grid, x1, y1, y2, width, height)
            self._carve_horizontal_corridor(grid, x1, x2, y2, width, height)

    def _carve_horizontal_corridor(
        self,
        grid: Grid,
        x1: int,
        x2: int,
        y: int,
        width: int,
        height: int,
    ) -> None:
        """Carve horizontal corridor."""
        start_x = min(x1, x2)
        end_x = max(x1, x2)
        for x in range(start_x, end_x + 1):
            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = Tile.floor()

    def _carve_vertical_corridor(
        self,
        grid: Grid,
        x: int,
        y1: int,
        y2: int,
        width: int,
        height: int,
    ) -> None:
        """Carve vertical corridor."""
        start_y = min(y1, y2)
        end_y = max(y1, y2)
        for y in range(start_y, end_y + 1):
            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = Tile.floor()

    def _place_features(
        self,
        grid: Grid,
        rooms: RoomList,
        width: int,
        height: int,
    ) -> PlacementMap:
        """Place stairs, treasures, etc."""
        placements: PlacementMap = {
            "stairs_down": [],
            "treasures": [],
            "springs": [],
            "magic_circles": [],
        }

        # Place stairs in last room
        if rooms:
            last_room = rooms[-1]
            stairs_x = self.rng.randint(last_room.x, last_room.x + last_room.width - 1)
            stairs_y = self.rng.randint(last_room.y, last_room.y + last_room.height - 1)
            grid[stairs_y][stairs_x] = Tile.stairs_down()
            placements["stairs_down"].append((stairs_x, stairs_y))

        # Place treasures in up to 3 random rooms (if any)
        if rooms:
            for room in self.rng.sample(rooms, k=min(3, len(rooms))):
                treasure_x = self.rng.randint(room.x, room.x + room.width - 1)
                treasure_y = self.rng.randint(room.y, room.y + room.height - 1)
                placements["treasures"].append((treasure_x, treasure_y))

        return placements
