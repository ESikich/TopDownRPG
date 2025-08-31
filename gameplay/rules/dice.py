# gameplay/rules/dice.py
"""Dice rolling system with attribute modifiers"""
import re
import random
from typing import List, Mapping, Optional, Tuple, TypedDict


class RollBreakdown(TypedDict):
    dice_total: int
    mod_total: int
    dice_rolls: List[int]


class DiceRoller:
    def __init__(self, rng: Optional[random.Random] = None) -> None:
        self.rng: random.Random = rng or random.Random()

    def roll(self, expr: str, attrs: Optional[Mapping[str, int]] = None) -> Tuple[int, RollBreakdown]:
        """Roll a dice expression like '2d6+3+STR/2' with optional attribute modifiers.

        Args:
            expr: Expression containing one dice term (XdY) plus optional modifiers.
            attrs: Mapping of attribute names (e.g., 'STR', 'AGI', 'INT') to values.

        Returns:
            total: Clamped at >= 0
            breakdown: Per-roll details (dice_total, mod_total, dice_rolls)
        """
        attrs = attrs or {}

        # Parse expression: XdY+Z+ATTR/2 etc
        breakdown: RollBreakdown = {"dice_total": 0, "mod_total": 0, "dice_rolls": []}

        # Handle base dice (XdY)
        dice_match = re.search(r"(\d+)d(\d+)", expr)
        if dice_match:
            num_dice = int(dice_match.group(1))
            die_size = int(dice_match.group(2))
            if num_dice > 0 and die_size > 0:
                rolls = [self.rng.randint(1, die_size) for _ in range(num_dice)]
                breakdown["dice_rolls"] = rolls
                breakdown["dice_total"] = sum(rolls)

        # Handle constant modifiers (+Z, -Z)
        for match in re.findall(r"([+-]\d+)", expr):
            breakdown["mod_total"] += int(match)

        # Handle attribute modifiers (+STR, +INT/2, etc)
        for sign, attr, divisor in re.findall(r"([+-])(STR|AGI|INT)(?:/(\d+))?", expr):
            attr_val = int(attrs.get(attr, 0))
            if divisor:
                div = int(divisor)
                if div > 0:
                    attr_val = attr_val // div
            if sign == "-":
                attr_val = -attr_val
            breakdown["mod_total"] += attr_val

        total = breakdown["dice_total"] + breakdown["mod_total"]
        return (0 if total < 0 else total), breakdown
