# ui/hud.py
"""Heads-Up Display for player stats and info"""
import pygame
from gameplay.ecs.components import CHealth, CStats, CSpellbook, CInventory

class HUD:
    def __init__(self, config):
        self.config = config
        self.font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 16)
    
    def render(self, screen, world, player_eid):
        """Render the HUD"""
        # Get player components
        health = world.get(player_eid, CHealth)
        stats = world.get(player_eid, CStats)
        spellbook = world.get(player_eid, CSpellbook)
        inventory = world.get(player_eid, CInventory)
        
        if not health:
            return
        
        # Calculate HUD position
        tile_size = self.config['gameplay']['tile_size']
        ui_height = self.config['gameplay']['ui_height']
        hud_y = screen.get_height() - ui_height
        
        # HUD background
        hud_rect = pygame.Rect(0, hud_y, screen.get_width(), ui_height)
        pygame.draw.rect(screen, (32, 32, 32), hud_rect)
        pygame.draw.rect(screen, (128, 128, 128), hud_rect, 2)
        
        margin = 10
        y_pos = hud_y + margin
        
        # Health bar
        hp_text = self.font.render(f"HP: {health.hp}/{health.max_hp}", True, (255, 255, 255))
        screen.blit(hp_text, (margin, y_pos))
        
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
            pygame.draw.rect(screen, (0, 255, 0), fill_rect)
        
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
        
        # Inventory count
        if inventory:
            inv_text = self.small_font.render(
                f"Items: {len(inventory.items)}/{inventory.capacity}", 
                True, (200, 200, 200)
            )
            screen.blit(inv_text, (margin + 200, y_pos + 30))
        
        # Controls
        controls = self.small_font.render("WASD:Move I:Inventory C:Spells R:Restart ESC:Pause", True, (150, 150, 150))
        screen.blit(controls, (margin, y_pos + 50))
