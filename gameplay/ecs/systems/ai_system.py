# gameplay/ecs/systems/ai_system.py
"""AI behavior system"""
from gameplay.ecs.world import World
from gameplay.ecs.components import CAI, CPosition, CHealth, CVisible
from core.events import MoveRequested
from util.pathfinding import find_path
import random

class AISystem:
    def __init__(self, world: World, player_eid: int, dungeon_grid=None, rng=None):
        self.world = world
        self.player_eid = player_eid
        self.dungeon_grid = dungeon_grid
        self.rng = rng or random.Random()
    
    def process(self):
        """Process AI for all entities with CAI"""
        for eid in self.world.entities_with(CAI, CPosition, CHealth):
            health = self.world.get(eid, CHealth)
            if health.is_dead:
                continue
                
            ai = self.world.get(eid, CAI)
            if ai.behavior == "chase":
                self._process_chase_ai(eid)
            elif ai.behavior == "wander":
                self._process_wander_ai(eid)
    
    def _process_chase_ai(self, eid: int):
        """Chase AI - move toward player if visible, otherwise wander"""
        pos = self.world.get(eid, CPosition)
        player_pos = self.world.get(self.player_eid, CPosition)
        
        if not pos or not player_pos:
            return
        
        # Check if player is visible
        visible = self.world.get(eid, CVisible)
        player_visible = False
        if visible:
            player_visible = (player_pos.x, player_pos.y) in visible.visible_tiles
        
        if player_visible:
            # Move toward player
            path = find_path((pos.x, pos.y), (player_pos.x, player_pos.y), 
                           self.dungeon_grid, self.world)
            if path and len(path) > 1:
                next_pos = path[1]  # First step of path
                self.world.post(MoveRequested(eid, next_pos))
        else:
            # Wander randomly
            self._process_wander_ai(eid)
    
    def _process_wander_ai(self, eid: int):
        """Random wandering AI"""
        pos = self.world.get(eid, CPosition)
        if not pos:
            return
        
        # Pick random adjacent position
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        dx, dy = self.rng.choice(directions)
        new_pos = (pos.x + dx, pos.y + dy)
        
        self.world.post(MoveRequested(eid, new_pos))