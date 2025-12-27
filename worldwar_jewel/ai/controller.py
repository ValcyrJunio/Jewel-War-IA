"""
Low-level controller placeholder. In V2 this would handle pathfinding and micro.
For now it forwards planner actions directly to the world.
"""

from typing import Dict, Tuple

from worldwar_jewel.game.world import ActionCommand


class PassthroughController:
    def __init__(self, team_id: int):
        self.team_id = team_id

    def act(self, planner_actions: Dict[Tuple[int, int], ActionCommand]) -> Dict[Tuple[int, int], ActionCommand]:
        return planner_actions

