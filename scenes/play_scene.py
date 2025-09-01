# scenes/play_scene.py
"""Main gameplay scene with dramatic combat UI"""

import time
import pygame
from typing import Any

from core.scene_manager import Scene
from core.events import Message, DescendRequested, EntityDied
from util.rng import GameRNG

from gameplay.ecs.world import World
from gameplay.ecs.components import CVisible, CPosition, CDescriptor, CHealth, CBlocker
from gameplay.ecs.systems.movement_system import MovementSystem
from gameplay.ecs.systems.combat_system import CombatSystem
from gameplay.ecs.systems.fov_system import FOVSystem
from gameplay.ecs.systems.ai_system import AISystem
from gameplay.ecs.systems.inventory_system import InventorySystem
from gameplay.ecs.systems.input_system import InputSystem
from gameplay.ecs.systems.combat_state_system import CombatStateSystem
from gameplay.dungeon.generator import DungeonGenerator
from gameplay.dungeon.tiles import TileType
from gameplay.content.factories import spawn_player, spawn_monster, spawn_item

from ui.hud import HUD
from ui.message_log import MessageLog
from ui.combat_ui import CombatUI  # Add this import


class PlayScene(Scene):
    def __init__(self, scene_manager: Any, config: dict) -> None:
        super().__init__(scene_manager, config)

        # Initialize game state
        self.world = World()
        seed = config["gameplay"].get("seed", int(time.time()))
        self.rng = GameRNG(int(time.time()))

        # Generate dungeon
        generator = DungeonGenerator(self.rng.rng)
        dungeon_data = generator.generate(25, 17)  # Adjust size as needed
        self.dungeon_grid = dungeon_data["grid"]
        self.rooms = dungeon_data["rooms"]

        # Create player
        if self.rooms:
            start_room = self.rooms[0]
            self.player_eid = spawn_player(
                self.world, (start_room.center_x, start_room.center_y)
            )
        else:
            self.player_eid = spawn_player(self.world, (5, 5))

        # Spawn some monsters
        self._spawn_monsters()

        # Initialize UI components FIRST
        self.hud = HUD(config)
        self.message_log = MessageLog()
        self.combat_ui = CombatUI(config)  # Initialize combat UI here

        # Initialize systems WITH combat integration
        self.combat_state_system = CombatStateSystem(self.world, self.player_eid)
        self.movement_system = MovementSystem(self.world, self.dungeon_grid, self.combat_state_system)
        self.combat_system = CombatSystem(self.world, self.rng.rng, self.combat_ui, self.player_eid)
        self.fov_system = FOVSystem(self.world, self.dungeon_grid)
        self.ai_system = AISystem(
            self.world, self.player_eid, self.dungeon_grid, self.rng.rng
        )
        self.inventory_system = InventorySystem(self.world)
        self.input_system = InputSystem(self.world, self.player_eid)

        # Initial FOV calculation
        self.fov_system._update_fov(self.player_eid)

        # Debug: Print initial visibility
        player_visible = self.world.get(self.player_eid, CVisible)
        if player_visible:
            print(f"Initial FOV: {len(player_visible.visible_tiles)} tiles visible")

        # Game state
        self.turn_count = 0
        self.game_over = False

    def _spawn_monsters(self) -> None:
        """Spawn monsters in random rooms"""
        if len(self.rooms) > 1:
            # Skip first room (player spawn)
            monster_rooms = self.rng.sample(
                self.rooms[1:], min(3, len(self.rooms) - 1)
            )

            for room in monster_rooms:
                x = self.rng.randint(room.x, room.x + room.width - 1)
                y = self.rng.randint(room.y, room.y + room.height - 1)
                spawn_monster(self.world, "slime", (x, y), self.rng.rng)

    def handle_input(self, event: pygame.event.Event, input_handler: Any) -> None:
        if event.type == pygame.KEYDOWN:
            key_name = pygame.key.name(event.key)
            action = input_handler.get_action(key_name)

            # Do not allow most player actions while combat UI is playing messages.
            # If the combat UI is actively showing a combat sequence or has messages queued,
            # ignore input to effectively pause the game state until the sequence is done.
            # However, still allow "pause" and "restart" actions so the player can pause
            # or restart the game even during combat animations.
            if self.combat_ui is not None and getattr(self.combat_ui, 'in_combat', False):
                # Only skip input if the action is not pause or restart
                if action not in ("pause", "restart"):
                    return

            if action == "pause":
                from scenes.pause_scene import PauseScene
                self.scene_manager.push(PauseScene(self.scene_manager, self.config))
                return

            if action == "restart":
                # Restart the game
                self.scene_manager.replace(
                    PlayScene(self.scene_manager, self.config)
                )
                return

            if action and not self.game_over:
                direction = input_handler.get_direction(action)
                
                # DEBUG: Check combat before processing
                if direction:
                    player_pos = self.world.get(self.player_eid, CPosition)
                    if player_pos:
                        dx, dy = direction.value
                        target_pos = (player_pos.x + dx, player_pos.y + dy)
                        self.debug_combat_attempt(player_pos, target_pos)
                
                self.input_system.handle_action(action, direction)
                # Process player turn
                self._process_turn()

    def debug_combat_attempt(self, player_pos, target_pos):
        """Debug why combat isn't happening"""
        print(f"\n=== COMBAT DEBUG ===")
        print(f"Player trying to move from ({player_pos.x}, {player_pos.y}) to {target_pos}")
        
        # Check what's at the target position
        entities_at_target = self.world.entities_at(target_pos[0], target_pos[1])
        print(f"Entities at target {target_pos}: {entities_at_target}")
        
        for target_eid in entities_at_target:
            if target_eid == self.player_eid:
                print(f"  - Entity {target_eid}: PLAYER (skipping)")
                continue
                
            pos = self.world.get(target_eid, CPosition)
            desc = self.world.get(target_eid, CDescriptor)
            health = self.world.get(target_eid, CHealth)
            blocker = self.world.get(target_eid, CBlocker)
            
            print(f"  - Entity {target_eid}: {desc.name if desc else 'Unknown'}")
            print(f"    Position: ({pos.x}, {pos.y})")
            print(f"    Health: {health}")
            print(f"    Blocker: {blocker}")
            print(f"    Should trigger combat: {health and not health.is_dead}")

    def _process_turn(self) -> None:
        """Process a complete game turn with proper combat management"""
        # 1. Process combat state changes first
        self.combat_state_system.process()
        
        # 2. Process player actions
        self.movement_system.process()
        self.combat_system.process()
        self.inventory_system.process()

        # 3. Process monster AI and actions  
        print("--- MONSTER AI PHASE ---")
        self.ai_system.process()
        print("--- MONSTER MOVEMENT PHASE ---") 
        self.movement_system.process()
        print("--- MONSTER COMBAT PHASE ---")
        self.combat_system.process()

        # 4. Update FOV after all movement is complete
        self.fov_system.process()

        # 5. Process remaining events and check game state
        events = self.world.drain_events()
        for event in events:
            if isinstance(event, Message):
                self.message_log.add_message(event.text, event.ttl_ms)
            elif isinstance(event, EntityDied):
                if event.eid == self.player_eid:
                    self.game_over = True
                    self.message_log.add_message(
                        "You have died! Press R to restart.", 10000
                    )
            elif isinstance(event, DescendRequested):
                self._descend_stairs()

        self.turn_count += 1

    def _descend_stairs(self) -> None:
        """Handle descending to next floor (placeholder)."""
        pos = self.world.get(self.player_eid, CPosition)
        if not pos:
            return

        # Bounds check in case something moved the player off-map
        if not (
            0 <= pos.y < len(self.dungeon_grid)
            and 0 <= pos.x < len(self.dungeon_grid[pos.y])
        ):
            self.message_log.add_message("You can't descend here.", 2000)
            return

        tile = self.dungeon_grid[pos.y][pos.x]

        # Prefer engine-native type check; fall back to glyph if needed
        on_stairs = False
        if hasattr(tile, "type"):
            try:
                on_stairs = tile.type == TileType.STAIRS_DOWN
            except Exception:
                on_stairs = False

        if not on_stairs and hasattr(tile, "glyph"):
            on_stairs = tile.glyph in (">", "stairs_down")

        if on_stairs:
            self.message_log.add_message(
                "You descend the stairs... (Not implemented yet)"
            )
            # TODO: trigger floor generation / scene transition here
        else:
            self.message_log.add_message("There are no stairs here.", 2000)

    def update(self, dt: float) -> None:
        """
        Update the play scene.

        `dt` is the real elapsed time since the last frame in seconds. When
        combat is active (as tracked by the combat state system), game time
        should be considered frozen for most UI elements so that messages and
        HUD effects do not expire during dramatic combat sequences. To
        accomplish this, we calculate a separate `time_delta_ms` that is
        zero when combat is active and `dt*1000` otherwise. This value is
        passed into the message log and HUD update methods. The combat UI
        always progresses using the real `dt` so that its animations and
        sequences play out smoothly even while the rest of the game is
        paused.
        """
        # Determine if game time should be frozen
        freeze_time = False
        # If combat state system exists and indicates active combat, freeze
        if hasattr(self, 'combat_state_system') and self.combat_state_system.combat_active:
            freeze_time = True
        # Compute elapsed milliseconds for UI updates
        time_delta_ms = 0.0 if freeze_time else dt * 1000.0
        # Update message log (handles message expiry)
        self.message_log.update(time_delta_ms)
        # Update HUD timers (e.g. damage flashes)
        if hasattr(self, 'hud'):
            self.hud.update(time_delta_ms, self.world, self.player_eid)
        # Always update combat UI using real dt so sequences progress
        self.combat_ui.update(dt)

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((0, 0, 0))

        # Render dungeon and entities
        self._render_dungeon(screen)
        self._render_entities(screen)

        # Render UI
        self.hud.render(screen, self.world, self.player_eid)
        self.message_log.render(screen)
        
        # 🎮 RENDER DRAMATIC COMBAT UI 🎮
        self.combat_ui.render(screen)
        
        # Render combat stats overlay if in combat
        self.combat_ui.render_combat_stats_overlay(screen, self.world, self.player_eid)

    def _render_dungeon(self, screen: pygame.Surface) -> None:
        """Render the dungeon tiles"""
        tile_size = self.config["gameplay"]["tile_size"]

        # Get player visibility
        player_visible = self.world.get(self.player_eid, CVisible)

        for y, row in enumerate(self.dungeon_grid):
            for x, tile in enumerate(row):
                rect = pygame.Rect(
                    x * tile_size, y * tile_size, tile_size, tile_size
                )

                is_visible = False
                is_seen = False

                if player_visible:
                    is_visible = (x, y) in player_visible.visible_tiles
                    is_seen = (x, y) in player_visible.seen_tiles

                if is_visible:
                    pygame.draw.rect(screen, tile.color, rect)
                    if tile.glyph and tile.glyph != ".":
                        font = pygame.font.Font(None, tile_size)
                        text = font.render(tile.glyph, True, (255, 255, 255))
                        text_rect = text.get_rect(center=rect.center)
                        screen.blit(text, text_rect)
                elif is_seen:
                    dimmed_color = tuple(c // 3 for c in tile.color)
                    pygame.draw.rect(screen, dimmed_color, rect)
                else:
                    pygame.draw.rect(screen, (32, 32, 48), rect)

    def _render_entities(self, screen: pygame.Surface) -> None:
        """Render all visible entities"""
        tile_size = self.config["gameplay"]["tile_size"]
        player_visible = self.world.get(self.player_eid, CVisible)

        for eid in self.world.entities_with(CPosition, CDescriptor):
            pos = self.world.get(eid, CPosition)
            desc = self.world.get(eid, CDescriptor)

            if player_visible and (pos.x, pos.y) in player_visible.visible_tiles:
                rect = pygame.Rect(
                    pos.x * tile_size, pos.y * tile_size, tile_size, tile_size
                )

                color = self._parse_color(desc.color)

                font = pygame.font.Font(None, tile_size)
                text = font.render(desc.glyph, True, color)
                text_rect = text.get_rect(center=rect.center)
                screen.blit(text, text_rect)

    def _parse_color(self, color_name: str) -> tuple[int, int, int]:
        """Parse color name to RGB tuple"""
        color_map: dict[str, tuple[int, int, int]] = {
            "white": (255, 255, 255),
            "black": (0, 0, 0),
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "gray": (128, 128, 128),
            "brown": (139, 69, 19),
            "purple": (128, 0, 128),
        }
        return color_map.get(color_name.lower(), (255, 255, 255))
