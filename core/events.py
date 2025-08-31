# core/events.py
"""Event definitions for the ECS system"""
from dataclasses import dataclass
from typing import Optional, Any, Dict
from core.types import Point

@dataclass
class Event:
    """Base event class"""
    pass

@dataclass
class MoveRequested(Event):
    eid: int
    to_xy: Point

@dataclass
class MoveResolved(Event):
    eid: int
    from_xy: Point
    to_xy: Point

@dataclass
class Bump(Event):
    eid: int
    target_eid: int

@dataclass
class AttackRequested(Event):
    attacker_eid: int
    target_eid: int

@dataclass
class DamageApplied(Event):
    target_eid: int
    amount: int
    dtype: str
    source_eid: Optional[int] = None

@dataclass
class EntityDied(Event):
    eid: int
    killer_eid: Optional[int] = None

@dataclass
class SpellCastRequested(Event):
    caster_eid: int
    spell_id: str
    target_spec: Any

@dataclass
class ItemPicked(Event):
    eid: int
    item_eid: int

@dataclass
class ItemEquipped(Event):
    eid: int
    slot: str
    item_eid: int

@dataclass
class DescendRequested(Event):
    eid: int
    stair_xy: Point

@dataclass
class Message(Event):
    text: str
    channel: str = "log"
    ttl_ms: int = 3000