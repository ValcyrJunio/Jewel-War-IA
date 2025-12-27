from typing import Dict, Optional, Tuple

from worldwar_jewel.config import BuildingStats
from worldwar_jewel.game.entities.building import Building
from worldwar_jewel.game.entities.unit import Unit

Vec2 = Tuple[float, float]


def can_afford(resources: Dict[str, int], cost: Dict[str, int]) -> bool:
    return all(resources.get(k, 0) >= v for k, v in cost.items())


def spend(resources: Dict[str, int], cost: Dict[str, int]) -> bool:
    if not can_afford(resources, cost):
        return False
    for k, v in cost.items():
        resources[k] = resources.get(k, 0) - v
    return True


def start_build(team_id: int, next_id: int, kind: str, stats: BuildingStats, pos: Vec2, team_resources: Dict[str, int]) -> Optional[Building]:
    if not spend(team_resources, stats.cost):
        return None
    hp = max(1, stats.max_hp // 3) if stats.build_time > 0 else stats.max_hp
    return Building(
        id=next_id,
        team_id=team_id,
        kind=kind,
        stats=stats,
        pos=pos,
        hp=hp,
        constructing=stats.build_time > 0,
        progress=0.0,
    )


def repair(unit: Unit, building: Building, amount: int) -> bool:
    if not unit.is_alive() or unit.busy > 0:
        return False
    if building.hp <= 0 or building.hp >= building.stats.max_hp:
        return False
    building.hp = min(building.stats.max_hp, building.hp + amount)
    unit.busy = 0.3
    return True

