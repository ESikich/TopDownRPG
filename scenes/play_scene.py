# scenes/play_scene.py
"""Main gameplay scene"""
import pygame
import random
from core.scene_manager import Scene
from gameplay.ecs.world import World
from gameplay.ecs.components import CVisible, CPosition, CDescriptor
from gameplay.ecs.systems.movement_system import MovementSystem
from gameplay.ecs.systems.combat_system import CombatSystem
from gameplay.ecs.systems.fov_system import FOVSystem
from gameplay.ecs.systems.ai_system import AISystem
from gameplay.ecs.systems.inventory_system import InventorySystem
from gameplay.ecs.systems.input_system import InputSystem
from gameplay.dungeon.generator import DungeonGenerator
from gameplay.content.factories import spawn_player, spawn_monster, spawn_item
from ui.hud import HUD
from ui.message_log import MessageLog
from core.events import Message, DescendRequested, EntityDied
from util.rng import GameRNG

class PlayScene(Scene):
    def __init__(self, scene_manager, config):
        super().__init__(scene_manager, config)
        
        # Initialize game state
        self.world = World()
        self.rng = GameRNG(config['gameplay'].get('seed', 42))
        
        # Generate dungeon
        generator = DungeonGenerator(self.rng.rng)
        dungeon_data = generator.generate(25, 17)  # Adjust size as needed
        self.dungeon_grid = dungeon_data['grid']
        self.rooms = dungeon_data['rooms']
        
        # Create player
        if self.rooms:
            start_room = self.rooms[0]
            self.player_eid = spawn_player(self.world, (start_room.center_x, start_room.center_y))
        else:
            self.player_eid = spawn_player(self.world, (5, 5))
        
        # Spawn some monsters
        self._spawn_monsters()
        
        # Initialize systems
        self.movement_system = MovementSystem(self.world, self.dungeon_grid)
        self.combat_system = CombatSystem(self.world, self.rng.rng)
        self.fov_system = FOVSystem(self.world, self.dungeon_grid)
        self.ai_system = AISystem(self.world, self.player_eid, self.dungeon_grid, self.rng.rng)
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
    
    def _spawn_monsters(self):
        """Spawn monsters in random rooms"""
        if len(self.rooms) > 1:
            # Skip first room (player spawn)
            monster_rooms = self.rng.sample(self.rooms[1:], min(3, len(self.rooms) - 1))
            
            for room in monster_rooms:
                x = self.rng.randint(room.x, room.x + room.width - 1)
                y = self.rng.randint(room.y, room.y + room.height - 1)
                spawn_monster(self.world, "slime", (x, y), self.rng.rng)
    
    def handle_input(self, event, input_handler):
        if event.type == pygame.KEYDOWN:
            key_name = pygame.key.name(event.key)
            action = input_handler.get_action(key_name)
            
            if action == 'pause':
                from scenes.pause_scene import PauseScene
                self.scene_manager.push(PauseScene(self.scene_manager, self.config))
                return
            
            if action == 'restart':
                # Restart the game
                self.scene_manager.replace(PlayScene(self.scene_manager, self.config))
                return
            
            if action and not self.game_over:
                direction = input_handler.get_direction(action)
                self.input_system.handle_action(action, direction)
                
                # Process player turn
                self._process_turn()
    
    def _process_turn(self):
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
                    self.message_log.add_message("You have died! Press R to restart.", 10000)
            elif isinstance(event, DescendRequested):
                self._descend_stairs()
        
        self.turn_count += 1
    
    def _descend_stairs(self):
        """Handle descending to next floor"""
        # Check if player is on stairs
        player_pos = self.world.get(self.player_eid, self.world._components[type(self.world.get(self.player_eid, list(self.world._components.keys())[0]))])
        # For now, just show a message
        self.message_log.add_message("You descend the stairs... (Not implemented yet)")
    
    def update(self, dt):
        self.message_log.update(dt * 1000)  # Convert to milliseconds
    
    def render(self, screen):
        screen.fill((0, 0, 0))
        
        # Render dungeon and entities
        self._render_dungeon(screen)
        self._render_entities(screen)
        
        # Render UI
        self.hud.render(screen, self.world, self.player_eid)
        self.message_log.render(screen)
    
    def _render_dungeon(self, screen):
        """Render the dungeon tiles"""
        tile_size = self.config['gameplay']['tile_size']
        
        # Get player visibility
        player_visible = self.world.get(self.player_eid, CVisible)
        
        for y, row in enumerate(self.dungeon_grid):
            for x, tile in enumerate(row):
                rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                
                # Check if tile is visible or seen
                is_visible = False
                is_seen = False
                
                if player_visible:
                    is_visible = (x, y) in player_visible.visible_tiles
                    is_seen = (x, y) in player_visible.seen_tiles
                
                if is_visible:
                    # Render normally
                    pygame.draw.rect(screen, tile.color, rect)
                    if tile.glyph and tile.glyph != '.':
                        font = pygame.font.Font(None, tile_size)
                        text = font.render(tile.glyph, True, (255, 255, 255))
                        text_rect = text.get_rect(center=rect.center)
                        screen.blit(text, text_rect)
                elif is_seen:
                    # Render dimmed (fog of war)
                    dimmed_color = tuple(c // 3 for c in tile.color)
                    pygame.draw.rect(screen, dimmed_color, rect)
                else:
                    # Not seen - render as black/fog
                    pygame.draw.rect(screen, (32, 32, 48), rect)
    
    def _render_entities(self, screen):
        """Render all visible entities"""
        tile_size = self.config['gameplay']['tile_size']
        player_visible = self.world.get(self.player_eid, CVisible)
        
        # Render entities with position and descriptor
        for eid in self.world.entities_with(CPosition, CDescriptor):
            pos = self.world.get(eid, CPosition)
            desc = self.world.get(eid, CDescriptor)
            
            # Check if entity is visible
            if player_visible and (pos.x, pos.y) in player_visible.visible_tiles:
                rect = pygame.Rect(pos.x * tile_size, pos.y * tile_size, tile_size, tile_size)
                
                # Parse color
                color = self._parse_color(desc.color)
                
                # Render glyph
                font = pygame.font.Font(None, tile_size)
                text = font.render(desc.glyph, True, color)
                text_rect = text.get_rect(center=rect.center)
                screen.blit(text, text_rect)
    
    def _parse_color(self, color_name: str) -> tuple:
        """Parse color name to RGB tuple"""
        color_map = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
            'gray': (128, 128, 128),
            'brown': (139, 69, 19),
            'purple': (128, 0, 128)
        }
        return color_map.get(color_name.lower(), (255, 255, 255))