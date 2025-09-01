# ECS Dungeon Crawler - Code Architecture

This README documents the architecture of the modular ECS (Entity‑Component‑System) dungeon crawler. The project began as a monolithic Pygame implementation and has been refactored into a well‑structured, testable architecture. Recent changes introduced a dramatic combat interface, a combat state manager and a debugging tool, which are noted throughout this document.

## Core Architecture Principles

- **Entities**: Just integer IDs. They have no behavior or data of their own.
- **Components**: Pure data structures (Python dataclasses). They contain state but no game logic.
- **Systems**: All game logic lives in systems. A system operates on entities that possess specific combinations of components.
- **Events**: Systems communicate by posting and consuming events. Events are processed in a FIFO queue each turn.

## Directory Structure

    TopDownRPG/
    ├── main.py                    # Entry point
    ├── debug_system.py            # Debugging tool for printing entity positions and FOV
    ├── config/
    │   ├── settings.toml         # Window, gameplay, colour configuration
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
    ├── ui/                       # Rendering components and interfaces
    │   ├── hud.py               # Player stats display
    │   ├── message_log.py       # Scrolling game messages
    │   └── combat_ui.py         # NEW: Dramatic combat interface
    ├── gameplay/                 # Core game logic (Pygame-agnostic)
    │   ├── ecs/                 # Entity-Component-System
    │   │   ├── world.py         # Entity/component management
    │   │   ├── components.py    # All component definitions
    │   │   └── systems/         # Game logic systems
    │   │       ├── movement_system.py
    │   │       ├── combat_system.py    # Improved with UI integration
    │   │       ├── combat_state_system.py  # NEW: Manage combat participants & locking
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
    │   │   ├── attack.py        # To‑hit calculation
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

## Key Systems Overview

### World (`gameplay/ecs/world.py`)

Central ECS coordinator. Manages entity IDs, component storage and event queue. Provides helper functions such as `create_entity`, `add`, `get`, `entities_with`, `post` and `drain_events`.

### Turn Processing (`scenes/play_scene.py`)

The game is strictly turn‑based. Each turn follows this order:

1. **Player Input** → processed by movement, combat and inventory systems.
2. **Monster AI** → processed by AI, movement and combat systems.
3. **FOV Update** for entities with vision.
4. **Event Handling** – death, messages and special events like stairs.

### Combat Rules (`gameplay/rules/`)

- **To‑hit**: d20 + accuracy vs 10 + evasion (nat1 is always a miss, nat20 a hit).
- **Damage**: Dice + attribute modifiers, doubled dice on crit.
- **Physical damage**: Reduced by armor soak then resistance.
- **Spell damage**: Ignores soak, reduced by spell_resist then resist.

### Content System (`gameplay/content/`)

JSON‑driven entity creation. Each content entry defines a name, glyph, colour and list of components. Factories create entities from these definitions and register them for lookup.

## Component Reference

### Core Components
- `CPosition(x, y, z=0)`: World coordinates.
- `CHealth(hp, max_hp, is_dead=False)`: Life tracking.
- `CStats(str, agi, int, accuracy, evasion, crit_chance, crit_mult)`: Attributes.
- `CBlocker(passable)`: Movement collision.

### Combat Components
- `CWeapon(damage_dice, damage_type, reach=1, tags=[])`: Attack capability.
- `CArmor(soak_dice, resist={}, spell_resist={})`: Damage mitigation.
- `CStatus(effects=[])`: Temporary status effects.

### AI/Player Components
- `CVision(radius)`: FOV calculation input.
- `CVisible(visible_tiles=set, seen_tiles=set)`: FOV results cache.
- `CAI(behavior, memory={})`: AI type and state.
- `CInventory(capacity, items=[])`: Item storage.
- `CEquipment(slots={})`: Worn gear.
- `CSpellbook(spells=[], mp, max_mp)`: Spell access.

## Event Flow

