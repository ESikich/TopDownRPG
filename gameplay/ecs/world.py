# gameplay/ecs/world.py
"""ECS World implementation"""
from typing import Dict, List, Type, Any, Iterable, Optional
from collections import defaultdict
from core.events import Event
from gameplay.ecs.components import CPosition, CBlocker

class World:
    def __init__(self):
        self._next_entity_id = 1
        self._entities: set[int] = set()
        self._components: Dict[Type, Dict[int, Any]] = defaultdict(dict)
        self._event_queue: List[Event] = []
        
    def create_entity(self) -> int:
        eid = self._next_entity_id
        self._next_entity_id += 1
        self._entities.add(eid)
        return eid
    
    def destroy_entity(self, eid: int) -> None:
        if eid in self._entities:
            self._entities.remove(eid)
            # Remove all components for this entity
            for component_dict in self._components.values():
                component_dict.pop(eid, None)
    
    def add(self, eid: int, component_obj) -> None:
        component_type = type(component_obj)
        self._components[component_type][eid] = component_obj
    
    def get(self, eid: int, component_type: Type) -> Any:
        return self._components[component_type].get(eid)
    
    def has(self, eid: int, *component_types: Type) -> bool:
        return all(eid in self._components[ct] for ct in component_types)
    
    def entities_with(self, *component_types: Type) -> Iterable[int]:
        if not component_types:
            return iter(self._entities)
        
        # Find intersection of entities that have all required components
        entity_sets = [set(self._components[ct].keys()) for ct in component_types]
        result = entity_sets[0].intersection(*entity_sets[1:]) if entity_sets else set()
        return result.intersection(self._entities)
    
    def post(self, event: Event) -> None:
        self._event_queue.append(event)
    
    def drain_events(self) -> List[Event]:
        events = self._event_queue.copy()
        self._event_queue.clear()
        return events
    
    def entities_at(self, x: int, y: int, *component_types: Type) -> List[int]:
        """Get entities at specific position with optional component filter"""
        entities = []
        for eid in self.entities_with(CPosition, *component_types):
            pos = self.get(eid, CPosition)
            if pos and pos.x == x and pos.y == y:
                entities.append(eid)
        return entities
    
    def is_blocked(self, x: int, y: int, grid=None) -> bool:
        """Check if position is blocked by tile or entity"""
        # Check tile blocking (if grid provided)
        if grid and (x < 0 or y < 0 or y >= len(grid) or x >= len(grid[0])):
            return True
        if grid and not grid[y][x].walkable:
            return True
            
        # Check entity blocking
        for eid in self.entities_at(x, y):
            blocker = self.get(eid, CBlocker)
            if blocker and not blocker.passable:
                return True
        return False