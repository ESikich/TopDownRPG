# gameplay/content/factories.py
"""Entity creation factories"""
from gameplay.ecs.world import World
from gameplay.ecs.components import *
from gameplay.content.registries import content_registry
from core.types import Point

def spawn_player(world: World, xy: Point) -> int:
    """Create player entity"""
    eid = world.create_entity()
    x, y = xy
    
    # Add core components
    world.add(eid, CPosition(x, y))
    world.add(eid, CHealth(100, 100))
    world.add(eid, CStats(
        strength=12, agility=14, intellect=10,
        accuracy=5, evasion=3, crit_chance=10.0, crit_mult=2.0
    ))
    world.add(eid, CVision(5))
    world.add(eid, CInventory(20))
    world.add(eid, CEquipment())
    world.add(eid, CSpellbook(["firebolt"]))
    world.add(eid, CBlocker(False))  # Player blocks movement
    world.add(eid, CDescriptor("Hero", "@", "blue"))
    
    return eid

def spawn_monster(world: World, monster_id: str, xy: Point, rng=None) -> int:
    """Create monster entity from registry data"""
    monster_data = content_registry.monsters.get(monster_id)
    if not monster_data:
        raise ValueError(f"Unknown monster: {monster_id}")
    
    eid = world.create_entity()
    x, y = xy
    
    # Add position
    world.add(eid, CPosition(x, y))
    
    # FIXED: Monsters should block movement (passable=False)
    world.add(eid, CBlocker(passable=False))  # This was the key issue!
    
    # Add descriptor
    world.add(eid, CDescriptor(
        monster_data["name"],
        monster_data["glyph"], 
        monster_data["color"]
    ))
    
    # Add vision for AI
    world.add(eid, CVision(4))
    
    # Add components from data
    for component_name, component_data in monster_data["components"].items():
        component_class = globals().get(component_name)
        if component_class:
            if isinstance(component_data, dict):
                component = component_class(**component_data)
            else:
                component = component_class(component_data)
            world.add(eid, component)
    
    # DEBUG: Print what we created
    print(f"Created monster {eid} ({monster_data['name']}) at ({x}, {y})")
    
    return eid

def spawn_item(world: World, item_id: str, xy: Point) -> int:
    """Create item entity from registry data"""
    item_data = content_registry.items.get(item_id)
    if not item_data:
        raise ValueError(f"Unknown item: {item_id}")
    
    eid = world.create_entity()
    x, y = xy
    
    # Add position and descriptor
    world.add(eid, CPosition(x, y))
    world.add(eid, CDescriptor(
        item_data["name"],
        item_data["glyph"],
        item_data["color"]
    ))
    
    # Items don't block movement
    world.add(eid, CBlocker(True))
    
    # Add components from data
    for component_name, component_data in item_data.get("components", {}).items():
        component_class = globals().get(component_name)
        if component_class:
            if isinstance(component_data, dict):
                component = component_class(**component_data)
            else:
                component = component_class(component_data)
            world.add(eid, component)
    
    return eid
