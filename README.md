# ECS Dungeon Crawler - Code Architecture

This README documents the architecture of the modular ECS (Entity-Component-System) dungeon crawler, refactored from a monolithic Pygame implementation.

## Core Architecture Principles

- **Entities**: Just integer IDs. No behavior, no data.
- **Components**: Pure data structures (dataclasses). No methods except properties.
- **Systems**: All game logic. Operate on entities with specific component combinations.
- **Events**: Communication between systems. FIFO queue processed each turn.

## Directory Structure

```
dungeon_crawler/
├── main.py                    # Entry point
├── config/
│   ├── settings.toml         # Window, gameplay, color configuration  
│   └── keybinds.toml         # Input mappings
├── core/                     # Pygame-specific infrastructure
│   ├── app.py               # Main application loop
│   ├── scene_manager.py     # Scene stack management
│   ├── events.py            # Event type definitions
│   ├── input.py             # Input handling and key mapping
│   └── types.py             # Core type definitions (Point, Rect, etc.)
├── scenes/                   # Game scenes
│   ├── start_scene.py       # Title screen
│   ├── play_scene.py        # Main gameplay scene
│   └── pause_scene.py       # Pause overlay
├── ui/                       # Rendering components
│   ├── hud.py               # Player stats display
│   └── message_log.py       # Scrolling game messages
├── gameplay/                 # Core game logic (Pygame-agnostic)
│   ├── ecs/                 # Entity-Component-System
│   │   ├── world.py         # Entity/component management
│   │   ├── components.py    # All component definitions
│   │   └── systems/         # Game logic systems
│   │       ├── movement_system.py
│   │       ├── combat_system.py
│   │       ├── fov_system.py
│   │       ├── ai_system.py
│   │       ├── inventory_system.py
│   │       └── input_system.py
│   ├── dungeon/             # Map generation and FOV
│   │   ├── tiles.py         # Tile type definitions
│   │   ├── generator.py     # Dungeon generation algorithm
│   │   └── fov.py           # Field of view calculation
│   ├── rules/               # Game mechanics
│   │   ├── dice.py          # Dice rolling with attribute modifiers
│   │   ├── attack.py        # To-hit calculation
│   │   └── damage.py        # Damage calculation and resistance
│   ├── content/             # Data-driven content
│   │   ├── registries.py    # Runtime content storage
│   │   └── factories.py     # Entity creation from JSON data
│   └── data/                # JSON content files
│       ├── items.json
│       ├── monsters.json
│       ├── spells.json
│       └── loot_tables.json
└── util/                     # Generic utilities
    ├── rng.py               # Centralized random number generation
    └── pathfinding.py       # A* pathfinding for AI
```

## Key Systems Overview

### World (`gameplay/ecs/world.py`)
Central ECS coordinator. Manages entity IDs, component storage, and event queue.

**Key APIs:**
- `create_entity()` → int: Generate new entity ID
- `add(eid, component)`: Attach component to entity
- `get(eid, ComponentType)` → component: Retrieve component
- `entities_with(*ComponentTypes)` → Iterable[int]: Query entities
- `post(event)`: Add event to queue
- `drain_events()` → List[Event]: Get and clear event queue

### Turn Processing (`scenes/play_scene.py`)
Strict turn-based execution:
1. Process player input → movement/combat systems
2. Process monster AI → movement/combat systems  
3. Update FOV for all entities with vision
4. Handle death, messages, and special events

### Combat Rules (`gameplay/rules/`)
- **To-hit**: d20 + accuracy vs 10 + evasion (nat1 miss, nat20 hit)
- **Damage**: Dice + attribute modifiers, doubled dice on crit
- **Physical damage**: Reduced by armor soak then resistance
- **Spell damage**: Ignores soak, reduced by spell_resist then resist

### Content System (`gameplay/content/`)
JSON-driven entity creation. Each content type defines:
- Visual representation (name, glyph, color)
- Components to attach with their data
- Registry lookup by string ID

