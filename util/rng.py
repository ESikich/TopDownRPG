# util/rng.py
"""Random number generation utilities"""
import random
from typing import Optional

class GameRNG:
    """Centralized RNG for reproducible gameplay"""
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
    
    def randint(self, a: int, b: int) -> int:
        return self.rng.randint(a, b)
    
    def random(self) -> float:
        return self.rng.random()
    
    def choice(self, seq):
        return self.rng.choice(seq)
    
    def sample(self, population, k):
        return self.rng.sample(population, k)