Events enable loose coupling between systems. A typical flow is:

1. **Input System**: Converts key presses to `MoveRequested(eid, target_xy)` events.
2. **Movement System**: Moves entities or posts `AttackRequested` events.
3. **Combat System**: Resolves attacks, applies damage and posts `DamageApplied` and `EntityDied` events.
4. **UI Systems**: Listen for `Message` events to display feedback.

## Data Flow Patterns

### Entity Creation

1. Call `spawn_player/monster/item()` in `factories.py`.
2. Look up JSON data in `registries.py`.
3. Create a new entity ID via `world.create_entity()`.
4. Attach components specified in JSON data.

### System Queries

    # Find all entities with position and health
    for eid in world.entities_with(CPosition, CHealth):
        pos = world.get(eid, CPosition)
        health = world.get(eid, CHealth)
        # Process entity...

### Event Communication

    # System A posts event
    world.post(AttackRequested(attacker_eid, target_eid))

    # System B processes during its turn
    events = world.drain_events()
    for event in events:
        if isinstance(event, AttackRequested):
            # Handle attack...

## Combat UI & State (NEW)

Recent updates added a dramatic combat interface and a combat state manager. When an attack occurs, a **Combat UI** sequence plays through messages announcing the attacker, hit/miss result, damage breakdown and target health. Critical hits trigger screen flashes and special messaging. The UI queues multiple attacker sequences and renders them in order.

Combat is now governed by a **CombatStateSystem** that tracks all participants in an encounter, posts `CombatStarted` and `CombatEnded` events and prevents entities from fleeing until combat resolves. This ensures movement and AI behaviours respect engagement restrictions.

An optional **debug_system.py** module prints turn numbers, entity positions, movement events and FOV visibility to the console. Integrate it into the turn loop to aid troubleshooting.

## Configuration Files

### `config/settings.toml`
- Window dimensions, tile size and UI height.
- Gameplay constants (vision radius, crit multiplier, default random seed).
- Colour palette definitions.

### `config/keybinds.toml`
Defines key mappings by category. Multiple keys can map to the same action; for example `W` and `Up` both move the player north. Bindings can be customised by editing this file.

## Testing Architecture

The modular ECS design supports focused testing:

- **Rules**: Test dice rolling and damage calculations in isolation.
- **Systems**: Mock world/components to test logic (e.g., combat system without graphics).
- **Content**: Validate JSON schemas and factory creation.
- **Integration**: Simulate full turn processing with known seeds.

## Extension Points

### Adding New Content
1. Define your item, monster or spell in the appropriate JSON file in `gameplay/data/`.
2. Reference it by ID in the `spawn_*()` factory functions.
3. No code changes are required for basic content additions.

### Adding New Components
1. Add a dataclass to `components.py`.
2. Update `factories.py` if your content uses the component.
3. Create or modify systems that use the new component.

### Adding New Systems
1. Create a class in `systems/` with a `process()` method.
2. Implement logic using world queries and events.
3. Add the system to the scene’s system list and turn processing order.

## Performance Considerations

- Entity queries are O(number of entities) but filtered by component presence.
- FOV recalculation runs only for entities with `CVision`.
- The event queue is cleared each turn to prevent memory growth.
- Spatial queries (`entities_at`) iterate all position entities.

## Common Patterns

### System Initialization

    def __init__(self, world: World, additional_deps=None):
        self.world = world
        self.additional_deps = additional_deps

### Event Processing

    def process(self):
        events = self.world.drain_events()
        for event in events:
            if isinstance(event, RelevantEvent):
                self._handle_event(event)

### Component Updates

    # Get component, modify in place, no need to re-add
    health = self.world.get(eid, CHealth)
    if health:
        health.hp -= damage

This architecture separates concerns cleanly: Pygame handles presentation, ECS handles game state, and events coordinate between subsystems. The result is testable, extensible code with clear data flow.
