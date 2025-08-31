# gameplay/ecs/systems/movement_system.py
"""Movement and collision system"""
from gameplay.ecs.world import World
from gameplay.ecs.components import CPosition, CBlocker, CHealth
from core.events import MoveRequested, MoveResolved, Bump, AttackRequested, Message

class MovementSystem:
    def __init__(self, world: World, dungeon_grid=None):
        self.world = world
        self.dungeon_grid = dungeon_grid
    
    def process(self):
        """Process all movement requests"""
        events = self.world.drain_events()
        
        for event in events:
            if isinstance(event, MoveRequested):
                self._handle_move_request(event)
    
    def _handle_move_request(self, event: MoveRequested):
        """Handle a single movement request"""
        eid = event.eid
        to_x, to_y = event.to_xy
        
        # Get current position
        pos = self.world.get(eid, CPosition)
        if not pos:
            return
        
        # Check bounds
        if self.dungeon_grid:
            if not (0 <= to_x < len(self.dungeon_grid[0]) and 0 <= to_y < len(self.dungeon_grid)):
                self.world.post(Message("Can't go that way!"))
                return
            
            # Check if tile is walkable
            if not self.dungeon_grid[to_y][to_x].walkable:
                self.world.post(Message("Blocked by wall!"))
                return
        
        # Check for entities at target position
        entities_at_target = self.world.entities_at(to_x, to_y)
        
        for target_eid in entities_at_target:
            if target_eid == eid:
                continue
                
            blocker = self.world.get(target_eid, CBlocker)
            if blocker and not blocker.passable:
                # Check if it's a living entity (has health)
                health = self.world.get(target_eid, CHealth)
                if health and not health.is_dead:
                    # Post bump and attack events
                    self.world.post(Bump(eid, target_eid))
                    self.world.post(AttackRequested(eid, target_eid))
                    return
                else:
                    self.world.post(Message("Blocked!"))
                    return
        
        # Move is valid - update position
        from_xy = (pos.x, pos.y)
        pos.x = to_x
        pos.y = to_y
        
        print(f"Entity {eid} moved from {from_xy} to ({to_x}, {to_y})")
        
        self.world.post(MoveResolved(eid, from_xy, (to_x, to_y)))