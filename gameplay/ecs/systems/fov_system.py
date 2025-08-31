# gameplay/ecs/systems/fov_system.py
"""Field of View system"""
from gameplay.ecs.world import World
from gameplay.ecs.components import CPosition, CVision, CVisible
from gameplay.dungeon.fov import compute_visible
from core.events import MoveResolved

class FOVSystem:
    def __init__(self, world: World, dungeon_grid=None):
        self.world = world
        self.dungeon_grid = dungeon_grid
    
    def process(self):
        """Update FOV for all entities with vision"""
        # Update FOV for all entities with vision, regardless of movement
        # This ensures FOV is always current
        for eid in self.world.entities_with(CVision, CPosition):
            self._update_fov(eid)
    
    def _update_fov(self, eid: int):
        """Update field of view for a specific entity"""
        pos = self.world.get(eid, CPosition)
        vision = self.world.get(eid, CVision)
        
        if not pos or not vision or not self.dungeon_grid:
            return
        
        # Compute visible tiles
        visible_tiles = compute_visible(self.dungeon_grid, pos.x, pos.y, vision.radius)
        
        # Update or create CVisible component
        visible_comp = self.world.get(eid, CVisible)
        if not visible_comp:
            visible_comp = CVisible()
            self.world.add(eid, visible_comp)
        
        # Update seen tiles (cumulative)
        visible_comp.seen_tiles.update(visible_tiles)
        visible_comp.visible_tiles = visible_tiles