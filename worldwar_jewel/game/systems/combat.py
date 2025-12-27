import math
from typing import List, Optional, Tuple

from worldwar_jewel.game.entities.building import Building
from worldwar_jewel.game.entities.unit import Unit

Vec2 = Tuple[float, float]


def dist(a: Vec2, b: Vec2) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def unit_attack(attacker: Unit, target: Unit) -> bool:
    """Simple melee/ranged attack. Returns True if executed."""
    if attacker.cooldown > 0 or attacker.busy > 0 or not attacker.is_alive():
        return False
    if not target.is_alive():
        return False
    if dist(attacker.pos, target.pos) > attacker.stats.attack_range:
        return False
    dmg = attacker.stats.damage
    target.hp = max(0, target.hp - dmg)
    attacker.cooldown = attacker.stats.attack_cooldown
    return True


def attack_building(attacker: Unit, building: Building, bonus: float = 1.0) -> bool:
    if attacker.cooldown > 0 or attacker.busy > 0 or not attacker.is_alive():
        return False
    if not building.is_alive():
        return False
    if dist(attacker.pos, building.pos) > attacker.stats.attack_range + 0.2:
        return False
    dmg = int(attacker.stats.damage * bonus)
    building.hp = max(0, building.hp - dmg)
    attacker.cooldown = attacker.stats.attack_cooldown
    return True


def turret_fire(turret: Building, enemies: List[Unit]) -> Optional[int]:
    """Turret auto-fires at closest enemy; returns unit id hit or None."""
    if turret.cooldown > 0 or not turret.is_alive() or turret.stats.attack_damage <= 0:
        return None
    best = None
    bestd = 1e9
    for u in enemies:
        if not u.is_alive():
            continue
        d = dist(turret.pos, u.pos)
        if d <= turret.stats.attack_range and d < bestd:
            bestd = d
            best = u
    if best is None:
        return None
    best.hp = max(0, best.hp - turret.stats.attack_damage)
    turret.cooldown = turret.stats.attack_cooldown
    return best.id

