from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from worldwar_jewel.config import ClassStats

Vec2 = Tuple[float, float]


@dataclass
class Unit:
    id: int
    team_id: int
    cls_id: str
    stats: ClassStats
    pos: Vec2
    hp: int
    cooldown: float = 0.0
    busy: float = 0.0
    inventory: Dict[str, int] = field(default_factory=lambda: {"wood": 0, "metal": 0, "fuel": 0})
    has_jewel: bool = False
    perks: List[str] = field(default_factory=list)
    path: List[Vec2] = field(default_factory=list)
    respawn_timer: float = 0.0

    def is_alive(self) -> bool:
        return self.hp > 0

    def tick_timers(self, dt: float):
        self.cooldown = max(0.0, self.cooldown - dt)
        self.busy = max(0.0, self.busy - dt)

    def clear_path(self):
        self.path.clear()
