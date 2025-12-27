import math
from typing import Optional
from .core import JewelWar, dist, norm

class ScriptBot:
    """A decent scripted baseline: farm -> craft -> steal -> return; fight if close."""
    def __init__(self, aggressiveness: float = 0.6):
        self.aggr = aggressiveness

    def act(self, game: JewelWar, team: int) -> int:
        a = game.agents[team]
        enemy = 1 - team
        e = game.agents[enemy]

        # if enemy close, maybe attack
        if dist(a.pos, e.pos) <= game.cfg.attack_range and a.cooldown <= 0 and a.busy <= 0:
            if game.rng.random() < self.aggr:
                return 7  # attack

        # if carrying jewel, go home & interact
        if a.has_jewel:
            if dist(a.pos, game.bases[team]) <= 1.5:
                return 8
            return self._move_towards(game, team, game.bases[team])

        # try steal enemy jewel if near
        enemy_jewel = game.jewels[enemy]
        if enemy_jewel.carried_by_team is None:
            if dist(a.pos, enemy_jewel.pos) <= 1.2:
                return 8
            # sometimes rush steal when crafted
            if a.weapon_level >= 1 or game.rng.random() < 0.15:
                return self._move_towards(game, team, enemy_jewel.pos)

        # craft if enough and at base
        if a.resources >= game.cfg.craft_cost and dist(a.pos, game.bases[team]) <= 1.5 and a.busy <= 0:
            return 6

        # if enough resources, go base to craft
        if a.resources >= game.cfg.craft_cost and a.weapon_level < 2:
            return self._move_towards(game, team, game.bases[team])

        # gather if on resource
        # (core gathers nearest if in range)
        if a.busy <= 0:
            # move to nearest resource; if close, gather
            ridx = game._nearest_resource(a.pos)
            if ridx is not None:
                r = game.resources[ridx]
                if r.alive and dist(a.pos, r.pos) <= 1.0:
                    return 5
                return self._move_towards(game, team, r.pos)

        return 0

    def _move_towards(self, game: JewelWar, team: int, target) -> int:
        a = game.agents[team]
        dx = target[0] - a.pos[0]
        dy = target[1] - a.pos[1]
        # choose cardinal direction
        if abs(dx) > abs(dy):
            return 4 if dx > 0 else 3
        else:
            return 2 if dy > 0 else 1
