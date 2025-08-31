# scenes/start_scene.py
"""Start scene with title screen"""
import pygame
from core.scene_manager import Scene

class StartScene(Scene):
    def __init__(self, scene_manager, config):
        super().__init__(scene_manager, config)
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)
    
    def handle_input(self, event, input_handler):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                from scenes.play_scene import PlayScene
                self.scene_manager.replace(PlayScene(self.scene_manager, self.config))
    
    def update(self, dt):
        pass
    
    def render(self, screen):
        screen.fill((0, 0, 0))  # Black background
        
        # Title
        title_text = self.font.render("ECS DUNGEON CRAWLER", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(screen.get_width()//2, screen.get_height()//2 - 50))
        screen.blit(title_text, title_rect)
        
        # Instructions
        start_text = self.small_font.render("Press SPACE to start", True, (255, 255, 255))
        start_rect = start_text.get_rect(center=(screen.get_width()//2, screen.get_height()//2 + 20))
        screen.blit(start_text, start_rect)
        
        controls_text = self.small_font.render("WASD to move, I for inventory, C for spells", True, (200, 200, 200))
        controls_rect = controls_text.get_rect(center=(screen.get_width()//2, screen.get_height()//2 + 50))
        screen.blit(controls_text, controls_rect)