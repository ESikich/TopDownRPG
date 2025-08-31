# core/app.py
"""Main application class"""
import pygame
import sys
import toml
from core.scene_manager import SceneManager
from core.input import InputHandler
from scenes.start_scene import StartScene

class App:
    def __init__(self):
        pygame.init()
        self.config = self._load_config()
        self.screen = pygame.display.set_mode((
            self.config['window']['width'],
            self.config['window']['height']
        ))
        pygame.display.set_caption(self.config['window']['title'])
        self.clock = pygame.time.Clock()
        self.input_handler = InputHandler()
        self.scene_manager = SceneManager()
        
        # Start with the start scene
        self.scene_manager.push(StartScene(self.scene_manager, self.config))
        
    def _load_config(self):
        try:
            with open('config/settings.toml', 'r') as f:
                return toml.load(f)
        except FileNotFoundError:
            # Default config if file not found
            return {
                'window': {'width': 800, 'height': 700, 'title': 'ECS Dungeon Crawler'},
                'gameplay': {'tile_size': 32, 'ui_height': 150, 'default_vision_radius': 2},
                'colors': {'black': [0,0,0], 'white': [255,255,255]}
            }
    
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                else:
                    if self.scene_manager.active_scene:
                        self.scene_manager.active_scene.handle_input(event, self.input_handler)
            
            if self.scene_manager.active_scene:
                self.scene_manager.active_scene.update(dt)
                self.scene_manager.active_scene.render(self.screen)
            else:
                running = False
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()