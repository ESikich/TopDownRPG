# gameplay/ecs/systems/ai_system.py
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
        
        # Calculate distance to player
        dx = abs(monster_pos.x - player_pos.x)
        dy = abs(monster_pos.y - player_pos.y)
        distance = max(dx, dy)  # Chebyshev distance
        
        print(f"  Monster {eid} at ({monster_pos.x}, {monster_pos.y})")
        print(f"  Player at ({player_pos.x}, {player_pos.y})")
        print(f"  Distance: {distance}")
        
        # If adjacent to player (distance == 1), ATTACK!
        if distance == 1:
            monster_desc = self.world.get(eid, CDescriptor)
            monster_name = monster_desc.name if monster_desc else f"Monster {eid}"
            print(f"  {monster_name} is adjacent to player - ATTACKING!")
            
            # Post attack request
            self.world.post(AttackRequested(eid, self.player_eid))
            return
        
        # If close but not adjacent, try to get adjacent
        if distance <= 5:  # Within chase range
            print(f"  Monster {eid} chasing player")
            
            # Find path to player
            path = find_path((monster_pos.x, monster_pos.y), 
                           (player_pos.x, player_pos.y), 
                           self.dungeon_grid, self.world)
            
            if path and len(path) > 1:
                next_step = path[1]  # First step toward player
                print(f"  Moving toward player: {monster_pos.x}, {monster_pos.y} -> {next_step}")
                
                # Check if this step would put us adjacent to player
                step_dx = abs(next_step[0] - player_pos.x)
                step_dy = abs(next_step[1] - player_pos.y)
                step_distance = max(step_dx, step_dy)
                
                if step_distance == 0:
                    # Would move into player - attack instead
                    print(f"  Path leads into player - attacking instead!")
                    self.world.post(AttackRequested(eid, self.player_eid))
                else:
                    # Safe move toward player
                    self.world.post(MoveRequested(eid, next_step))
            else:
                print(f"  No path to player - trying direct approach")
                self._move_toward_player_direct(eid, monster_pos, player_pos)
        else:
            print(f"  Player too far away ({distance}) - wandering")
            self._process_wander_ai(eid, player_pos)
    
    def _move_toward_player_direct(self, eid: int, monster_pos, player_pos):
        """Move directly toward player when pathfinding fails"""
        # Calculate direction to player
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
        
        # Check if this would move into player
        if new_pos == (player_pos.x, player_pos.y):
            print(f"  Direct move would enter player position - attacking!")
            self.world.post(AttackRequested(eid, self.player_eid))
        else:
            self.world.post(MoveRequested(eid, new_pos))
    
    def _process_wander_ai(self, eid: int, player_pos):
        """Wander randomly but attack if bumping into player"""
        monster_pos = self.world.get(eid, CPosition)
        if not monster_pos:
            return
        
        print(f"  Monster {eid} wandering randomly")
        
        # Pick random adjacent direction
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        dx, dy = self.rng.choice(directions)
        new_pos = (monster_pos.x + dx, monster_pos.y + dy)
        
        # Check if this would bump into player
        if new_pos == (player_pos.x, player_pos.y):
            print(f"  Wander bumped into player - attacking!")
            self.world.post(AttackRequested(eid, self.player_eid))
        else:
            print(f"  Wander move: {monster_pos.x}, {monster_pos.y} -> {new_pos}")
            self.world.post(MoveRequested(eid, new_pos))