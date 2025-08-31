# ui/message_log.py
"""Message logging system"""
import pygame
from typing import List, Tuple
import time

class MessageLog:
    def __init__(self, max_messages: int = 10):
        self.max_messages = max_messages
        self.messages: List[Tuple[str, float]] = []  # (message, expire_time)
        self.font = pygame.font.Font(None, 20)
    
    def add_message(self, text: str, ttl_ms: int = 3000):
        """Add a message with time-to-live"""
        expire_time = time.time() * 1000 + ttl_ms
        self.messages.append((text, expire_time))
        
        # Keep only recent messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def update(self, current_time_ms: float):
        """Remove expired messages"""
        current_time = time.time() * 1000
        self.messages = [(msg, exp) for msg, exp in self.messages if exp > current_time]
    
    def render(self, screen):
        """Render active messages"""
        if not self.messages:
            return
        
        y_offset = 10
        for message, expire_time in self.messages[-5:]:  # Show last 5 messages
            # Calculate alpha based on remaining time
            current_time = time.time() * 1000
            remaining = expire_time - current_time
            
            if remaining > 0:
                alpha = min(255, max(50, int(remaining / 10)))  # Fade out effect
                
                # Create surface for alpha blending
                text_surface = self.font.render(message, True, (255, 255, 255))
                alpha_surface = pygame.Surface(text_surface.get_size())
                alpha_surface.set_alpha(alpha)
                alpha_surface.blit(text_surface, (0, 0))
                
                screen.blit(alpha_surface, (10, y_offset))
                y_offset += 25