## Component Reference

### Core Components
- `CPosition(x, y, z=0)`: World coordinates
- `CHealth(hp, max_hp, is_dead=False)`: Life tracking
- `CStats(str, agi, int, accuracy, evasion, crit_chance, crit_mult)`: Attributes
- `CBlocker(passable)`: Movement collision

### Combat Components  
- `CWeapon(damage_dice, damage_type, reach=1, tags=[])`: Attack capability
- `CArmor(soak_dice, resist={}, spell_resist={})`: Damage mitigation
- `CStatus(effects=[])`: Temporary status effects

### AI/Player Components
- `CVision(radius)`: FOV calculation input
- `CVisible(visible_tiles=set, seen_tiles=set)`: FOV results cache
- `CAI(behavior, memory={})`: AI type and state
- `CInventory(capacity, items=[])`: Item storage
- `CEquipment(slots={})`: Worn gear
- `CSpellbook(spells=[], mp, max_mp)`: Spell access

## Event Flow

Events enable loose coupling between systems:

1. **Input System**: Converts key presses to `MoveRequested(eid, target_xy)`
2. **Movement System**: Processes moves, posts `MoveResolved` or `AttackRequested`  
3. **Combat System**: Handles attacks, posts `DamageApplied` and `EntityDied`
4. **UI Systems**: Listen for `Message` events to display feedback

## Data Flow Patterns

### Entity Creation
1. `spawn_player/monster/item()` in `factories.py`
2. Look up JSON data in `registries.py`
3. Create entity ID via `world.create_entity()`
4. Attach components specified in JSON data

### System Queries
```python
# Find all entities with position and health
for eid in world.entities_with(CPosition, CHealth):
    pos = world.get(eid, CPosition) 
    health = world.get(eid, CHealth)
    # Process entity...
```

### Event Communication
```python
# System A posts event
world.post(AttackRequested(attacker_eid, target_eid))

# System B processes during its turn
events = world.drain_events()
for event in events:
    if isinstance(event, AttackRequested):
        # Handle attack...
```

## Configuration Files

### `config/settings.toml`
- Window dimensions, tile size
- Gameplay constants (vision radius, crit multiplier)  
- Color palette definitions

### `config/keybinds.toml`
- Key mappings organized by category
- Multiple keys can map to same action
- Input system translates keys to action strings

## Testing Architecture

The modular design supports focused testing:

- **Rules**: Test dice rolling, damage calculation in isolation
- **Systems**: Mock world/components to test logic
- **Content**: Validate JSON schemas and factory creation
- **Integration**: Full turn processing with known seeds

## Extension Points

### Adding New Content
1. Define in appropriate JSON file (`items.json`, `monsters.json`, etc.)
2. Reference by ID in `spawn_*()` factory functions
3. No code changes required for basic content

### Adding New Components  
1. Add dataclass to `components.py`
2. Update `factories.py` if content needs it
3. Create/modify systems that use the component

### Adding New Systems
1. Create class in `systems/` directory
2. Implement `process()` method using world queries
3. Add to scene's system list and turn processing order

## Performance Considerations

- Entity queries are O(entities) but filtered by component presence
- FOV recalculation only for entities with `CVision` 
- Event queue is cleared each turn to prevent memory growth
- Spatial queries (`entities_at`) iterate all position entities

## Common Patterns

### System Initialization
```python
def __init__(self, world: World, additional_deps=None):
    self.world = world
    self.additional_deps = additional_deps
```

### Event Processing
```python
def process(self):
    events = self.world.drain_events()
    for event in events:
        if isinstance(event, RelevantEvent):
            self._handle_event(event)
```

### Component Updates
```python
# Get component, modify in place, no need to re-add
health = self.world.get(eid, CHealth)
if health:
    health.hp -= damage
```

This architecture separates concerns cleanly: Pygame handles presentation, ECS handles game state, and events coordinate between subsystems. The result is testable, extensible code with clear data flow.