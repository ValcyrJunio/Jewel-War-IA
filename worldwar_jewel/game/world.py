import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

from worldwar_jewel.config import (
    BUILDING_PRESETS,
    CLASS_PRESETS,
    TEAM_PROFILES,
    BuildingStats,
    ClassStats,
    GameTuning,
)
from worldwar_jewel.game.entities import Building, Jewel, ResourceNode, Unit
from worldwar_jewel.game.mapgen import MapLayout, generate_map
from worldwar_jewel.game.pathfinding import a_star
from worldwar_jewel.game.systems import capture_rules, combat
from worldwar_jewel.game.systems.building_system import repair, start_build

Vec2 = Tuple[float, float]


@dataclass
class ActionCommand:
    kind: str
    target: Optional[Vec2] = None
    extra: Optional[str] = None


ACTION_SHORTCUTS: Dict[int, str] = {
    0: "noop",
    1: "up",
    2: "down",
    3: "left",
    4: "right",
    5: "gather",
    6: "build_wall",
    7: "attack",
    8: "interact",
    9: "plant_explosive",
    10: "repair",
    11: "build_turret",
}


def _action_from_int(val: int) -> ActionCommand:
    kind = ACTION_SHORTCUTS.get(int(val), "noop")
    if kind in ("up", "down", "left", "right"):
        dx, dy = 0.0, 0.0
        if kind == "up":
            dy = -1.0
        elif kind == "down":
            dy = 1.0
        elif kind == "left":
            dx = -1.0
        elif kind == "right":
            dx = 1.0
        return ActionCommand(kind="move", target=(dx, dy))
    return ActionCommand(kind=kind)


@dataclass
class TeamState:
    id: int
    name: str
    color: Tuple[int, int, int]
    resources: Dict[str, int]
    units: List[Unit]
    buildings: List[Building]
    eliminated: bool = False


