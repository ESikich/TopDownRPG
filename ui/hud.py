# ui/hud.py
"""Enhanced HUD with combat feedback"""
import pygame
from typing import Optional
from gameplay.ecs.components import CHealth, CStats, CSpellbook, CInventory

class HUD:
    """
    Heads-up display for the player including health, mana, stats and
    combat feedback. This implementation tracks damage flash using a
    remaining time value rather than absolute wall clock time so that the
    caller can pause the effect (e.g. during combat sequences).
    """

    def __init__(self, config: dict) -> None:
        self.config = config
        self.font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 16)
        self.large_font = pygame.font.Font(None, 28)
        # Store last known HP to detect damage
        self.last_hp: Optional[int] = None
        # Remaining time (ms) to flash red background / show damage
        self.damage_flash_remaining_ms: float = 0.0
        # Amount of damage most recently taken
        self.damage_amount: int = 0

    def update(self, elapsed_ms: float, world, player_eid: int) -> None:
        """Update damage flash timers and detect new damage.

        `elapsed_ms` should represent the game time that has passed since
        the previous call. When game time is frozen (e.g. during combat
        sequences), callers should pass zero to prevent the damage flash
        timers from advancing.
        """
        # Access health component for player
        from gameplay.ecs.components import CHealth
        health: Optional[CHealth] = world.get(player_eid, CHealth)
        if not health:
            return
        # Detect damage taken
        if self.last_hp is not None and health.hp < self.last_hp:
            # Compute amount and reset remaining flash time (1.5s)
            self.damage_amount = self.last_hp - health.hp
            self.damage_flash_remaining_ms = 1500.0
        # Update last_hp for next frame
        self.last_hp = health.hp
        # Decrease remaining flash time
        if self.damage_flash_remaining_ms > 0.0:
            self.damage_flash_remaining_ms = max(0.0, self.damage_flash_remaining_ms - elapsed_ms)

    def render(self, screen: pygame.Surface, world, player_eid: int) -> None:
        """Render the HUD to the given screen surface."""
        from gameplay.ecs.components import CHealth, CStats, CSpellbook, CInventory
        # Fetch player components
        health: Optional[CHealth] = world.get(player_eid, CHealth)
        stats: Optional[CStats] = world.get(player_eid, CStats)
        spellbook: Optional[CSpellbook] = world.get(player_eid, CSpellbook)
        inventory: Optional[CInventory] = world.get(player_eid, CInventory)

        if not health:
            return

        # Determine dimensions
        tile_size = self.config['gameplay']['tile_size']
        ui_height = self.config['gameplay']['ui_height']
        hud_y = screen.get_height() - ui_height
        hud_rect = pygame.Rect(0, hud_y, screen.get_width(), ui_height)

        # Compute background colour with damage flash
        base_color = (32, 32, 32)
        bg_color = base_color
        if self.damage_flash_remaining_ms > 0.0:
            # Scale intensity between 0 and 100 based on remaining time
            flash_intensity = int((self.damage_flash_remaining_ms / 1500.0) * 100)
            bg_color = (base_color[0] + flash_intensity, base_color[1], base_color[2])

        pygame.draw.rect(screen, bg_color, hud_rect)
        pygame.draw.rect(screen, (128, 128, 128), hud_rect, 2)

        margin = 10
        y_pos = hud_y + margin

        # Health bar and damage indicator
        hp_text = self.font.render(f"HP: {health.hp}/{health.max_hp}", True, (255, 255, 255))
        screen.blit(hp_text, (margin, y_pos))
        # Show damage amount if flashing and damage_amount > 0
        if self.damage_flash_remaining_ms > 0.0 and self.damage_amount > 0:
            damage_text = self.large_font.render(f"-{self.damage_amount}", True, (255, 50, 50))
            screen.blit(damage_text, (margin + 200, y_pos - 5))

        # Health bar visual
        bar_x = margin + 100
        bar_width = 150
        bar_height = 16
        bar_rect = pygame.Rect(bar_x, y_pos + 2, bar_width, bar_height)
        # Background bar
        pygame.draw.rect(screen, (64, 0, 0), bar_rect)
        if health.max_hp > 0:
            fill_width = int((health.hp / health.max_hp) * bar_width)
            fill_rect = pygame.Rect(bar_x, y_pos + 2, fill_width, bar_height)
            # Choose colour based on hp percentage
            health_percent = health.hp / health.max_hp
            if health_percent > 0.6:
                health_colour = (0, 255, 0)
            elif health_percent > 0.3:
                health_colour = (255, 255, 0)
            else:
                health_colour = (255, 0, 0)
            pygame.draw.rect(screen, health_colour, fill_rect)
        pygame.draw.rect(screen, (255, 255, 255), bar_rect, 1)

        # Mana/spell points
        if spellbook:
            mp_text = self.font.render(f"MP: {spellbook.mp}/{spellbook.max_mp}", True, (255, 255, 255))
            screen.blit(mp_text, (margin + 300, y_pos))
        # Stats display
        if stats:
            stats_text = self.small_font.render(
                f"STR:{stats.strength} AGI:{stats.agility} INT:{stats.intellect}", True, (200, 200, 200)
            )
            screen.blit(stats_text, (margin, y_pos + 30))
            combat_text = self.small_font.render(
                f"ACC:{stats.accuracy} EVA:{stats.evasion} CRIT:{stats.crit_chance:.1f}%", True, (200, 200, 200)
            )
            screen.blit(combat_text, (margin + 200, y_pos + 30))
        # Inventory count
        if inventory:
            inv_text = self.small_font.render(
                f"Items: {len(inventory.items)}/{inventory.capacity}", True, (200, 200, 200)
            )
            screen.blit(inv_text, (margin + 400, y_pos + 30))
        # Controls helper text
        controls = self.small_font.render(
            "WASD:Move I:Inventory C:Spells R:Restart ESC:Pause", True, (150, 150, 150)
        )
        screen.blit(controls, (margin, y_pos + 50))
        # Combat indicator
        if self.damage_flash_remaining_ms > 0.0:
            combat_text = self.font.render("IN COMBAT!", True, (255, 100, 100))
            screen.blit(combat_text, (screen.get_width() - 150, y_pos))
