# gameplay/rules/attack.py
"""Attack resolution system"""

import random
from dataclasses import dataclass
from typing import Mapping, Optional

from gameplay.ecs.components import CStats


@dataclass(frozen=True)
class AttackResult:
    hit: bool
    crit: bool
    roll: int         # the d20 result before modifiers
    target: int       # the defense value that had to be met or exceeded


def to_hit(
    attacker_stats: CStats,
    defender_stats: CStats,
    context: Optional[Mapping[str, int]] = None,
    rng: Optional[random.Random] = None,
) -> AttackResult:
    """
    Resolve a to-hit roll.

    Parameters
    ----------
    attacker_stats : CStats
        Uses `accuracy` and `crit_chance` (0–100).
    defender_stats : CStats
        Uses `evasion`.
    context : Mapping[str, int], optional
        Optional modifiers:
          - "weapon_bonus": flat attack bonus (default 0)
          - "cover": flat defense bonus added to target (default 0)
    rng : random.Random, optional
        RNG source; a new Random() is used if not provided.

    Returns
    -------
    AttackResult
        Outcome with raw d20 `roll`, `target` defense value, and flags `hit`/`crit`.
    """
    r = rng or random.Random()
    ctx = context or {}

    # Roll d20
    roll = r.randint(1, 20)

    # Calculate modifiers/target
    attack_bonus = int(attacker_stats.accuracy) + int(ctx.get("weapon_bonus", 0))
    defense_value = 10 + int(defender_stats.evasion) + int(ctx.get("cover", 0))

    # Natural 1/20 rules
    if roll == 1:
        return AttackResult(hit=False, crit=False, roll=roll, target=defense_value)

    if roll == 20:
        hit = True
    else:
        hit = (roll + attack_bonus) >= defense_value

    # Crit only if the attack hits
    crit = False
    if hit:
        # Clamp crit chance to [0, 100] defensively
        crit_chance = max(0.0, min(100.0, float(attacker_stats.crit_chance)))
        crit = (r.random() * 100.0) < crit_chance

    return AttackResult(hit=hit, crit=crit, roll=roll, target=defense_value)
