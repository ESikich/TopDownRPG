# gameplay/rules/attack.py
"""Attack resolution system"""
import random
from typing import Dict, Tuple, NamedTuple
from gameplay.ecs.components import CStats

class AttackResult(NamedTuple):
    hit: bool
    crit: bool
    roll: int
    target: int

def to_hit(attacker_stats: CStats, defender_stats: CStats, context: Dict = None, rng=None) -> AttackResult:
    """Resolve to-hit roll"""
    rng = rng or random.Random()
    context = context or {}
    
    # Roll d20
    roll = rng.randint(1, 20)
    
    # Calculate modifiers
    attack_bonus = attacker_stats.accuracy + context.get('weapon_bonus', 0)
    defense_value = 10 + defender_stats.evasion + context.get('cover', 0)
    
    # Natural 1 always misses, natural 20 always hits
    if roll == 1:
        return AttackResult(False, False, roll, defense_value)
    elif roll == 20:
        hit = True
    else:
        hit = (roll + attack_bonus) >= defense_value
    
    # Check for crit on successful hit
    crit = False
    if hit:
        crit_roll = rng.random() * 100
        crit = crit_roll < attacker_stats.crit_chance
    
    return AttackResult(hit, crit, roll, defense_value)