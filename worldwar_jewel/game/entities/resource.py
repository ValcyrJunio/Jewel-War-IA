from dataclasses import dataclass
from typing import Tuple

Vec2 = Tuple[float, float]


@dataclass
class ResourceNode:
    id: int
    rtype: str
    pos: Vec2
    amount: int = 1
    alive: bool = True
    respawn: float = 0.0

    def tick(self, dt: float, respawn_time: float):
        if not self.alive:
            self.respawn -= dt
            if self.respawn <= 0:
                self.alive = True
                self.respawn = 0.0

