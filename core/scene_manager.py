# core/scene_manager.py
"""Scene management system"""
from typing import List, Optional

class Scene:
    """Base scene class"""
    def __init__(self, scene_manager, config):
        self.scene_manager = scene_manager
        self.config = config
    
    def handle_input(self, event, input_handler):
        pass
    
    def update(self, dt):
        pass
    
    def render(self, screen):
        pass

class SceneManager:
    def __init__(self):
        self.scenes: List[Scene] = []
    
    @property
    def active_scene(self) -> Optional[Scene]:
        return self.scenes[-1] if self.scenes else None
    
    def push(self, scene: Scene):
        self.scenes.append(scene)
    
    def pop(self) -> Optional[Scene]:
        return self.scenes.pop() if self.scenes else None
    
    def replace(self, scene: Scene):
        if self.scenes:
            self.scenes[-1] = scene
        else:
            self.scenes.append(scene)
