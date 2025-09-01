# gameplay/ecs/systems/combat_system.py
"""Combat system with improved UI integration"""
from gameplay.ecs.world import World
from gameplay.ecs.components import CStats, CHealth, CWeapon, CArmor, CDescriptor
from gameplay.rules.attack import to_hit
from gameplay.rules.damage import apply_melee_ranged
from core.events import AttackRequested, DamageApplied, EntityDied, Message
import random

class CombatSystem:
    def __init__(self, world: World, rng=None, combat_ui=None, player_eid=None):
        self.world = world
        self.rng = rng or random.Random()
        self.combat_ui = combat_ui
        self.player_eid = player_eid  # Need this to determine if player is attacking
    
    def process(self):
        """Process all combat events"""
        events = self.world.drain_events()
        
        for event in events:
            if isinstance(event, AttackRequested):
                self._handle_attack(event)
    
    def _handle_attack(self, event: AttackRequested):
        """Resolve attack with full UI feedback"""
        attacker_eid = event.attacker_eid
        target_eid = event.target_eid
        
        # Determine if this is a player attack or monster attack
        is_player_attacking = (attacker_eid == self.player_eid)
        
        print(f"Combat: Entity {attacker_eid} attacks {target_eid} (Player attacking: {is_player_attacking})")
        
        # Get entity names
        attacker_desc = self.world.get(attacker_eid, CDescriptor)
        target_desc = self.world.get(target_eid, CDescriptor)
        
        attacker_name = attacker_desc.name if attacker_desc else f"Entity {attacker_eid}"
        target_name = target_desc.name if target_desc else f"Entity {target_eid}"
        
        # Get required components
        attacker_stats = self.world.get(attacker_eid, CStats)
        target_health = self.world.get(target_eid, CHealth)
        target_stats = self.world.get(target_eid, CStats)
        
        if not all([attacker_stats, target_health, target_stats]):
            print("Combat failed - missing components")
            return
        
        # Get weapon and armor
        weapon = self.world.get(attacker_eid, CWeapon)
        if not weapon:
            weapon = CWeapon(damage_dice="1d4+STR", damage_type="Physical")
        
        target_armor = self.world.get(target_eid, CArmor)
        
        # Resolve to-hit
        attack_result = to_hit(attacker_stats, target_stats, rng=self.rng)
        
        print(f"  Attack result: {'HIT' if attack_result.hit else 'MISS'}{' (CRIT)' if attack_result.crit else ''}")
        
        # Initialize damage values
        damage = 0
        original_damage = 0
        soak = 0
        
        # Calculate damage if hit
        if attack_result.hit:
            damage_result = apply_melee_ranged(attacker_stats, weapon, target_armor, 
                                              attack_result.crit, self.rng)
            damage = damage_result.final_damage
            original_damage = damage_result.original_damage
            soak = damage_result.soak_amount
            
            print(f"  Damage: {original_damage} -> {damage} (soak: {soak})")
            
            # Apply damage
            old_hp = target_health.hp
            target_health.hp -= damage
            target_health.hp = max(0, target_health.hp)
            
            # Post damage event
            self.world.post(DamageApplied(target_eid, damage, 
                                         damage_result.damage_type, attacker_eid))
        
        # Check for death
        target_died = target_health.hp <= 0
        if target_died:
            target_health.is_dead = True
            self.world.post(EntityDied(target_eid, attacker_eid))
            print(f"  {target_name} died!")
        
        # 🎬 ADD COMPLETE COMBAT SEQUENCE TO UI
        if self.combat_ui:
            self.combat_ui.add_combat_sequence(
                attacker_name=attacker_name,
                target_name=target_name,
                hit=attack_result.hit,
                crit=attack_result.crit,
                damage=damage,
                original_damage=original_damage,
                soak=soak,
                target_hp=target_health.hp,
                target_max_hp=target_health.max_hp,
                target_died=target_died,
                is_player_attacking=is_player_attacking
            )