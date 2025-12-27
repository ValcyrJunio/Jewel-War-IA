"""
Self-play scaffolding. Hook into RL or scripted league.
Currently provides a simple loop that pits two planners against each other for testing.
"""

from typing import Dict, Tuple

from worldwar_jewel.ai.planner import SimplePlanner
from worldwar_jewel.game.world import ActionCommand, World


def rollout_once(seed: int | None = None) -> Tuple[int | None, World]:
    world = World(seed=seed)
    planners = [SimplePlanner(tid) for tid in range(world.cfg.team_count)]
    dt = 1.0 / world.cfg.fps
    for _ in range(int(world.cfg.max_time_s * world.cfg.fps)):
        acts: Dict[Tuple[int, int], ActionCommand] = {}
        for p in planners:
            acts.update(p.act(world))
        info = world.step(acts, dt)
        if info["done"]:
            break
    return world.winner, world

