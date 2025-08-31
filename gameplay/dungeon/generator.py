# gameplay/dungeon/generator.py
"""Dungeon generation system"""
import random
from typing import List, Dict, Any
from core.types import Rect
from gameplay.dungeon.tiles import Tile, TileType

class DungeonGenerator:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
    
    def generate(self, width: int, height: int, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a complete dungeon layout"""
        params = params or {}
        
        # Initialize grid with walls
        grid = [[Tile.wall() for _ in range(width)] for _ in range(height)]
        
        # Generate rooms
        rooms = self._generate_rooms(width, height, params)
        
        # Carve out rooms
        for room in rooms:
            for y in range(room.y, room.y + room.height):
                for x in range(room.x, room.x + room.width):
                    if 0 <= x < width and 0 <= y < height:
                        grid[y][x] = Tile.floor()
        
        # Connect rooms with corridors
        self._connect_rooms(grid, rooms, width, height)
        
        # Place special features
        placements = self._place_features(grid, rooms, width, height)
        
        return {
            'grid': grid,
            'rooms': rooms,
            'placements': placements
        }
    
    def _generate_rooms(self, width: int, height: int, params: Dict) -> List[Rect]:
        """Generate non-overlapping rooms"""
        rooms = []
        max_attempts = params.get('max_room_attempts', 50)
        min_size = params.get('min_room_size', 4)
        max_size = params.get('max_room_size', 8)
        max_rooms = params.get('max_rooms', 8)
        
        for _ in range(max_attempts):
            if len(rooms) >= max_rooms:
                break
                
            room_width = self.rng.randint(min_size, max_size)
            room_height = self.rng.randint(min_size, max_size)
            room_x = self.rng.randint(1, width - room_width - 1)
            room_y = self.rng.randint(1, height - room_height - 1)
            
            new_room = Rect(room_x, room_y, room_width, room_height)
            
            # Check for overlaps
            can_place = True
            for existing_room in rooms:
                if new_room.intersects(existing_room):
                    can_place = False
                    break
            
            if can_place:
                rooms.append(new_room)
        
        return rooms
    
    def _connect_rooms(self, grid: List[List[Tile]], rooms: List[Rect], width: int, height: int):
        """Connect rooms with corridors"""
        if len(rooms) < 2:
            return
        
        # Connect consecutive rooms
        for i in range(len(rooms) - 1):
            self._carve_corridor(grid, rooms[i], rooms[i + 1], width, height)
        
        # Connect last to first for a cycle
        if len(rooms) > 2:
            self._carve_corridor(grid, rooms[-1], rooms[0], width, height)
        
        # Add some extra connections
        for _ in range(len(rooms) // 3):
            room1 = self.rng.choice(rooms)
            room2 = self.rng.choice(rooms)
            if room1 != room2:
                self._carve_corridor(grid, room1, room2, width, height)
    
    def _carve_corridor(self, grid: List[List[Tile]], room1: Rect, room2: Rect, width: int, height: int):
        """Carve L-shaped corridor between rooms"""
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
    
    def _carve_horizontal_corridor(self, grid: List[List[Tile]], x1: int, x2: int, y: int, width: int, height: int):
        """Carve horizontal corridor"""
        start_x = min(x1, x2)
        end_x = max(x1, x2)
        for x in range(start_x, end_x + 1):
            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = Tile.floor()
    
    def _carve_vertical_corridor(self, grid: List[List[Tile]], x: int, y1: int, y2: int, width: int, height: int):
        """Carve vertical corridor"""
        start_y = min(y1, y2)
        end_y = max(y1, y2)
        for y in range(start_y, end_y + 1):
            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = Tile.floor()
    
    def _place_features(self, grid: List[List[Tile]], rooms: List[Rect], width: int, height: int) -> Dict[str, List]:
        """Place stairs, treasures, etc."""
        placements = {
            'stairs_down': [],
            'treasures': [],
            'springs': [],
            'magic_circles': []
        }
        
        # Place stairs in last room
        if rooms:
            last_room = rooms[-1]
            stairs_x = self.rng.randint(last_room.x, last_room.x + last_room.width - 1)
            stairs_y = self.rng.randint(last_room.y, last_room.y + last_room.height - 1)
            grid[stairs_y][stairs_x] = Tile.stairs_down()
            placements['stairs_down'].append((stairs_x, stairs_y))
        
        # Place treasures in random rooms
        treasure_rooms = self.rng.sample(rooms, min(3, len(rooms)))
        for room in treasure_rooms:
            treasure_x = self.rng.randint(room.x, room.x + room.width - 1)
            treasure_y = self.rng.randint(room.y, room.y + room.height - 1)
            placements['treasures'].append((treasure_x, treasure_y))
        
        return placements