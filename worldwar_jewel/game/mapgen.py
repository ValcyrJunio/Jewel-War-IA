import random
from dataclasses import dataclass
from typing import List, Set, Tuple

from worldwar_jewel.config import GameTuning

Vec2 = Tuple[float, float]
GridPos = Tuple[int, int]


@dataclass
class MapLayout:
    width: int
    height: int
    walls: Set[GridPos]
    bases: List[Vec2]
    spawns: List[Vec2]
    resource_spots: List[Tuple[str, Vec2]]


def _triangular_bases(cfg: GameTuning) -> Tuple[List[Vec2], List[Vec2]]:
    w, h = cfg.width, cfg.height
    bases = [
        (4.5, h * 0.25),
        (w - 4.5, h * 0.3),
        (w * 0.55, h - 5.0),
    ]
    spawns = [
        (bases[0][0] + 1.8, bases[0][1]),
        (bases[1][0] - 1.8, bases[1][1]),
        (bases[2][0], bases[2][1] - 1.8),
    ]
    return bases, spawns


def _random_walls(cfg: GameTuning, rng: random.Random) -> Set[GridPos]:
    walls: Set[GridPos] = set()
    # Border ring (implicit walls for bounds)
    # Add small clusters to form chokepoints
    for _ in range(40):
        cx = rng.randint(6, cfg.width - 7)
        cy = rng.randint(4, cfg.height - 5)
        size_x = rng.randint(1, 3)
        size_y = rng.randint(1, 3)
        for dx in range(size_x + 1):
            for dy in range(size_y + 1):
                walls.add((cx + dx, cy + dy))
    # Central ruins / pillars
    midx, midy = cfg.width // 2, cfg.height // 2
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if abs(dx) + abs(dy) <= 3:
                walls.add((midx + dx, midy + dy))
    return walls


def _scatter_resources(cfg: GameTuning, rng: random.Random, walls: Set[GridPos], bases: List[Vec2]) -> List[Tuple[str, Vec2]]:
    spots: List[Tuple[str, Vec2]] = []
    attempts = 0
    radius_block = 3.5
    while len(spots) < cfg.resources_on_map and attempts < cfg.resources_on_map * 80:
        attempts += 1
        x = rng.uniform(3.0, cfg.width - 3.0)
        y = rng.uniform(2.0, cfg.height - 2.0)
        if (int(x), int(y)) in walls:
            continue
        if any((abs(x - bx) < radius_block and abs(y - by) < radius_block) for bx, by in bases):
            continue
        rtype = rng.choice(cfg.resource_types)
        # Central area has better metal/fuel odds
        if abs(x - cfg.width * 0.5) < cfg.width * 0.15 and abs(y - cfg.height * 0.5) < cfg.height * 0.15:
            rtype = rng.choice(["metal", "metal", "fuel", rtype])
        spots.append((rtype, (x, y)))
    return spots


def generate_map(cfg: GameTuning, team_count: int, seed: int | None = None) -> MapLayout:
    rng = random.Random(seed)
    bases, spawns = _triangular_bases(cfg)
    # If fewer teams, trim; if more, rotate additional bases around circle
    if team_count != 3:
        bases = bases[:team_count]
        spawns = spawns[:team_count]
        if team_count > 3:
            import math

            angle_step = 360.0 / team_count
            radius = min(cfg.width, cfg.height) * 0.35
            bases = []
            spawns = []
            for i in range(team_count):
                ang = (angle_step * i) * math.pi / 180.0
                ring = radius * (0.92 + rng.random() * 0.1)
                bx = cfg.width * 0.5 + ring * math.cos(ang)
                by = cfg.height * 0.5 + ring * math.sin(ang)
                bases.append((bx, by))
                spawns.append((bx + rng.uniform(-1.2, 1.2), by + rng.uniform(-1.2, 1.2)))

    walls = _random_walls(cfg, rng)
    # carve safe zones around bases/spawns
    for pos in bases + spawns:
        bx, by = int(pos[0]), int(pos[1])
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if abs(dx) + abs(dy) <= 4:
                    walls.discard((bx + dx, by + dy))
    resources = _scatter_resources(cfg, rng, walls, bases)

    return MapLayout(
        width=cfg.width,
        height=cfg.height,
        walls=walls,
        bases=bases,
        spawns=spawns,
        resource_spots=resources,
    )
