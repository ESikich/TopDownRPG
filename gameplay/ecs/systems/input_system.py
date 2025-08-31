# gameplay/ecs/systems/input_system.py
"""Input handling for player actions"""
from gameplay.ecs.world import World
from gameplay.ecs.components import CPosition
from core.events import MoveRequested, DescendRequested, Message
from core.types import Direction

class InputSystem:
    def __init__(self, world: World, player_eid: int):
        self.world = world
        self.player_eid = player_eid
        self.pending_action = None
    
    def handle_action(self, action: str, direction: Direction = None):
        """Handle player input action"""
        if action in ['up', 'down', 'left', 'right'] and direction:
            self._handle_movement(direction)
        elif action == 'wait':
            self.world.post(Message("You wait."))
        elif action == 'descend':
            self._handle_descend()
        elif action == 'inventory':
            self.world.post(Message("Inventory not implemented yet"))
        elif action == 'spellbook':
            self.world.post(Message("Spellbook not implemented yet"))
    
    def _handle_movement(self, direction: Direction):
        """Handle player movement"""
        pos = self.world.get(self.player_eid, CPosition)
        if not pos:
            return
        
        dx, dy = direction.value
        new_pos = (pos.x + dx, pos.y + dy)
        
        self.world.post(MoveRequested(self.player_eid, new_pos))
    
    def _handle_descend(self):
        """Handle descending stairs"""
        pos = self.world.get(self.player_eid, CPosition)
        if pos:
            self.world.post(DescendRequested(self.player_eid, (pos.x, pos.y)))