class World:
    """Tri-faction RTS core loop with jewels and base destruction."""

    def __init__(
        self,
        cfg: GameTuning | None = None,
        seed: Optional[int] = None,
        team_classes: Optional[Dict[int, List[str]]] = None,
    ):
        self.cfg = cfg or GameTuning()
        self.rng = random.Random(seed)
        self.layout: MapLayout = generate_map(self.cfg, self.cfg.team_count, seed=seed)
        self.t = 0.0
        self.done = False
        self.winner: Optional[int] = None

        self.resources: List[ResourceNode] = []
        self.units: List[Unit] = []
        self.buildings: List[Building] = []
        self.jewels: List[Jewel] = []
        self.teams: Dict[int, TeamState] = {}
        self._hold_timers: Dict[int, float] = {}
        self._next_unit_id = 0
        self._next_building_id = 0
        self.spawns = self.layout.spawns

        self._spawn_entities(team_classes=team_classes)

    # ------------------------------------------------------------------ setup
    def _spawn_entities(self, team_classes: Optional[Dict[int, List[str]]]):
        # Resources
        for i, (rtype, pos) in enumerate(self.layout.resource_spots):
            node = ResourceNode(id=i, rtype=rtype, pos=pos, amount=1, alive=True, respawn=0.0)
            self.resources.append(node)

        for tid in range(self.cfg.team_count):
            profile = TEAM_PROFILES[tid % len(TEAM_PROFILES)]
            classes = team_classes.get(tid) if team_classes else None
            if not classes:
                classes = ["engineer", "assault", "scout"]
            classes = (classes * 3)[: self.cfg.squad_size]  # fill
            units = []
            for ci, cls_id in enumerate(classes):
                stats = CLASS_PRESETS[cls_id]
                pos = self._find_open_near(self.layout.spawns[min(tid, len(self.layout.spawns) - 1)])
                u = Unit(
                    id=self._next_unit_id,
                    team_id=tid,
                    cls_id=cls_id,
                    stats=stats,
                    pos=(pos[0] + self.rng.uniform(-0.4, 0.4), pos[1] + self.rng.uniform(-0.4, 0.4)),
                    hp=stats.max_hp,
                )
                units.append(u)
                self.units.append(u)
                self._next_unit_id += 1

            # Base buildings
            core_stats = BUILDING_PRESETS["core"]
            base_pos = self.layout.bases[min(tid, len(self.layout.bases) - 1)]
            core = Building(
                id=self._next_building_id,
                team_id=tid,
                kind="core",
                stats=core_stats,
                pos=base_pos,
                hp=core_stats.max_hp,
                constructing=False,
                progress=core_stats.build_time,
            )
            self.buildings.append(core)
            self._next_building_id += 1

            jewel = Jewel(home_team=tid, pos=base_pos)
            self.jewels.append(jewel)
            team_state = TeamState(
                id=tid,
                name=profile.name,
                color=profile.color,
                resources={"wood": 6, "metal": 4, "fuel": 2},
                units=units,
                buildings=[core],
                eliminated=False,
            )
            self.teams[tid] = team_state
            self._hold_timers[tid] = 0.0

    # ------------------------------------------------------------------- utils
    def _blocked(self, x: float, y: float) -> bool:
        if x < 0.5 or y < 0.5 or x > self.cfg.width - 1.5 or y > self.cfg.height - 1.5:
            return True
        tx, ty = int(x), int(y)
        if (tx, ty) in self.layout.walls:
            return True
        for b in self.buildings:
            if b.stats.blocks_movement and b.is_alive():
                if abs(b.pos[0] - x) < 0.7 and abs(b.pos[1] - y) < 0.7:
                    return True
        return False

    def blocked_cells(self) -> set[tuple[int, int]]:
        blocked = set(self.layout.walls)
        for b in self.buildings:
            if b.stats.blocks_movement and b.is_alive():
                blocked.add((int(b.pos[0]), int(b.pos[1])))
        return blocked

    def _core_alive(self, team_id: int) -> bool:
        return any(b.kind == "core" and b.is_alive() for b in self.buildings if b.team_id == team_id)

    def _find_open_near(self, pos: Vec2) -> Vec2:
        """Find nearest free cell to pos."""
        cx, cy = int(pos[0]), int(pos[1])
        blocked = self.blocked_cells()
        for radius in range(5):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    tx, ty = cx + dx, cy + dy
                    if tx < 1 or ty < 1 or tx >= self.cfg.width - 1 or ty >= self.cfg.height - 1:
                        continue
                    if (tx, ty) in blocked:
                        continue
                    return (tx + 0.5, ty + 0.5)
        return pos

    def _move(self, unit: Unit, dx: float, dy: float, dt: float):
        if not unit.is_alive() or unit.busy > 0:
            return
        speed = unit.stats.move_speed
        if unit.has_jewel:
            speed *= self.cfg.jewel_carry_slow * unit.stats.carry_slow
        nx = unit.pos[0] + dx * speed * dt
        ny = unit.pos[1] + dy * speed * dt
        if not self._blocked(nx, unit.pos[1]):
            unit.pos = (nx, unit.pos[1])
        if not self._blocked(unit.pos[0], ny):
            unit.pos = (unit.pos[0], ny)

    def _nearest_resource(self, pos: Vec2) -> Optional[ResourceNode]:
        best = None
        bestd = 1e9
        for r in self.resources:
            if not r.alive:
                continue
            d = math.hypot(pos[0] - r.pos[0], pos[1] - r.pos[1])
            if d < bestd:
                bestd = d
                best = r
        return best

    def _gather(self, unit: Unit, team: TeamState) -> bool:
        if unit.busy > 0 or not unit.is_alive():
            return False
        r = self._nearest_resource(unit.pos)
        if r is None or not r.alive:
            return False
        if math.hypot(unit.pos[0] - r.pos[0], unit.pos[1] - r.pos[1]) > 1.1:
            return False
        unit.busy = self.cfg.gather_time_s / max(0.3, unit.stats.gather_speed)
        r.alive = False
        r.respawn = self.cfg.resource_respawn_s
        team.resources[r.rtype] = team.resources.get(r.rtype, 0) + r.amount
        return True

    def _start_build(self, unit: Unit, team: TeamState, kind: str) -> bool:
        stats = BUILDING_PRESETS[kind]
        # Place in front of unit (rounded to grid)
        px, py = unit.pos
        bx, by = round(px + 0.8), round(py)
        # Avoid overlap with walls/buildings
        if self._blocked(bx, by):
            return False
        b = start_build(team.id, self._next_building_id, kind, stats, (bx, by), team.resources)
        if not b:
            return False
        b.constructing = True if stats.build_time > 0 else False
        b.progress = 0.0
        self.buildings.append(b)
        team.buildings.append(b)
        self._next_building_id += 1
        unit.busy = stats.build_time / max(0.2, unit.stats.build_speed)
        return True

    def _repair(self, unit: Unit, team: TeamState) -> bool:
        # Repair closest damaged friendly building
        damaged = [b for b in team.buildings if b.hp > 0 and b.hp < b.stats.max_hp]
        if not damaged:
            return False
        damaged.sort(key=lambda b: math.hypot(unit.pos[0] - b.pos[0], unit.pos[1] - b.pos[1]))
        for b in damaged:
            if math.hypot(unit.pos[0] - b.pos[0], unit.pos[1] - b.pos[1]) <= 1.3:
                return repair(unit, b, amount=12)
        return False

    # ------------------------------------------------------------------- apply
    def _apply_action(self, unit: Unit, team: TeamState, action: ActionCommand, dt: float):
        if action.kind == "move" and action.target:
            dx, dy = action.target
            norm = math.hypot(dx, dy)
            if norm > 0.001:
                self._move(unit, dx / norm, dy / norm, dt)
        elif action.kind == "gather":
            self._gather(unit, team)
        elif action.kind == "attack":
            self._attack_closest_enemy(unit)
        elif action.kind == "plant_explosive":
            self._attack_building(unit, bonus=2.0)
        elif action.kind == "interact":
            self._interact_jewel(unit, team, dt)
        elif action.kind == "build_wall" and unit.cls_id == "engineer":
            self._start_build(unit, team, "wall")
        elif action.kind == "build_turret" and unit.cls_id == "engineer":
            self._start_build(unit, team, "turret")
        elif action.kind == "repair" and unit.cls_id == "engineer":
            self._repair(unit, team)

    def _attack_closest_enemy(self, unit: Unit):
        enemies = [u for u in self.units if u.team_id != unit.team_id and u.is_alive()]
        if not enemies:
            return
        enemies.sort(key=lambda e: math.hypot(e.pos[0] - unit.pos[0], e.pos[1] - unit.pos[1]))
        target = enemies[0]
        if combat.unit_attack(unit, target):
            if target.hp == 0 and target.has_jewel:
                self._drop_jewel_from_unit(target)
            if target.hp == 0:
                target.respawn_timer = max(target.respawn_timer, self.cfg.respawn_time_s)

    def _attack_building(self, unit: Unit, bonus: float):
        buildings = [b for b in self.buildings if b.team_id != unit.team_id and b.is_alive()]
        if not buildings:
            return
        buildings.sort(key=lambda b: math.hypot(b.pos[0] - unit.pos[0], b.pos[1] - unit.pos[1]))
        target = buildings[0]
        before_hp = target.hp
        if combat.attack_building(unit, target, bonus=bonus):
            if target.hp == 0 and target.stats.is_core:
                self._on_core_destroyed(target.team_id, target.pos)
            if before_hp > 0 and target.hp == 0:
                # Drop jewel of this team on the ruins
                for j in self.jewels:
                    if j.home_team == target.team_id and j.carried_by is None and j.at_home:
                        j.pos = target.pos
                        j.at_home = False

    def _drop_jewel_from_unit(self, unit: Unit):
        for j in self.jewels:
            if j.carried_by == unit.id:
                j.drop(unit.pos)
        unit.has_jewel = False

    def _interact_jewel(self, unit: Unit, team: TeamState, dt: float):
        # deliver if carrying
        if unit.has_jewel:
            jewel = next(j for j in self.jewels if j.carried_by == unit.id)
            base_pos = self.layout.bases[team.id]
            if capture_rules.try_deliver(team.id, unit, jewel, base_pos, self._hold_timers, self.cfg.capture_hold_s, dt):
                self.done = True
                self.winner = team.id
                return
        else:
            # Try pick up enemy jewel
            for j in self.jewels:
                if j.home_team == team.id:
                    continue
                if j.carried_by is None and math.hypot(unit.pos[0] - j.pos[0], unit.pos[1] - j.pos[1]) <= 1.2:
                    j.carried_by = unit.id
                    j.at_home = False
                    unit.has_jewel = True
                    break

    # ------------------------------------------------------------------- ticks
    def _tick_resources(self, dt: float):
        for r in self.resources:
            r.tick(dt, self.cfg.resource_respawn_s)

    def _tick_buildings(self, dt: float):
        for b in self.buildings:
            if not b.is_alive():
                continue
            b.tick(dt)
            if b.constructing:
                # Allow faster build based on nearby engineers
                speed_bonus = 1.0
                for u in self.units:
                    if u.team_id == b.team_id and u.is_alive():
                        if math.hypot(u.pos[0] - b.pos[0], u.pos[1] - b.pos[1]) <= 2.2 and u.cls_id == "engineer":
                            speed_bonus = max(speed_bonus, u.stats.build_speed)
                b.progress += dt * (speed_bonus - 1.0)

    def _tick_units(self, dt: float):
        for u in self.units:
            if u.hp <= 0:
                # dead; count respawn
                u.respawn_timer -= dt
                if u.respawn_timer <= 0 and self._core_alive(u.team_id):
                    spawn = self._find_open_near(self.spawns[u.team_id])
                    u.pos = spawn
                    u.hp = u.stats.max_hp
                    u.cooldown = 0.0
                    u.busy = 0.0
                    u.has_jewel = False
                    u.respawn_timer = 0.0
                continue
            u.tick_timers(dt)

    def _update_jewels(self):
        for j in self.jewels:
            if j.carried_by is not None:
                carrier = next((u for u in self.units if u.id == j.carried_by), None)
                if carrier and carrier.is_alive():
                    j.pos = carrier.pos
                else:
                    j.carried_by = None
                    j.at_home = False

    def _turrets_fire(self):
        for b in self.buildings:
            if not b.is_alive() or b.kind != "turret":
                continue
            enemies = [u for u in self.units if u.team_id != b.team_id]
            hit = combat.turret_fire(b, enemies)
            if hit is not None:
                victim = next((u for u in self.units if u.id == hit), None)
                if victim and victim.hp == 0 and victim.has_jewel:
                    self._drop_jewel_from_unit(victim)

    # ------------------------------------------------------------------- rules
    def _on_core_destroyed(self, team_id: int, pos: Vec2):
        self.teams[team_id].eliminated = True
        # Drop jewel to the ruin if it was at home
        for j in self.jewels:
            if j.home_team == team_id and j.at_home:
                j.pos = pos
                j.at_home = False
        # Remove respawn support by flagging elimination; units remain until killed
        for u in self.units:
            if u.team_id == team_id and u.hp <= 0:
                u.respawn_timer = 1e9

    def _check_victory(self):
        alive = []
        for tid, team in self.teams.items():
            core_alive = any(b.kind == "core" and b.is_alive() for b in team.buildings)
            if core_alive:
                alive.append(tid)
            else:
                self.teams[tid].eliminated = True
        if self.cfg.domination_enabled and len(alive) == 1:
            self.done = True
            self.winner = alive[0]

    # ------------------------------------------------------------------- API
    def step(self, actions: Dict[Tuple[int, int], Union[ActionCommand, int]], dt: float) -> Dict:
        if self.done:
            return {"done": True, "winner": self.winner}

        self.t += dt
        self._tick_units(dt)
        self._tick_resources(dt)
        self._tick_buildings(dt)
        self._update_jewels()

        # Auto turrets fire before actions resolve
        self._turrets_fire()

        # Apply actions per unit
        for (team_id, unit_idx), act in actions.items():
            # Safety: find unit by global index
            team_units = [u for u in self.units if u.team_id == team_id]
            if unit_idx >= len(team_units):
                continue
            unit = team_units[unit_idx]
            team = self.teams.get(team_id)
            if team is None or team.eliminated:
                continue
            if unit.hp <= 0:
                continue
            if isinstance(act, int):
                action_cmd = _action_from_int(act)
            else:
                action_cmd = act
            self._apply_action(unit, team, action_cmd, dt)

        # Move jewels with carriers after movement
        self._update_jewels()
        self._check_victory()

        if self.t >= self.cfg.max_time_s and not self.done:
            # Decide winner by jewel proximity or resource
            scores = []
            for tid, team in self.teams.items():
                dist_home = 0.0
                enemy_jewel = next((j for j in self.jewels if j.home_team != tid and j.carried_by and any(u.id == j.carried_by for u in self.units if u.team_id == tid)), None)
                if enemy_jewel:
                    dist_home = 0.0
                else:
                    dist_home = sum(math.hypot(j.pos[0] - self.layout.bases[tid][0], j.pos[1] - self.layout.bases[tid][1]) for j in self.jewels if j.home_team != tid)
                res_score = team.resources.get("wood", 0) + 1.4 * team.resources.get("metal", 0) + 1.6 * team.resources.get("fuel", 0)
                scores.append((res_score - dist_home, tid))
            scores.sort(reverse=True)
            self.done = True
            self.winner = scores[0][1]

        info = {"done": self.done, "winner": self.winner, "time": self.t}
        return info

    # ----------------------------------------------------------------- helpers
    def get_team_units(self, team_id: int) -> List[Unit]:
        return [u for u in self.units if u.team_id == team_id]

    def observation_snapshot(self) -> Dict:
        """Lightweight snapshot for UI."""
        return {
            "time": self.t,
            "teams": {
                tid: {
                    "resources": dict(team.resources),
                    "eliminated": team.eliminated,
                    "units": [
                        {
                            "pos": u.pos,
                            "hp": u.hp,
                            "cls": u.cls_id,
                            "has_jewel": u.has_jewel,
                        }
                        for u in self.units
                        if u.team_id == tid
                    ],
                    "buildings": [
                        {
                            "pos": b.pos,
                            "hp": b.hp,
                            "kind": b.kind,
                        }
                        for b in self.buildings
                        if b.team_id == tid and b.is_alive()
                    ],
                }
                for tid, team in self.teams.items()
            },
            "jewels": [
                {"team": j.home_team, "pos": j.pos, "carried_by": j.carried_by, "at_home": j.at_home} for j in self.jewels
            ],
        }
