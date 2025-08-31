# gameplay/ecs/systems/inventory_system.py
"""Inventory and equipment system"""
from gameplay.ecs.world import World
from gameplay.ecs.components import CPosition, CInventory, CEquipment, CDescriptor, CWeapon, CArmor
from core.events import MoveResolved, ItemPicked, ItemEquipped, Message

class InventorySystem:
    def __init__(self, world: World):
        self.world = world
    
    def process(self):
        """Process inventory-related events"""
        events = self.world.drain_events()
        
        for event in events:
            if isinstance(event, MoveResolved):
                self._check_item_pickup(event)
    
    def _check_item_pickup(self, event: MoveResolved):
        """Check if entity moved onto an item"""
        eid = event.eid
        to_x, to_y = event.to_xy
        
        # Check if entity has inventory
        inventory = self.world.get(eid, CInventory)
        if not inventory:
            return
        
        # Find items at this position
        items_here = []
        for item_eid in self.world.entities_with(CPosition, CDescriptor):
            item_pos = self.world.get(item_eid, CPosition)
            descriptor = self.world.get(item_eid, CDescriptor)
            
            if (item_pos.x == to_x and item_pos.y == to_y and 
                "item" in descriptor.glyph.lower()):
                items_here.append(item_eid)
        
        # Pick up items if inventory has space
        for item_eid in items_here:
            if len(inventory.items) >= inventory.capacity:
                self.world.post(Message("Inventory full!"))
                break
            
            # Add to inventory and remove from world
            inventory.items.append(item_eid)
            # Remove position component so it's no longer on the map
            pos = self.world.get(item_eid, CPosition)
            if pos:
                self.world._components[CPosition].pop(item_eid, None)
            
            descriptor = self.world.get(item_eid, CDescriptor)
            item_name = descriptor.name if descriptor else "item"
            
            self.world.post(ItemPicked(eid, item_eid))
            self.world.post(Message(f"Picked up {item_name}"))