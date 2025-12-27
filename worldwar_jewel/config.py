from dataclasses import dataclass, field
from typing import Dict, Tuple, List

# --- Core dataclasses ------------------------------------------------------


@dataclass
class ClassStats:
    name: str
    max_hp: int
    move_speed: float
    damage: int
    attack_range: float
    attack_cooldown: float
    gather_speed: float
    build_speed: float
    sight: float
    capture_bonus: float = 0.0
    carry_slow: float = 0.85


@dataclass
class BuildingStats:
    name: str
    max_hp: int
    build_time: float
    cost: Dict[str, int]
    attack_damage: int = 0
    attack_range: float = 0.0
    attack_cooldown: float = 1.0
    provides_respawn: bool = False
    is_core: bool = False
    blocks_movement: bool = True
    storage_bonus: int = 0
    vision: float = 0.0


@dataclass
class TeamProfile:
    name: str
    color: Tuple[int, int, int]
    id: int


@dataclass
class GameTuning:
    width: int = 64
    height: int = 40
    tile: int = 20
    fps: int = 30
    max_time_s: float = 600.0

    # squads/teams
    team_count: int = 3
    squad_size: int = 3

    # economy
    resource_types: Tuple[str, ...] = ("wood", "metal", "fuel")
    resources_on_map: int = 45
    resource_respawn_s: float = 22.0
    gather_time_s: float = 1.1

    # capture/dominance
    capture_hold_s: float = 2.5
    jewel_carry_slow: float = 0.75
    domination_enabled: bool = True
    require_core_alive: bool = True
    respawn_time_s: float = 4.0

    # misc
    projectile_speed: float = 14.0
    wall_spacing: float = 0.9


# --- Defaults --------------------------------------------------------------

TEAM_PROFILES: List[TeamProfile] = [
    TeamProfile(name="Blue", color=(70, 130, 255), id=0),
    TeamProfile(name="Red", color=(230, 80, 90), id=1),
    TeamProfile(name="Green", color=(90, 200, 140), id=2),
]

CLASS_PRESETS: Dict[str, ClassStats] = {
    "engineer": ClassStats(
        name="Engineer",
        max_hp=120,
        move_speed=5.5,
        damage=12,
        attack_range=1.5,
        attack_cooldown=0.6,
        gather_speed=1.15,
        build_speed=1.35,
        sight=10.0,
    ),
    "assault": ClassStats(
        name="Assault",
        max_hp=150,
        move_speed=5.0,
        damage=18,
        attack_range=1.7,
        attack_cooldown=0.55,
        gather_speed=1.0,
        build_speed=0.9,
        sight=9.0,
    ),
    "scout": ClassStats(
        name="Scout",
        max_hp=90,
        move_speed=7.5,
        damage=10,
        attack_range=1.4,
        attack_cooldown=0.5,
        gather_speed=0.95,
        build_speed=0.8,
        sight=13.0,
        capture_bonus=0.65,
        carry_slow=1.0,
    ),
}

BUILDING_PRESETS: Dict[str, BuildingStats] = {
    "core": BuildingStats(
        name="Core",
        max_hp=550,
        build_time=0.0,
        cost={},
        provides_respawn=True,
        is_core=True,
        blocks_movement=True,
        vision=10.0,
    ),
    "depot": BuildingStats(
        name="Depot",
        max_hp=220,
        build_time=6.0,
        cost={"wood": 8, "metal": 6},
        storage_bonus=20,
    ),
    "workshop": BuildingStats(
        name="Workshop",
        max_hp=240,
        build_time=7.5,
        cost={"wood": 6, "metal": 9},
    ),
    "turret": BuildingStats(
        name="Turret",
        max_hp=180,
        build_time=4.0,
        cost={"metal": 7, "fuel": 3},
        attack_damage=10,
        attack_range=7.0,
        attack_cooldown=0.9,
        vision=8.0,
    ),
    "wall": BuildingStats(
        name="Wall",
        max_hp=120,
        build_time=2.0,
        cost={"wood": 4, "metal": 1},
        blocks_movement=True,
    ),
}
