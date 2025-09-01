# ui/message_log.py
"""Enhanced message logging system with better visibility"""
import pygame
from typing import List, Tuple
import time

class MessageLog:
    def __init__(self, max_messages: int = 15):
        self.max_messages = max_messages
        self.messages: List[Tuple[str, float, str]] = []  # (message, expire_time, priority)
        self.font = pygame.font.Font(None, 24)  # Larger font
        self.small_font = pygame.font.Font(None, 20)
    
    def add_message(self, text: str, ttl_ms: int = 4000, priority: str = "normal"):
        """Add a message with time-to-live and priority"""
        expire_time = time.time() * 1000 + ttl_ms
        self.messages.append((text, expire_time, priority))
        
        # Keep only recent messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
        
        # Print to console for immediate feedback
        print(f"MESSAGE: {text}")
    
    def update(self, current_time_ms: float):
        """Remove expired messages"""
        current_time = time.time() * 1000
        self.messages = [(msg, exp, pri) for msg, exp, pri in self.messages if exp > current_time]
    
    def render(self, screen):
        """Render active messages with better visibility"""
        if not self.messages:
            return
        
        # Show more messages and make them more prominent
        recent_messages = self.messages[-8:]  # Show last 8 messages
        
        # Create semi-transparent background for messages
        if recent_messages:
            msg_height = len(recent_messages) * 28 + 10
            msg_bg = pygame.Surface((screen.get_width() - 20, msg_height))
            msg_bg.set_alpha(180)
            msg_bg.fill((0, 0, 0))
            screen.blit(msg_bg, (10, 10))
        
        y_offset = 15
        for message, expire_time, priority in recent_messages:
            current_time = time.time() * 1000
            remaining = expire_time - current_time
            
            if remaining > 0:
                # Different colors for different priorities/types
                color = (255, 255, 255)  # Default white
                font = self.font
                
                if "attack" in message.lower() or "deals" in message.lower():
                    color = (255, 100, 100)  # Red for damage
                    font = self.font  # Keep large
                elif "miss" in message.lower():
                    color = (150, 150, 150)  # Gray for misses
                elif "critical" in message.lower().replace("!", ""):
                    color = (255, 255, 0)  # Yellow for crits
                    font = self.font
                elif "defeated" in message.lower() or "died" in message.lower():
                    color = (255, 50, 50)  # Bright red for deaths
                    font = self.font
                elif "hp" in message.lower():
                    color = (100, 255, 100)  # Green for health status
                    font = self.small_font
                
                # Calculate alpha based on remaining time (fade out in last second)
                if remaining < 1000:  # Last second
                    alpha = max(50, int(remaining / 1000 * 255))
                else:
                    alpha = 255
                
                # Render text
                text_surface = font.render(message, True, color)
                if alpha < 255:
                    # Create alpha surface for fading
                    alpha_surface = pygame.Surface(text_surface.get_size())
                    alpha_surface.set_alpha(alpha)
                    alpha_surface.blit(text_surface, (0, 0))
                    screen.blit(alpha_surface, (15, y_offset))
                else:
                    screen.blit(text_surface, (15, y_offset))
                
                y_offset += 28