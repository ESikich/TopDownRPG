# gameplay/rules/dice.py
"""Dice rolling system with attribute modifiers"""
import re
import random
from typing import Dict, Tuple

class DiceRoller:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
    
    def roll(self, expr: str, attrs: Dict[str, int] = None) -> Tuple[int, Dict]:
        """Roll dice expression with attribute modifiers"""
        attrs = attrs or {}
        
        # Parse expression: XdY+Z+ATTR/2 etc
        breakdown = {'dice_total': 0, 'mod_total': 0, 'dice_rolls': []}
        
        # Handle base dice (XdY)
        dice_match = re.search(r'(\d+)d(\d+)', expr)
        if dice_match:
            num_dice = int(dice_match.group(1))
            die_size = int(dice_match.group(2))
            rolls = [self.rng.randint(1, die_size) for _ in range(num_dice)]
            breakdown['dice_rolls'] = rolls
            breakdown['dice_total'] = sum(rolls)
        
        # Handle constant modifiers (+Z, -Z)
        const_matches = re.findall(r'([+-]\d+)', expr)
        for match in const_matches:
            breakdown['mod_total'] += int(match)
        
        # Handle attribute modifiers (+STR, +INT/2, etc)
        attr_matches = re.findall(r'([+-])(STR|AGI|INT)(?:/(\d+))?', expr)
        for sign, attr, divisor in attr_matches:
            attr_val = attrs.get(attr, 0)
            if divisor:
                attr_val = attr_val // int(divisor)
            if sign == '-':
                attr_val = -attr_val
            breakdown['mod_total'] += attr_val
        
        total = breakdown['dice_total'] + breakdown['mod_total']
        return max(0, total), breakdown
