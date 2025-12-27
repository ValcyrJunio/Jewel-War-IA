from dataclasses import dataclass

@dataclass
class GameConfig:
    width: int = 30
    height: int = 18
    tile: int = 32
    fps: int = 30

    # gameplay
    max_time_s: float = 300.0  # 5 minutes default
    move_speed: float = 6.0    # tiles per second-ish (scaled)
    gather_time_s: float = 1.0
    craft_time_s: float = 2.0

    # economy
    resources_on_map: int = 20
    resource_respawn_s: float = 12.0
    craft_cost: int = 3

    # combat
    attack_cooldown_s: float = 0.6
    attack_range: float = 1.2
    attack_damage: int = 20
    max_hp: int = 100

    # jewel
    capture_hold_s: float = 0.0  # set >0 to require holding at base
