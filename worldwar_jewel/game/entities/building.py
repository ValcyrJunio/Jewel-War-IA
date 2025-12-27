from dataclasses import dataclass, field
from typing import Tuple

from worldwar_jewel.config import BuildingStats

Vec2 = Tuple[float, float]


@dataclass
class Building:
    id: int
    team_id: int
    kind: str
    stats: BuildingStats
    pos: Vec2
    hp: int
    constructing: bool = False
    progress: float = 0.0
    cooldown: float = 0.0

    def is_alive(self) -> bool:
        return self.hp > 0

    def tick(self, dt: float):
        if self.constructing:
            self.progress += dt
            if self.progress >= self.stats.build_time:
                self.constructing = False
                self.progress = self.stats.build_time
        self.cooldown = max(0.0, self.cooldown - dt)

