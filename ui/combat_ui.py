# ui/combat_ui.py
"""Improved Combat UI system that handles multiple attackers"""
import pygame
import time
from typing import List, Optional, Tuple, Deque
from dataclasses import dataclass
from collections import deque

@dataclass
class CombatSequence:
    attacker_name: str
    target_name: str
    messages: List['CombatMessage']
    start_time: float
    is_player_attacking: bool

@dataclass
class CombatMessage:
    text: str
    color: Tuple[int, int, int]
    size: str
    duration: float

class CombatUI:
    def __init__(self, config):
        self.config = config
        
        # Fonts
        self.fonts = {
            'small': pygame.font.Font(None, 20),
            'normal': pygame.font.Font(None, 28),
            'large': pygame.font.Font(None, 36),
            'huge': pygame.font.Font(None, 48)
        }
        
        # Combat sequence queue
        self.combat_queue: Deque[CombatSequence] = deque()
        self.current_sequence: Optional[CombatSequence] = None
        self.current_message_index = 0
        self.current_message_start = 0
        
        # Visual effects
        self.screen_flash_color = None
        self.screen_flash_end = 0
        
        # State tracking
        self.in_combat = False
        self.combat_end_time = 0
        
        # Message timing
        self.base_message_duration = 1.2
        self.short_message_duration = 0.8
        self.long_message_duration = 2.0
    
    def add_combat_sequence(self, attacker_name: str, target_name: str, 
                          hit: bool, crit: bool, damage: int, 
                          original_damage: int, soak: int,
                          target_hp: int, target_max_hp: int,
                          target_died: bool, is_player_attacking: bool = True):
        """Add a complete combat sequence"""
        messages = []
        
        # 1. Attack announcement
        attack_color = (100, 200, 255) if is_player_attacking else (255, 100, 100)
        messages.append(CombatMessage(
            f"{attacker_name} attacks {target_name}!",
            attack_color,
            "large",
            self.base_message_duration
        ))
        
        # 2. Hit result
        if not hit:
            messages.append(CombatMessage(
                f"{attacker_name} misses!",
                (150, 150, 150),
                "normal",
                self.short_message_duration
            ))
        elif crit:
            messages.append(CombatMessage(
                "💥 CRITICAL HIT! 💥",
                (255, 255, 0),
                "huge",
                self.long_message_duration
            ))
            self.add_screen_flash((150, 150, 0), 0.5)
        else:
            messages.append(CombatMessage(
                f"{attacker_name} hits!",
                (255, 150, 150),
                "large",
                self.base_message_duration
            ))
            flash_color = (0, 100, 0) if is_player_attacking else (100, 0, 0)
            self.add_screen_flash(flash_color, 0.3)
        
        # 3. Damage (if hit)
        if hit and damage > 0:
            damage_text = f"{damage} damage!"
            if soak > 0:
                damage_text += f" ({original_damage} - {soak} armor)"
            
            messages.append(CombatMessage(
                damage_text,
                (255, 50, 50),
                "large",
                self.base_message_duration
            ))
        elif hit and damage == 0:
            messages.append(CombatMessage(
                "No damage!",
                (100, 100, 100),
                "normal",
                self.short_message_duration
            ))
        
        # 4. Health status or death
        if target_died:
            messages.append(CombatMessage(
                f"💀 {target_name} is defeated! 💀",
                (255, 0, 0),
                "huge",
                self.long_message_duration
            ))
            self.add_screen_flash((150, 0, 0), 0.8)
        elif hit and damage > 0:
            health_percent = (target_hp / target_max_hp) * 100
            if health_percent <= 25:
                status_text = f"{target_name} is critically wounded!"
                color = (255, 100, 100)
                size = "large"
            elif health_percent <= 50:
                status_text = f"{target_name} is badly hurt!"
                color = (255, 150, 100)
                size = "normal"
            else:
                status_text = f"{target_name}: {target_hp}/{target_max_hp} HP"
                color = (100, 255, 100)
                size = "small"
            
            messages.append(CombatMessage(
                status_text,
                color,
                size,
                self.base_message_duration
            ))
        
        # Create and queue the sequence
        sequence = CombatSequence(
            attacker_name=attacker_name,
            target_name=target_name,
            messages=messages,
            start_time=time.time(),
            is_player_attacking=is_player_attacking
        )
        
        self.combat_queue.append(sequence)
        self.in_combat = True
        
        print(f"Added combat sequence: {attacker_name} -> {target_name} ({'Player' if is_player_attacking else 'Monster'} attacking)")
    
    def add_screen_flash(self, color: Tuple[int, int, int], duration: float):
        """Add screen flash effect"""
        self.screen_flash_color = color
        self.screen_flash_end = time.time() + duration
    
    def update(self, dt: float):
        """Update combat UI with sequence management"""
        current_time = time.time()
        
        # Start next sequence if none active
        if not self.current_sequence and self.combat_queue:
            self.current_sequence = self.combat_queue.popleft()
            self.current_message_index = 0
            self.current_message_start = current_time
            print(f"Starting combat sequence: {self.current_sequence.attacker_name} attacks")
        
        # Update current sequence
        if self.current_sequence:
            current_msg = self.current_sequence.messages[self.current_message_index]
            message_age = current_time - self.current_message_start
            
            # Check if current message is done
            if message_age >= current_msg.duration:
                self.current_message_index += 1
                
                # Check if sequence is complete
                if self.current_message_index >= len(self.current_sequence.messages):
                    print(f"Completed combat sequence: {self.current_sequence.attacker_name}")
                    self.current_sequence = None
                    self.current_message_index = 0
                    
                    # Add small delay between sequences
                    if self.combat_queue:
                        # Brief pause before next sequence
                        time.sleep(0.2)
                else:
                    # Move to next message in sequence
                    self.current_message_start = current_time
        
        # End combat if no more sequences
        if not self.current_sequence and not self.combat_queue:
            if self.in_combat:
                print("All combat sequences complete - ending combat")
                self.in_combat = False
                self.combat_end_time = current_time + 1.0  # Cooldown
    
    def render(self, screen: pygame.Surface):
        """Render current combat message"""
        current_time = time.time()
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Render screen flash
        if current_time < self.screen_flash_end and self.screen_flash_color:
            remaining_time = self.screen_flash_end - current_time
            flash_alpha = int(min(100, remaining_time * 200))
            
            flash_surface = pygame.Surface((screen_width, screen_height))
            flash_surface.set_alpha(flash_alpha)
            flash_surface.fill(self.screen_flash_color)
            screen.blit(flash_surface, (0, 0))
        
        # Render current message
        if self.current_sequence and self.current_message_index < len(self.current_sequence.messages):
            current_msg = self.current_sequence.messages[self.current_message_index]
            message_age = current_time - self.current_message_start
            remaining_time = current_msg.duration - message_age
            
            # Calculate fade
            if remaining_time < 0.3:
                alpha = max(100, int(remaining_time / 0.3 * 255))
            else:
                alpha = 255
            
            # Render message
            font = self.fonts[current_msg.size]
            text_surface = font.render(current_msg.text, True, current_msg.color)
            
            if alpha < 255:
                alpha_surface = pygame.Surface(text_surface.get_size())
                alpha_surface.set_alpha(alpha)
                alpha_surface.blit(text_surface, (0, 0))
                text_surface = alpha_surface
            
            # Position message
            text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 2))
            
            # Background
            bg_rect = text_rect.inflate(40, 20)
            bg_surface = pygame.Surface(bg_rect.size)
            bg_surface.set_alpha(180)
            bg_surface.fill((0, 0, 0))
            screen.blit(bg_surface, bg_rect.topleft)
            
            screen.blit(text_surface, text_rect)
            
            # Combat banner
            if self.in_combat:
                banner_text = "⚔ COMBAT ⚔"
                if not self.current_sequence.is_player_attacking:
                    banner_text = "🛡 ENEMY ATTACK 🛡"
                
                banner_surface = self.fonts['normal'].render(banner_text, True, (255, 255, 255))
                banner_rect = banner_surface.get_rect(center=(screen_width // 2, screen_height // 4))
                
                # Background color depends on who's attacking
                bg_color = (0, 100, 0) if self.current_sequence.is_player_attacking else (100, 0, 0)
                banner_bg = pygame.Surface(banner_rect.inflate(60, 20).size)
                banner_bg.set_alpha(150)
                banner_bg.fill(bg_color)
                screen.blit(banner_bg, banner_rect.inflate(60, 20).topleft)
                
                screen.blit(banner_surface, banner_rect)
        
        # Show combat queue status
        if self.combat_queue:
            queue_text = f"Combat Queue: {len(self.combat_queue)} pending"
            queue_surface = self.fonts['small'].render(queue_text, True, (200, 200, 200))
            screen.blit(queue_surface, (10, 10))
    
    def render_combat_stats_overlay(self, screen: pygame.Surface, world, player_eid, target_eid=None):
        """Render combat stats during combat"""
        if not self.in_combat:
            return
            
        from gameplay.ecs.components import CStats, CHealth, CDescriptor
        
        player_stats = world.get(player_eid, CStats)
        player_health = world.get(player_eid, CHealth)
        
        if not player_stats or not player_health:
            return
        
        # Stats panel
        panel_width = 280
        panel_height = 120
        panel_x = 20
        panel_y = screen.get_height() - 200
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.set_alpha(220)
        panel_surface.fill((20, 20, 40))
        screen.blit(panel_surface, panel_rect.topleft)
        
        pygame.draw.rect(screen, (100, 100, 150), panel_rect, 2)
        
        title = self.fonts['normal'].render("COMBAT STATS", True, (255, 255, 255))
        screen.blit(title, (panel_x + 10, panel_y + 10))
        
        y_offset = panel_y + 35
        stats_text = [
            f"Health: {player_health.hp}/{player_health.max_hp}",
            f"Attack: +{player_stats.accuracy}",
            f"Defense: {10 + player_stats.evasion}",
            f"Crit: {player_stats.crit_chance:.1f}%"
        ]
        
        for text in stats_text:
            rendered = self.fonts['small'].render(text, True, (200, 200, 200))
            screen.blit(rendered, (panel_x + 10, y_offset))
            y_offset += 18