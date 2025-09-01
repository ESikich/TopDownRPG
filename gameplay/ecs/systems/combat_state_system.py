# gameplay/ecs/systems/combat_state_system.py
"""System to manage combat state and locking"""
from gameplay.ecs.world import World
from gameplay.ecs.components import CPosition, CHealth, CDescriptor
from core.events import AttackRequested, EntityDied, Event
from typing import Set, Tuple
from dataclasses import dataclass

@dataclass
class CombatStarted(Event):
    """Event posted when combat begins"""
    participants: Set[int]

@dataclass
class CombatEnded(Event):
    """Event posted when combat ends"""
    participants: Set[int]

class CombatStateSystem:
    def __init__(self, world: World, player_eid: int):
        self.world = world
        self.player_eid = player_eid
        self.combat_participants: Set[int] = set()
        self.combat_active = False
        
    def process(self):
        """Manage combat state"""
        events = self.world.drain_events()
        
        for event in events:
            if isinstance(event, AttackRequested):
                self._handle_combat_start(event.attacker_eid, event.target_eid)
            elif isinstance(event, EntityDied):
                self._handle_entity_death(event.eid)
        
        # Re-post events for other systems
        for event in events:
            self.world.post(event)
    
    def _handle_combat_start(self, attacker_eid: int, target_eid: int):
        """Handle start of combat"""
        new_participants = {attacker_eid, target_eid}
        
        if not self.combat_active:
            print(f"COMBAT STARTED: {attacker_eid} vs {target_eid}")
            self.combat_active = True
            self.combat_participants = new_participants
            self.world.post(CombatStarted(self.combat_participants.copy()))
        else:
            # Add new participants to existing combat
            self.combat_participants.update(new_participants)
    
    def _handle_entity_death(self, dead_eid: int):
        """Handle entity death and check if combat should end"""
        if dead_eid in self.combat_participants:
            self.combat_participants.remove(dead_eid)
            print(f"Entity {dead_eid} removed from combat. Remaining: {self.combat_participants}")
            
            # Check if combat should end
            if self._should_end_combat():
                self._end_combat()
    
    def _should_end_combat(self) -> bool:
        """Check if combat should end"""
        if len(self.combat_participants) < 2:
            return True
            
        # Check if all remaining participants are not adjacent
        positions = {}
        for eid in self.combat_participants:
            pos = self.world.get(eid, CPosition)
            health = self.world.get(eid, CHealth)
            if pos and health and not health.is_dead:
                positions[eid] = pos
        
        if len(positions) < 2:
            return True
        
        # Check if any two entities are still adjacent
        pos_list = list(positions.items())
        for i in range(len(pos_list)):
            for j in range(i + 1, len(pos_list)):
                eid1, pos1 = pos_list[i]
                eid2, pos2 = pos_list[j]
                
                dx = abs(pos1.x - pos2.x)
                dy = abs(pos1.y - pos2.y)
                distance = max(dx, dy)
                
                if distance <= 1:  # Still adjacent
                    return False
        
        return True  # No one is adjacent anymore
    
    def _end_combat(self):
        """End combat"""
        print(f"COMBAT ENDED. Participants were: {self.combat_participants}")
        ending_participants = self.combat_participants.copy()
        self.combat_active = False
        self.combat_participants.clear()
        self.world.post(CombatEnded(ending_participants))
    
    def is_in_combat(self, eid: int) -> bool:
        """Check if entity is in combat"""
        return eid in self.combat_participants
    
    def can_move_freely(self, eid: int, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
        """Check if entity can move freely or is locked in combat"""
        if not self.is_in_combat(eid):
            return True
        
        # In combat - can only move to adjacent tiles or to attack
        dx = abs(to_pos[0] - from_pos[0])
        dy = abs(to_pos[1] - from_pos[1])
        distance = max(dx, dy)
        
        # Allow movement to adjacent tiles only
        if distance <= 1:
            return True
        
        print(f"Entity {eid} tried to flee combat! Move blocked.")
        return False