import math
from typing import Dict, List, Tuple

from worldwar_jewel.game.entities.jewel import Jewel
from worldwar_jewel.game.entities.unit import Unit

Vec2 = Tuple[float, float]


def dist(a: Vec2, b: Vec2) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def try_deliver(team_id: int, unit: Unit, jewel: Jewel, base_pos: Vec2, hold_timers: Dict[int, float], hold_required: float, dt: float) -> bool:
    """Returns True if capture condition satisfied."""
    if not unit.has_jewel or jewel.carried_by != unit.id:
        hold_timers[team_id] = 0.0
        return False
    if dist(unit.pos, base_pos) > 1.6:
        hold_timers[team_id] = 0.0
        return False
    hold_timers[team_id] += dt
    if hold_timers[team_id] >= hold_required:
        return True
    return False


def alive_core_team_ids(cores_alive: List[Tuple[int, bool]]) -> List[int]:
    return [tid for tid, alive in cores_alive if alive]

