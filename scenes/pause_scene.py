# scenes/pause_scene.py
"""Pause menu scene"""
import pygame
from core.scene_manager import Scene

class PauseScene(Scene):
    def __init__(self, scene_manager, config):
        super().__init__(scene_manager, config)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
    
    def handle_input(self, event, input_handler):
        if event.type == pygame.KEYDOWN:
            action = input_handler.get_action(pygame.key.name(event.key))
            if action == 'pause' or event.key == pygame.K_ESCAPE:
                self.scene_manager.pop()  # Return to game
    
    def update(self, dt):
        pass
    
    def render(self, screen):
        # Semi-transparent overlay
        overlay = pygame.Surface(screen.get_size())
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Pause menu
        pause_text = self.font.render("PAUSED", True, (255, 255, 255))
        pause_rect = pause_text.get_rect(center=(screen.get_width()//2, screen.get_height()//2 - 30))
        screen.blit(pause_text, pause_rect)
        
        resume_text = self.small_font.render("Press ESC to resume", True, (255, 255, 255))
        resume_rect = resume_text.get_rect(center=(screen.get_width()//2, screen.get_height()//2 + 10))
        screen.blit(resume_text, resume_rect)
