# gameplay/rules/damage.py
"""Damage calculation and application"""
from typing import NamedTuple, Dict, Optional
from gameplay.rules.dice import DiceRoller
from gameplay.ecs.components import CStats, CArmor, CWeapon

class DamageResult(NamedTuple):
    final_damage: int
    original_damage: int
    soak_amount: int
    resist_mult: float
    damage_type: str

def apply_melee_ranged(attacker_stats: CStats, weapon: CWeapon, defender_armor: Optional[CArmor], 
                      is_crit: bool, rng=None) -> DamageResult:
    """Apply weapon damage with armor considerations"""
    roller = DiceRoller(rng)
    attrs = {'STR': attacker_stats.strength, 'AGI': attacker_stats.agility, 'INT': attacker_stats.intellect}
    
    # Roll base damage
    base_damage, breakdown = roller.roll(weapon.damage_dice, attrs)
    
    # Apply crit (double dice only, not modifiers)
    if is_crit:
        crit_dice = breakdown['dice_total'] * 2
        final_base = crit_dice + breakdown['mod_total']
    else:
        final_base = base_damage
    
    soak_amount = 0
    resist_mult = 1.0
    
    if weapon.damage_type == "Physical" and defender_armor:
        # Apply soak for physical damage
        if defender_armor.soak_dice:
            soak_damage, _ = roller.roll(defender_armor.soak_dice)
            soak_amount = soak_damage
        
        # Apply physical resistance
        resist_mult = 1.0 - defender_armor.resist.get("Physical", 0.0)
    elif defender_armor:
        # Non-physical damage - no soak, but apply elemental resistance
        resist_mult = 1.0 - defender_armor.resist.get(weapon.damage_type, 0.0)
    
    # Calculate final damage
    after_soak = max(0, final_base - soak_amount)
    final_damage = int(after_soak * resist_mult)
    
    return DamageResult(final_damage, final_base, soak_amount, resist_mult, weapon.damage_type)

def apply_spell(spell_data: Dict, caster_stats: CStats, defender_armor: Optional[CArmor], rng=None) -> DamageResult:
    """Apply spell damage (ignores armor soak)"""
    roller = DiceRoller(rng)
    attrs = {'STR': caster_stats.strength, 'AGI': caster_stats.agility, 'INT': caster_stats.intellect}
    
    # Roll spell damage
    damage_dice = spell_data.get('damage_dice', '1d4')
    damage_type = spell_data.get('damage_type', 'Arcane')
    base_damage, _ = roller.roll(damage_dice, attrs)
    
    # Spells ignore armor soak but respect spell resistance
    resist_mult = 1.0
    if defender_armor:
        # Check spell resistance first, then general resistance as fallback
        if damage_type in defender_armor.spell_resist:
            resist_mult = 1.0 - defender_armor.spell_resist[damage_type]
        else:
            resist_mult = 1.0 - defender_armor.resist.get(damage_type, 0.0)
    
    final_damage = int(base_damage * resist_mult)
    
    return DamageResult(final_damage, base_damage, 0, resist_mult, damage_type)
