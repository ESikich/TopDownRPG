# debug_system.py
"""Debug system to track entity positions and movements"""
from gameplay.ecs.world import World
from gameplay.ecs.components import CPosition, CDescriptor, CHealth
from core.events import MoveResolved

class DebugSystem:
    def __init__(self, world: World, player_eid: int):
        self.world = world
        self.player_eid = player_eid
        self.turn_count = 0
    
    def process_turn_start(self):
        """Call this at the start of each turn"""
        self.turn_count += 1
        print(f"\n=== TURN {self.turn_count} START ===")
        self._print_all_entity_positions()
    
    def process_events(self):
        """Process movement events for debugging"""
        events = self.world.drain_events()
        
        for event in events:
            if isinstance(event, MoveResolved):
                desc = self.world.get(event.eid, CDescriptor)
                name = desc.name if desc else f"Entity {event.eid}"
                print(f"  {name} moved: {event.from_xy} -> {event.to_xy}")
        
        # Re-post events so other systems can process them
        for event in events:
            self.world.post(event)
    
    def _print_all_entity_positions(self):
        """Print positions of all entities"""
        print("Entity positions:")
        
        # Player first
        player_pos = self.world.get(self.player_eid, CPosition)
        if player_pos:
            print(f"  PLAYER (@): ({player_pos.x}, {player_pos.y})")
        
        # All other entities
        for eid in self.world.entities_with(CPosition, CDescriptor):
            if eid == self.player_eid:
                continue
                
            pos = self.world.get(eid, CPosition)
            desc = self.world.get(eid, CDescriptor)
            health = self.world.get(eid, CHealth)
            
            status = ""
            if health and health.is_dead:
                status = " [DEAD]"
            
            print(f"  {desc.name} ({desc.glyph}): ({pos.x}, {pos.y}){status}")
    
    def print_fov_info(self):
        """Print FOV information"""
        from gameplay.ecs.components import CVisible
        
        visible = self.world.get(self.player_eid, CVisible)
        if visible:
            print(f"FOV: {len(visible.visible_tiles)} visible, {len(visible.seen_tiles)} seen")
            print(f"Visible tiles: {sorted(visible.visible_tiles)}")
            
            # Check which entities are in FOV
            visible_entities = []
            for eid in self.world.entities_with(CPosition, CDescriptor):
                if eid == self.player_eid:
                    continue
                pos = self.world.get(eid, CPosition)
                if (pos.x, pos.y) in visible.visible_tiles:
                    desc = self.world.get(eid, CDescriptor)
                    visible_entities.append(f"{desc.name} at ({pos.x}, {pos.y})")
            
            if visible_entities:
                print(f"Entities in FOV: {', '.join(visible_entities)}")
            else:
                print("No entities visible in FOV")