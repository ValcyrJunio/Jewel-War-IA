import numpy as np
import gymnasium as gym
from gymnasium import spaces

from worldwar_jewel.ai.planner import SimplePlanner
from worldwar_jewel.config import GameTuning
from worldwar_jewel.game.world import ACTION_SHORTCUTS, ActionCommand, World


class WorldWarEnv(gym.Env):
    """Headless env controlling team 0 squad (3 units). Other teams use SimplePlanner."""

    metadata = {"render_modes": []}

    def __init__(self, cfg: GameTuning | None = None, seed: int | None = None):
        super().__init__()
        self.cfg = cfg or GameTuning()
        self.seed_val = seed
        self.world = World(self.cfg, seed=seed)
        self.opponents = [SimplePlanner(tid) for tid in range(1, self.cfg.team_count)]
        self.squad_size = self.cfg.squad_size
        self.action_space = spaces.MultiDiscrete([len(ACTION_SHORTCUTS)] * self.squad_size)
        # Observation: for each of 3 units -> pos(x,y), hp, has_jewel + closest enemy pos/hp + resources summary
        # shape: squad*(5) + enemy*(3) + resources(3) = 3*5 + 3*3 + 3 = 27
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(27,), dtype=np.float32)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.world = World(self.cfg, seed=seed or self.seed_val)
        self.opponents = [SimplePlanner(tid) for tid in range(1, self.cfg.team_count)]
        obs = self._obs()
        return obs, {}

    def step(self, action):
        dt = 1.0 / self.cfg.fps
        act_dict = {}
        # actions for our squad (team 0)
        for idx, a in enumerate(action):
            act_dict[(0, idx)] = int(a)
        for opp in self.opponents:
            act_dict.update(opp.act(self.world))
        self.world.step(act_dict, dt)
        obs = self._obs()
        reward = self._reward()
        terminated = self.world.done
        truncated = False
        info = {"winner": self.world.winner}
        return obs, reward, terminated, truncated, info

    def _obs(self):
        t0_units = self.world.get_team_units(0)
        # pad to squad size
        while len(t0_units) < self.squad_size:
            t0_units.append(t0_units[-1])
        # pick nearest enemy aggregate
        enemies = [u for u in self.world.units if u.team_id != 0 and u.is_alive()]
        enemy_summary = []
        for i in range(3):
            if i < len(enemies):
                enemy_summary.extend(
                    [
                        enemies[i].pos[0] / self.cfg.width,
                        enemies[i].pos[1] / self.cfg.height,
                        enemies[i].hp / enemies[i].stats.max_hp,
                    ]
                )
            else:
                enemy_summary.extend([0.0, 0.0, 0.0])

        obs_vec = []
        for i in range(self.squad_size):
            u = t0_units[i]
            obs_vec.extend(
                [
                    u.pos[0] / self.cfg.width,
                    u.pos[1] / self.cfg.height,
                    u.hp / u.stats.max_hp,
                    float(u.has_jewel),
                    0.0,  # reserved slot for future perk/weapon level
                ]
            )
        res = self.world.teams[0].resources
        obs_vec.extend(
            [
                min(1.0, res.get("wood", 0) / 50.0),
                min(1.0, res.get("metal", 0) / 50.0),
                min(1.0, res.get("fuel", 0) / 30.0),
            ]
        )
        obs_vec.extend(enemy_summary)
        return np.array(obs_vec, dtype=np.float32)

    def _reward(self) -> float:
        # Reward shaping: slight bonus for resources, heavy for win/lose.
        team = self.world.teams[0]
        res_score = team.resources.get("wood", 0) * 0.01 + team.resources.get("metal", 0) * 0.02
        jewel_bonus = 0.2 if any(u.has_jewel for u in self.world.units if u.team_id == 0) else 0.0
        if self.world.done:
            if self.world.winner == 0:
                return 5.0 + res_score + jewel_bonus
            return -5.0 + res_score + jewel_bonus
        return res_score + jewel_bonus

    def render(self):
        return None

