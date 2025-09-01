# ui/message_log.py
"""Enhanced message logging system with better visibility"""
import pygame
from typing import List, Tuple

class MessageLog:
    """
    Enhanced message log that tracks remaining time per message rather than relying
    on absolute wall clock time. This allows the caller to control time
    progression (e.g. freezing message expiry during combat) by passing in
    appropriate `dt` values to `update`. Messages are stored as tuples of
    (text, remaining_ms, priority). When remaining_ms reaches zero the
    message is removed. Rendering fades messages based on their remaining
    lifetime.
    """

    def __init__(self, max_messages: int = 15):
        self.max_messages = max_messages
        # Each message is a tuple: (text, remaining_ms, priority)
        self.messages: List[Tuple[str, float, str]] = []
        self.font = pygame.font.Font(None, 24)  # Larger font
        self.small_font = pygame.font.Font(None, 20)

    def add_message(self, text: str, ttl_ms: int = 4000, priority: str = "normal") -> None:
        """Add a message with a time-to-live (in milliseconds) and priority.

        The TTL is used to initialise the remaining time for the message. The
        `update` method will subtract elapsed time from this value. Messages
        will persist when the elapsed time passed to `update` is zero (e.g. when
        game time is frozen).
        """
        # Append new message with remaining time
        self.messages.append((text, float(ttl_ms), priority))
        # Trim to max_messages by discarding oldest messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
        # Also print to console for debugging/feedback
        print(f"MESSAGE: {text}")

    def update(self, elapsed_ms: float) -> None:
        """Update message lifetimes.

        Decrease the remaining time for each message by `elapsed_ms`. Messages
        whose remaining time drops to zero or below will be removed. If
        `elapsed_ms` is zero, message timers are not advanced, effectively
        pausing expiration.
        """
        if not self.messages:
            return
        # Update remaining time for each message
        updated: List[Tuple[str, float, str]] = []
        for text, remaining_ms, priority in self.messages:
            new_remaining = remaining_ms - elapsed_ms
            if new_remaining > 0:
                updated.append((text, new_remaining, priority))
        self.messages = updated

    def render(self, screen: pygame.Surface) -> None:
        """Render active messages with improved visuals.

        Messages are displayed with semi-transparent background and fade out
        during their final second of lifetime. Colours and font sizes
        differentiate different message types (e.g. damage, misses).
        """
        if not self.messages:
            return

        # Display up to the last 8 messages
        recent_messages = self.messages[-8:]

        # Draw background behind the messages
        if recent_messages:
            msg_height = len(recent_messages) * 28 + 10
            msg_bg = pygame.Surface((screen.get_width() - 20, msg_height))
            msg_bg.set_alpha(180)
            msg_bg.fill((0, 0, 0))
            screen.blit(msg_bg, (10, 10))

        y_offset = 15
        for message, remaining_ms, priority in recent_messages:
            # Determine fade alpha based on remaining time (fade in last second)
            alpha = 255
            if remaining_ms < 1000:  # Fade during final 1000ms
                # Scale alpha between 50 and 255
                alpha = max(50, int((remaining_ms / 1000.0) * 255))

            # Choose colour and font based on message content/priority
            colour = (255, 255, 255)
            font = self.font
            lower_msg = message.lower()
            if "attack" in lower_msg or "deals" in lower_msg:
                colour = (255, 100, 100)
            elif "miss" in lower_msg:
                colour = (150, 150, 150)
            elif "critical" in lower_msg.replace("!", ""):
                colour = (255, 255, 0)
            elif "defeated" in lower_msg or "died" in lower_msg:
                colour = (255, 50, 50)
            elif "hp" in lower_msg:
                colour = (100, 255, 100)
                font = self.small_font

            text_surface = font.render(message, True, colour)
            if alpha < 255:
                # Apply fading alpha to the text
                alpha_surface = pygame.Surface(text_surface.get_size())
                alpha_surface.set_alpha(alpha)
                alpha_surface.blit(text_surface, (0, 0))
                screen.blit(alpha_surface, (15, y_offset))
            else:
                screen.blit(text_surface, (15, y_offset))
            y_offset += 28
