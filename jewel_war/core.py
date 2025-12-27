import math
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

import numpy as np

from .config import GameConfig

Vec2 = Tuple[float, float]

def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

def dist(a: Vec2, b: Vec2) -> float:
    return math.hypot(a[0]-b[0], a[1]-b[1])

def norm(vx, vy):
    d = math.hypot(vx, vy)
    if d < 1e-9:
        return 0.0, 0.0
    return vx/d, vy/d

@dataclass
class AgentState:
    pos: Vec2
    hp: int
    resources: int
    has_jewel: bool
    weapon_level: int
    cooldown: float
    busy: float

@dataclass
class ResourceNode:
    pos: Vec2
    alive: bool = True
    respawn: float = 0.0

@dataclass
class Jewel:
    home_team: int
    pos: Vec2
    carried_by_team: Optional[int] = None  # team index
    at_home: bool = True

class JewelWar:
    """Core simulation. Two teams by default (0=Blue, 1=Red).
    Real-time discrete steps; all mechanics are deterministic given RNG seed.
    """

    def __init__(self, cfg: GameConfig, seed: Optional[int] = None):
        self.cfg = cfg
        self.rng = random.Random(seed)
        self.t = 0.0
        self.done = False
        self.winner: Optional[int] = None
        self.max_steps = int(cfg.max_time_s * cfg.fps)

        self.walls = self._gen_walls()
        self.bases = [(2.0, cfg.height/2), (cfg.width-3.0, cfg.height/2)]
        self.spawn = [(3.5, cfg.height/2), (cfg.width-4.5, cfg.height/2)]
        self.jewels = [
            Jewel(home_team=0, pos=self.bases[0]),
            Jewel(home_team=1, pos=self.bases[1]),
        ]

        self.resources: List[ResourceNode] = []
        self._spawn_resources()

        self.agents = [
            AgentState(pos=self.spawn[0], hp=cfg.max_hp, resources=0, has_jewel=False, weapon_level=0, cooldown=0.0, busy=0.0),
            AgentState(pos=self.spawn[1], hp=cfg.max_hp, resources=0, has_jewel=False, weapon_level=0, cooldown=0.0, busy=0.0),
        ]

        self._capture_hold: Dict[int, float] = {0: 0.0, 1: 0.0}

    def _gen_walls(self):
        # Simple symmetric obstacles to create strategy/chokepoints.
        w, h = self.cfg.width, self.cfg.height
        walls = set()
        # Border walls (implicit); keep open. Add some blocks.
        for x in range(8, w-8, 6):
            for y in range(3, h-3, 6):
                # small 2x2 blocks
                for dx in range(2):
                    for dy in range(2):
                        walls.add((x+dx, y+dy))
                        walls.add((w-1-(x+dx), y+dy))  # mirror
        # Middle column sparse blockers
        mid = w//2
        for y in range(2, h-2, 4):
            if y % 8 != 0:
                walls.add((mid, y))
        return walls

    def _spawn_resources(self):
        self.resources.clear()
        attempts = 0
        while len(self.resources) < self.cfg.resources_on_map and attempts < 5000:
            attempts += 1
            x = self.rng.uniform(4, self.cfg.width-5)
            y = self.rng.uniform(2, self.cfg.height-3)
            tx, ty = int(x), int(y)
            if (tx, ty) in self.walls:
                continue
            # keep away from bases
            if dist((x,y), self.bases[0]) < 4 or dist((x,y), self.bases[1]) < 4:
                continue
            self.resources.append(ResourceNode(pos=(x,y), alive=True, respawn=0.0))

    def reset(self, seed: Optional[int] = None):
        if seed is not None:
            self.rng.seed(seed)
        self.__init__(self.cfg, seed=None)
        return self

    def _blocked(self, x: float, y: float) -> bool:
        if x < 0.5 or y < 0.5 or x > self.cfg.width-1.5 or y > self.cfg.height-1.5:
            return True
        tx, ty = int(x), int(y)
        return (tx, ty) in self.walls

    def _move(self, team: int, dx: float, dy: float, dt: float):
        a = self.agents[team]
        if a.busy > 0:
            return
        speed = self.cfg.move_speed * (1.0 + 0.25*a.weapon_level)  # weapon level slightly buffs speed (feel of progression)
        nx = a.pos[0] + dx * speed * dt
        ny = a.pos[1] + dy * speed * dt

        # simple collision: try x then y
        if not self._blocked(nx, a.pos[1]):
            a.pos = (nx, a.pos[1])
        if not self._blocked(a.pos[0], ny):
            a.pos = (a.pos[0], ny)

    def _nearest_resource(self, pos: Vec2) -> Optional[int]:
        best = None
        bestd = 1e9
        for i, r in enumerate(self.resources):
            if not r.alive:
                continue
            d = dist(pos, r.pos)
            if d < bestd:
                bestd = d
                best = i
        return best

    def _gather(self, team: int):
        a = self.agents[team]
        if a.busy > 0:
            return False
        idx = self._nearest_resource(a.pos)
        if idx is None:
            return False
        r = self.resources[idx]
        if not r.alive:
            return False
        if dist(a.pos, r.pos) <= 1.0:
            a.busy = self.cfg.gather_time_s
            # mark for collection at end of busy
            r.alive = False
            r.respawn = self.cfg.resource_respawn_s
            a.resources += 1
            return True
        return False

    def _craft(self, team: int):
        a = self.agents[team]
        if a.busy > 0:
            return False
        if dist(a.pos, self.bases[team]) <= 1.5 and a.resources >= self.cfg.craft_cost:
            a.busy = self.cfg.craft_time_s
            a.resources -= self.cfg.craft_cost
            a.weapon_level = min(a.weapon_level + 1, 3)
            return True
        return False

    def _attack(self, team: int):
        a = self.agents[team]
        if a.busy > 0 or a.cooldown > 0:
            return False
        enemy = 1 - team
        e = self.agents[enemy]
        if e.hp <= 0:
            return False
        if dist(a.pos, e.pos) <= self.cfg.attack_range:
            dmg = self.cfg.attack_damage + 10 * a.weapon_level
            e.hp = max(0, e.hp - dmg)
            a.cooldown = self.cfg.attack_cooldown_s
            # if enemy dies, drop jewel if carried
            if e.hp == 0:
                if self.jewels[team].carried_by_team == enemy:
                    # not possible; each jewel carried by team that took it; use state in jewel list
                    pass
                for j in self.jewels:
                    if j.carried_by_team == enemy:
                        j.carried_by_team = None
                        j.at_home = False
                        j.pos = e.pos
                # respawn enemy
                e.pos = self.spawn[enemy]
                e.hp = self.cfg.max_hp
                e.has_jewel = False
                e.weapon_level = max(0, e.weapon_level-1)  # setback
            return True
        return False

    def _interact_jewel(self, team: int):
        """Steal enemy jewel if at enemy base or pick up dropped jewel; also deliver to own base."""
        a = self.agents[team]
        if a.busy > 0:
            return False
        enemy = 1 - team

        # If carrying enemy jewel, try deliver to home base
        if a.has_jewel:
            if dist(a.pos, self.bases[team]) <= 1.5:
                if self.cfg.capture_hold_s <= 0:
                    self.done = True
                    self.winner = team
                else:
                    self._capture_hold[team] += 1.0 / self.cfg.fps
                    if self._capture_hold[team] >= self.cfg.capture_hold_s:
                        self.done = True
                        self.winner = team
                return True
            else:
                # reset hold if moved away
                self._capture_hold[team] = 0.0

        # Try pick up enemy jewel if near it and not carried
        enemy_jewel = self.jewels[enemy]
        if not a.has_jewel and enemy_jewel.carried_by_team is None and dist(a.pos, enemy_jewel.pos) <= 1.2:
            enemy_jewel.carried_by_team = team
            enemy_jewel.at_home = False
            a.has_jewel = True
            return True

        return False

    def step(self, action_team0: int, action_team1: int, dt: float):
        """Advance simulation by dt seconds. Actions are discrete integers.
        Returns dict with info.
        """
        if self.done:
            return {"done": True, "winner": self.winner}

        self.t += dt

        # Update cooldowns/busy and resource respawns
        for a in self.agents:
            a.cooldown = max(0.0, a.cooldown - dt)
            a.busy = max(0.0, a.busy - dt)

        for r in self.resources:
            if not r.alive:
                r.respawn -= dt
                if r.respawn <= 0:
                    r.alive = True
                    r.respawn = 0.0

        # Update jewels positions if carried
        for j in self.jewels:
            if j.carried_by_team is not None:
                j.pos = self.agents[j.carried_by_team].pos

        # Execute actions for each team
        for team, action in [(0, action_team0), (1, action_team1)]:
            if self.agents[team].hp <= 0:
                continue
            self._apply_action(team, action, dt)

        # Check time limit
        if self.t >= self.cfg.max_time_s:
            self.done = True
            # decide by who is carrying jewel / resources as tiebreak
            if self.agents[0].has_jewel and not self.agents[1].has_jewel:
                self.winner = 0
            elif self.agents[1].has_jewel and not self.agents[0].has_jewel:
                self.winner = 1
            else:
                self.winner = 0 if self.agents[0].resources >= self.agents[1].resources else 1

        return {"done": self.done, "winner": self.winner}

    def _apply_action(self, team: int, action: int, dt: float):
        # 0 noop
        if action == 1:   # up
            self._move(team, 0, -1, dt)
        elif action == 2: # down
            self._move(team, 0, 1, dt)
        elif action == 3: # left
            self._move(team, -1, 0, dt)
        elif action == 4: # right
            self._move(team, 1, 0, dt)
        elif action == 5: # gather
            self._gather(team)
        elif action == 6: # craft
            self._craft(team)
        elif action == 7: # attack
            self._attack(team)
        elif action == 8: # interact jewel / deliver
            self._interact_jewel(team)

    def get_obs(self, team: int) -> np.ndarray:
        """Observation vector for a team."""
        a = self.agents[team]
        enemy = 1 - team
        e = self.agents[enemy]
        # normalize positions to [0,1]
        ax, ay = a.pos[0]/self.cfg.width, a.pos[1]/self.cfg.height
        ex, ey = e.pos[0]/self.cfg.width, e.pos[1]/self.cfg.height
        # jewel positions
        my_jewel = self.jewels[team]
        en_jewel = self.jewels[enemy]
        mjx, mjy = my_jewel.pos[0]/self.cfg.width, my_jewel.pos[1]/self.cfg.height
        ejx, ejy = en_jewel.pos[0]/self.cfg.width, en_jewel.pos[1]/self.cfg.height
        # bases
        mbx, mby = self.bases[team][0]/self.cfg.width, self.bases[team][1]/self.cfg.height
        ebx, eby = self.bases[enemy][0]/self.cfg.width, self.bases[enemy][1]/self.cfg.height

        # nearest resource (alive)
        ridx = self._nearest_resource(a.pos)
        if ridx is None:
            rx, ry, rdist = 0.0, 0.0, 1.0
        else:
            r = self.resources[ridx]
            rx, ry = r.pos[0]/self.cfg.width, r.pos[1]/self.cfg.height
            rdist = min(1.0, dist(a.pos, r.pos)/max(self.cfg.width, self.cfg.height))

        obs = np.array([
            ax, ay,
            ex, ey,
            mjx, mjy,
            ejx, ejy,
            mbx, mby,
            ebx, eby,
            rx, ry, rdist,
            a.hp / self.cfg.max_hp,
            e.hp / self.cfg.max_hp,
            min(1.0, a.resources/10.0),
            min(1.0, e.resources/10.0),
            float(a.has_jewel),
            float(e.has_jewel),
            a.weapon_level/3.0,
            e.weapon_level/3.0,
            min(1.0, a.cooldown/2.0),
            min(1.0, a.busy/2.0),
        ], dtype=np.float32)
        return obs
