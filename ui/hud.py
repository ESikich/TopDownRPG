# ui/hud.py
"""Enhanced HUD with combat feedback"""
import pygame
import time
from gameplay.ecs.components import CHealth, CStats, CSpellbook, CInventory

class HUD:
    def __init__(self, config):
        self.config = config
        self.font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 16)
        self.large_font = pygame.font.Font(None, 28)
        
        # Combat feedback tracking
        self.last_hp = None
        self.damage_flash_time = 0
        self.damage_amount = 0
    
    def render(self, screen, world, player_eid):
        """Render the HUD with combat feedback"""
        # Get player components
        health = world.get(player_eid, CHealth)
        stats = world.get(player_eid, CStats)
        spellbook = world.get(player_eid, CSpellbook)
        inventory = world.get(player_eid, CInventory)
        
        if not health:
            return
        
        # Check for damage taken
        current_time = time.time() * 1000
        if self.last_hp is not None and health.hp < self.last_hp:
            self.damage_amount = self.last_hp - health.hp
            self.damage_flash_time = current_time + 1500  # Flash for 1.5 seconds
        self.last_hp = health.hp
        
        # Calculate HUD position
        tile_size = self.config['gameplay']['tile_size']
        ui_height = self.config['gameplay']['ui_height']
        hud_y = screen.get_height() - ui_height
        
        # HUD background with damage flash
        hud_rect = pygame.Rect(0, hud_y, screen.get_width(), ui_height)
        
        # Flash red background if recently damaged
        bg_color = (32, 32, 32)
        if current_time < self.damage_flash_time:
            flash_intensity = int((self.damage_flash_time - current_time) / 1500 * 100)
            bg_color = (32 + flash_intensity, 32, 32)
        
        pygame.draw.rect(screen, bg_color, hud_rect)
        pygame.draw.rect(screen, (128, 128, 128), hud_rect, 2)
        
        margin = 10
        y_pos = hud_y + margin
        
        # Health bar with damage indicator
        hp_text = self.font.render(f"HP: {health.hp}/{health.max_hp}", True, (255, 255, 255))
        screen.blit(hp_text, (margin, y_pos))
        
        # Show damage taken
        if current_time < self.damage_flash_time and self.damage_amount > 0:
            damage_text = self.large_font.render(f"-{self.damage_amount}", True, (255, 50, 50))
            screen.blit(damage_text, (margin + 200, y_pos - 5))
        
        # Health bar visual
        bar_x = margin + 100
        bar_width = 150
        bar_height = 16
        bar_rect = pygame.Rect(bar_x, y_pos + 2, bar_width, bar_height)
        
        # Background
        pygame.draw.rect(screen, (64, 0, 0), bar_rect)
        
        # Health fill
        if health.max_hp > 0:
            fill_width = int((health.hp / health.max_hp) * bar_width)
            fill_rect = pygame.Rect(bar_x, y_pos + 2, fill_width, bar_height)
            
            # Color based on health percentage
            health_percent = health.hp / health.max_hp
            if health_percent > 0.6:
                health_color = (0, 255, 0)  # Green
            elif health_percent > 0.3:
                health_color = (255, 255, 0)  # Yellow
            else:
                health_color = (255, 0, 0)  # Red
            
            pygame.draw.rect(screen, health_color, fill_rect)
        
        pygame.draw.rect(screen, (255, 255, 255), bar_rect, 1)
        
        # MP if available
        if spellbook:
            mp_text = self.font.render(f"MP: {spellbook.mp}/{spellbook.max_mp}", True, (255, 255, 255))
            screen.blit(mp_text, (margin + 300, y_pos))
        
        # Stats if available
        if stats:
            stats_text = self.small_font.render(
                f"STR:{stats.strength} AGI:{stats.agility} INT:{stats.intellect}", 
                True, (200, 200, 200)
            )
            screen.blit(stats_text, (margin, y_pos + 30))
            
            # Combat stats
            combat_text = self.small_font.render(
                f"ACC:{stats.accuracy} EVA:{stats.evasion} CRIT:{stats.crit_chance:.1f}%", 
                True, (200, 200, 200)
            )
            screen.blit(combat_text, (margin + 200, y_pos + 30))
        
        # Inventory count
        if inventory:
            inv_text = self.small_font.render(
                f"Items: {len(inventory.items)}/{inventory.capacity}", 
                True, (200, 200, 200)
            )
            screen.blit(inv_text, (margin + 400, y_pos + 30))
        
        # Controls
        controls = self.small_font.render("WASD:Move I:Inventory C:Spells R:Restart ESC:Pause", True, (150, 150, 150))
        screen.blit(controls, (margin, y_pos + 50))
        
        # Combat indicator
        if current_time < self.damage_flash_time:
            combat_text = self.font.render("IN COMBAT!", True, (255, 100, 100))
            screen.blit(combat_text, (screen.get_width() - 150, y_pos))