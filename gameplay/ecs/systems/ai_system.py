"""Fixed AI system with proper combat behavior"""
from gameplay.ecs.world import World
from gameplay.ecs.components import CAI, CPosition, CHealth, CVisible, CDescriptor
from core.events import MoveRequested, AttackRequested
from util.pathfinding import find_path
import random


class AISystem:
    def __init__(self, world: World, player_eid: int, dungeon_grid=None, rng=None):
        self.world = world
        self.player_eid = player_eid
        self.dungeon_grid = dungeon_grid
        self.rng = rng or random.Random()

    def process(self):
        """Process AI for all living entities with CAI"""
        print("\n=== AI TURN START ===")

        # Get player position once
        player_pos = self.world.get(self.player_eid, CPosition)
        if not player_pos:
            return

        for eid in self.world.entities_with(CAI, CPosition, CHealth):
            health = self.world.get(eid, CHealth)
            if health.is_dead:
                continue

            print(f"Processing AI for entity {eid}")

            ai = self.world.get(eid, CAI)
            if ai.behavior == "chase":
                self._process_chase_ai(eid, player_pos)
            elif ai.behavior == "wander":
                self._process_wander_ai(eid, player_pos)

        print("=== AI TURN END ===")

    def _process_chase_ai(self, eid: int, player_pos):
        """Chase AI with proper attack logic"""
        monster_pos = self.world.get(eid, CPosition)
        if not monster_pos:
            return

        # Manhattan distance (4-way adjacency)
        dx = abs(monster_pos.x - player_pos.x)
        dy = abs(monster_pos.y - player_pos.y)
        manhattan = dx + dy

        print(f"  Monster {eid} at ({monster_pos.x}, {monster_pos.y})")
        print(f"  Player at ({player_pos.x}, {player_pos.y})")
        print(f"  Manhattan distance: {manhattan}")

        if manhattan == 1:
            monster_desc = self.world.get(eid, CDescriptor)
            monster_name = monster_desc.name if monster_desc else f"Monster {eid}"
            print(f"  {monster_name} is adjacent to player - ATTACKING!")
            self.world.post(AttackRequested(eid, self.player_eid))
            return

        if manhattan <= 5:  # Within chase range
            print(f"  Monster {eid} chasing player")
            path = find_path((monster_pos.x, monster_pos.y), (player_pos.x, player_pos.y), self.dungeon_grid, self.world)
            if path and len(path) > 1:
                next_step = path[1]
                print(f"  Moving toward player: {monster_pos.x}, {monster_pos.y} -> {next_step}")
                # Just move; MovementSystem will trigger attack if adjacent after move
                self.world.post(MoveRequested(eid, next_step))
            else:
                print(f"  No path to player - trying direct approach")
                self._move_toward_player_direct(eid, monster_pos, player_pos)
        else:
            print(f"  Player too far away ({manhattan}) - wandering")
            self._process_wander_ai(eid, player_pos)

    def _move_toward_player_direct(self, eid: int, monster_pos, player_pos):
        dx = 0
        if player_pos.x > monster_pos.x:
            dx = 1
        elif player_pos.x < monster_pos.x:
            dx = -1

        dy = 0
        if player_pos.y > monster_pos.y:
            dy = 1
        elif player_pos.y < monster_pos.y:
            dy = -1

        new_pos = (monster_pos.x + dx, monster_pos.y + dy)
        print(f"  Direct move toward player: {monster_pos.x}, {monster_pos.y} -> {new_pos}")

        if new_pos == (player_pos.x, player_pos.y):
            print(f"  Direct move would enter player position - attacking!")
            self.world.post(AttackRequested(eid, self.player_eid))
        else:
            self.world.post(MoveRequested(eid, new_pos))

    def _process_wander_ai(self, eid: int, player_pos):
        monster_pos = self.world.get(eid, CPosition)
        if not monster_pos:
            return

        print(f"  Monster {eid} wandering randomly")
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        dx, dy = self.rng.choice(directions)
        new_pos = (monster_pos.x + dx, monster_pos.y + dy)

        if new_pos == (player_pos.x, player_pos.y):
            print(f"  Wander bumped into player - attacking!")
            self.world.post(AttackRequested(eid, self.player_eid))
        else:
            print(f"  Wander move: {monster_pos.x}, {monster_pos.y} -> {new_pos}")
            self.world.post(MoveRequested(eid, new_pos))
