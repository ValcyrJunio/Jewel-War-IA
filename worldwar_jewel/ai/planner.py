import math
import random
from typing import Dict, Tuple

from worldwar_jewel.game.world import ActionCommand, World
from worldwar_jewel.game.pathfinding import a_star

Vec2 = Tuple[float, float]


def _dir(a: Vec2, b: Vec2) -> Vec2:
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy)
    if d < 1e-5:
        return 0.0, 0.0
    return dx / d, dy / d


class SimplePlanner:
    """Heuristic AI for squads. Focuses on gather->build->steal jewel."""

    def __init__(self, team_id: int):
        self.team_id = team_id
        self.rng = random.Random(team_id * 991)

    def act(self, world: World) -> Dict[Tuple[int, int], ActionCommand]:
        actions: Dict[Tuple[int, int], ActionCommand] = {}
        team_units = world.get_team_units(self.team_id)
        for idx, u in enumerate(team_units):
            if not u.is_alive():
                continue
            # carry jewel: run home
            if u.has_jewel:
                home = world.layout.bases[self.team_id]
                if math.hypot(u.pos[0] - home[0], u.pos[1] - home[1]) <= 1.5:
                    actions[(self.team_id, idx)] = ActionCommand(kind="interact")
                else:
                    dx, dy = _dir(u.pos, home)
                    actions[(self.team_id, idx)] = ActionCommand(kind="move", target=(dx, dy))
                continue

            # engineer: build turret then wall, else gather
            if u.cls_id == "engineer":
                if self._need_turret(world) and self._can_afford(world, "turret"):
                    actions[(self.team_id, idx)] = self._step_towards(world, u, world.layout.bases[self.team_id], fallback=ActionCommand(kind="build_turret"))
                elif self._can_afford(world, "wall"):
                    actions[(self.team_id, idx)] = self._step_towards(world, u, world.layout.bases[self.team_id], fallback=ActionCommand(kind="build_wall"))
                elif self._can_afford(world, "wall"):
                    actions[(self.team_id, idx)] = ActionCommand(kind="build_wall")
                else:
                    actions[(self.team_id, idx)] = self._gather_or_move(world, u)
                continue

            # scout: try steal jewel
            if u.cls_id == "scout":
                target_jewel = next((j for j in world.jewels if j.home_team != self.team_id and j.carried_by is None), None)
                if target_jewel:
                    if math.hypot(u.pos[0] - target_jewel.pos[0], u.pos[1] - target_jewel.pos[1]) <= 1.2:
                        actions[(self.team_id, idx)] = ActionCommand(kind="interact")
                    else:
                        actions[(self.team_id, idx)] = self._step_towards(world, u, target_jewel.pos)
                    continue
            # assault default: attack nearest enemy or building
            actions[(self.team_id, idx)] = ActionCommand(kind="attack")
        return actions

    def _gather_or_move(self, world: World, unit):
        node = world._nearest_resource(unit.pos)  # type: ignore[attr-defined]
        if node and math.hypot(unit.pos[0] - node.pos[0], unit.pos[1] - node.pos[1]) <= 1.0:
            return ActionCommand(kind="gather")
        if node:
            return self._step_towards(world, unit, node.pos)
        return ActionCommand(kind="noop")

    def _can_afford(self, world: World, building_kind: str) -> bool:
        team = world.teams[self.team_id]
        cost = worldwar_cost(building_kind)
        return all(team.resources.get(k, 0) >= v for k, v in cost.items())

    def _need_turret(self, world: World) -> bool:
        team = world.teams[self.team_id]
        return not any(b.kind == "turret" and b.is_alive() for b in team.buildings)

    def _step_towards(self, world: World, unit, target: Vec2, fallback: ActionCommand | None = None) -> ActionCommand:
        """Pathfind around walls/blocks; falls back to straight line."""
        start = (int(unit.pos[0]), int(unit.pos[1]))
        goal = (int(target[0]), int(target[1]))
        blocked = world.blocked_cells()
        if goal in blocked:
            goal = (goal[0] + self.rng.choice([-1, 1]), goal[1] + self.rng.choice([-1, 1]))
        if start in blocked:
            start = (max(1, start[0] - 1), max(1, start[1] - 1))
        path = a_star(start, goal, blocked, (world.cfg.width, world.cfg.height))
        if path:
            nx, ny = path[0]
            dx, dy = nx + 0.5 - unit.pos[0], ny + 0.5 - unit.pos[1]
            return ActionCommand(kind="move", target=_dir(unit.pos, (unit.pos[0] + dx, unit.pos[1] + dy)))
        # fallback straight move or provided action
        if fallback:
            return fallback
        dx, dy = _dir(unit.pos, target)
        return ActionCommand(kind="move", target=(dx, dy))


def worldwar_cost(kind: str) -> Dict[str, int]:
    from worldwar_jewel.config import BUILDING_PRESETS

    return BUILDING_PRESETS[kind].cost
