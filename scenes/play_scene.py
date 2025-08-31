# scenes/play_scene.py
"""Main gameplay scene"""

import random
import pygame
from typing import Any

from core.scene_manager import Scene
from core.events import Message, DescendRequested, EntityDied
from util.rng import GameRNG

from gameplay.ecs.world import World
from gameplay.ecs.components import CVisible, CPosition, CDescriptor
from gameplay.ecs.systems.movement_system import MovementSystem
from gameplay.ecs.systems.combat_system import CombatSystem
from gameplay.ecs.systems.fov_system import FOVSystem
from gameplay.ecs.systems.ai_system import AISystem
from gameplay.ecs.systems.inventory_system import InventorySystem
from gameplay.ecs.systems.input_system import InputSystem
from gameplay.dungeon.generator import DungeonGenerator
from gameplay.dungeon.tiles import TileType
from gameplay.content.factories import spawn_player, spawn_monster, spawn_item

from ui.hud import HUD
from ui.message_log import MessageLog


class PlayScene(Scene):
    def __init__(self, scene_manager: Any, config: dict) -> None:
        super().__init__(scene_manager, config)

        # Initialize game state
        self.world = World()
        self.rng = GameRNG(config["gameplay"].get("seed", 42))

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

        # Initialize systems
        self.movement_system = MovementSystem(self.world, self.dungeon_grid)
        self.combat_system = CombatSystem(self.world, self.rng.rng)
        self.fov_system = FOVSystem(self.world, self.dungeon_grid)
        self.ai_system = AISystem(
            self.world, self.player_eid, self.dungeon_grid, self.rng.rng
        )
        self.inventory_system = InventorySystem(self.world)
        self.input_system = InputSystem(self.world, self.player_eid)

        # UI components
        self.hud = HUD(config)
        self.message_log = MessageLog()

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
                self.input_system.handle_action(action, direction)

                # Process player turn
                self._process_turn()

    def _process_turn(self) -> None:
        """Process a complete game turn"""
        # 1. Process player actions
        self.movement_system.process()
        self.combat_system.process()
        self.inventory_system.process()

        # 2. Process monster AI and actions
        self.ai_system.process()
        self.movement_system.process()
        self.combat_system.process()

        # 3. Update FOV after all movement is complete
        self.fov_system.process()

        # 4. Process remaining events and check game state
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
        self.message_log.update(dt * 1000)  # Convert to milliseconds

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((0, 0, 0))

        # Render dungeon and entities
        self._render_dungeon(screen)
        self._render_entities(screen)

        # Render UI
        self.hud.render(screen, self.world, self.player_eid)
        self.message_log.render(screen)

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
