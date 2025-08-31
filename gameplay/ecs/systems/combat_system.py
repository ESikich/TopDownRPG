# gameplay/ecs/systems/combat_system.py
"""Combat resolution system"""
from gameplay.ecs.world import World
from gameplay.ecs.components import CStats, CHealth, CWeapon, CArmor
from gameplay.rules.attack import to_hit
from gameplay.rules.damage import apply_melee_ranged
from core.events import AttackRequested, DamageApplied, EntityDied, Message
import random

class CombatSystem:
    def __init__(self, world: World, rng=None):
        self.world = world
        self.rng = rng or random.Random()
    
    def process(self):
        """Process all combat events"""
        events = self.world.drain_events()
        
        for event in events:
            if isinstance(event, AttackRequested):
                self._handle_attack(event)
    
    def _handle_attack(self, event: AttackRequested):
        """Resolve an attack between two entities"""
        attacker_eid = event.attacker_eid
        target_eid = event.target_eid
        
        # Get required components
        attacker_stats = self.world.get(attacker_eid, CStats)
        target_health = self.world.get(target_eid, CHealth)
        target_stats = self.world.get(target_eid, CStats)
        
        if not all([attacker_stats, target_health, target_stats]):
            return
        
        # Get weapon (use default if none equipped)
        weapon = self.world.get(attacker_eid, CWeapon)
        if not weapon:
            # Default unarmed attack
            weapon = CWeapon(damage_dice="1d4+STR", damage_type="Physical")
        
        # Get target armor
        target_armor = self.world.get(target_eid, CArmor)
        
        # Resolve to-hit
        attack_result = to_hit(attacker_stats, target_stats, rng=self.rng)
        
        if not attack_result.hit:
            self.world.post(Message("Miss!"))
            return
        
        # Calculate damage
        damage_result = apply_melee_ranged(attacker_stats, weapon, target_armor, 
                                          attack_result.crit, self.rng)
        
        # Apply damage
        target_health.hp -= damage_result.final_damage
        
        # Post damage event
        self.world.post(DamageApplied(target_eid, damage_result.final_damage, 
                                     damage_result.damage_type, attacker_eid))
        
        # Create message
        crit_text = " (Critical Hit!)" if attack_result.crit else ""
        self.world.post(Message(f"Dealt {damage_result.final_damage} damage{crit_text}"))
        
        # Check for death
        if target_health.hp <= 0:
            target_health.is_dead = True
            self.world.post(EntityDied(target_eid, attacker_eid))
            self.world.post(Message("Target defeated!"))