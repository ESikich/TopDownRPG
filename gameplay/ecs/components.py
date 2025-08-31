# gameplay/ecs/components.py
"""ECS Component definitions - pure data only"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass
class CPosition:
    x: int
    y: int
    z: int = 0

@dataclass  
class CVision:
    radius: int

@dataclass
class CBlocker:
    passable: bool

@dataclass
class CHealth:
    hp: int
    max_hp: int
    is_dead: bool = False

@dataclass
class CStats:
    strength: int
    agility: int
    intellect: int
    accuracy: int
    evasion: int
    crit_chance: float
    crit_mult: float

@dataclass
class CArmor:
    soak_dice: str
    resist: Dict[str, float] = field(default_factory=dict)
    spell_resist: Dict[str, float] = field(default_factory=dict)

@dataclass
class CWeapon:
    damage_dice: str
    damage_type: str
    reach: int = 1
    tags: List[str] = field(default_factory=list)

@dataclass
class CInventory:
    capacity: int
    items: List[int] = field(default_factory=list)

@dataclass
class CEquipment:
    slots: Dict[str, int] = field(default_factory=dict)

@dataclass
class CSpellbook:
    spells: List[str] = field(default_factory=list)
    mp: int = 50
    max_mp: int = 50

@dataclass
class CStatus:
    effects: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class CAI:
    behavior: str
    memory: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CInteractable:
    kind: str
    data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CDescriptor:
    name: str
    glyph: str
    color: str

@dataclass
class CVisible:
    """Cache for FOV computation"""
    visible_tiles: set = field(default_factory=set)
    seen_tiles: set = field(default_factory=set)