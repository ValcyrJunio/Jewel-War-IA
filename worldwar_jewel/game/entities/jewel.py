from dataclasses import dataclass
from typing import Optional, Tuple

Vec2 = Tuple[float, float]


@dataclass
class Jewel:
    home_team: int
    pos: Vec2
    carried_by: Optional[int] = None  # unit id
    at_home: bool = True

    def drop(self, position: Vec2):
        self.carried_by = None
        self.at_home = False
        self.pos = position

