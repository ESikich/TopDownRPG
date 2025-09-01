"""Movement system that respects combat locks
and triggers adjacency attacks after NPC movement."""
from typing import Optional
from gameplay.ecs.world import World
from gameplay.ecs.components import CPosition, CBlocker, CHealth
from core.events import MoveRequested, MoveResolved, Bump, AttackRequested, Message


class MovementSystem:
    def __init__(self, world: World, dungeon_grid=None, combat_state_system=None, player_eid: Optional[int] = None):
        self.world = world
        self.dungeon_grid = dungeon_grid
        self.combat_state_system = combat_state_system
        self.player_eid = player_eid

    @staticmethod
    def _adjacent4(a: CPosition, b: CPosition) -> bool:
        # 4-way adjacency (no diagonals), consistent with our pathfinding
        return abs(a.x - b.x) + abs(a.y - b.y) == 1

    def process(self) -> None:
        """Process all movement requests.

        Drain the event queue, handle MoveRequested events,
        and re-post any other events back into the queue so other systems
        (like the combat system) can handle them.
        """
        events = self.world.drain_events()
        for event in events:
            if isinstance(event, MoveRequested):
                self._handle_move_request(event)
            else:
                # Re-post events we don’t handle (e.g., AttackRequested)
                self.world.post(event)

    def _handle_move_request(self, event: MoveRequested):
        """Handle movement with combat lock checking"""
        eid = event.eid
        to_x, to_y = event.to_xy

        # Get current position
        pos = self.world.get(eid, CPosition)
        if not pos:
            return

        from_pos = (pos.x, pos.y)
        to_pos = (to_x, to_y)

        # Check combat lock
        if self.combat_state_system and not self.combat_state_system.can_move_freely(eid, from_pos, to_pos):
            self.world.post(Message("Cannot flee from combat!"))
            return

        # Check bounds
        if self.dungeon_grid:
            if not (0 <= to_x < len(self.dungeon_grid[0]) and 0 <= to_y < len(self.dungeon_grid)):
                self.world.post(Message("Can't go that way!"))
                return

            # Check if tile is walkable
            if not self.dungeon_grid[to_y][to_x].walkable:
                return

        # Check for entities at target position
        entities_at_target = self.world.entities_at(to_x, to_y)

        for target_eid in entities_at_target:
            if target_eid == eid:
                continue

            # Get target info
            target_health = self.world.get(target_eid, CHealth)
            target_blocker = self.world.get(target_eid, CBlocker)

            # Check for living entities (combat!)
            if target_health and not target_health.is_dead:
                print(f"Movement collision: Entity {eid} bumps into living entity {target_eid} - COMBAT!")
                self.world.post(Bump(eid, target_eid))
                self.world.post(AttackRequested(eid, target_eid))
                return

            # Check for blocking objects
            if target_blocker and not target_blocker.passable:
                return

        # Move is valid - update position
        pos.x = to_x
        pos.y = to_y

        print(f"Entity {eid} moved from {from_pos} to ({to_x}, {to_y})")
        self.world.post(MoveResolved(eid, from_pos, (to_x, to_y)))

        # NEW: NPC adjacency attack after moving
        if self.player_eid is not None and eid != self.player_eid:
            player_pos = self.world.get(self.player_eid, CPosition)
            if player_pos and self._adjacent4(pos, player_pos):
                self.world.post(AttackRequested(attacker_eid=eid, target_eid=self.player_eid))
