import numpy as np
import gymnasium as gym
from gymnasium import spaces

from .config import GameConfig
from .core import JewelWar
from .bots import ScriptBot

ACTION_MEANINGS = {
    0: "NOOP",
    1: "UP",
    2: "DOWN",
    3: "LEFT",
    4: "RIGHT",
    5: "GATHER",
    6: "CRAFT",
    7: "ATTACK",
    8: "INTERACT",
}

class JewelWarEnv(gym.Env):
    """Single-agent RL env: agent controls team 0, opponent is scripted (team 1)."""
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 30}

    def __init__(self, cfg: GameConfig | None = None, render_mode: str | None = None, opponent_aggr: float = 0.65, seed: int | None = None):
        super().__init__()
        self.cfg = cfg or GameConfig()
        self.render_mode = render_mode
        self.game = JewelWar(self.cfg, seed=seed)
        self.opponent = ScriptBot(aggressiveness=opponent_aggr)

        obs0 = self.game.get_obs(0)
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=obs0.shape, dtype=np.float32)
        self.action_space = spaces.Discrete(9)

        self._episode_steps = 0

        # Reward shaping weights (tuned for learning fast)
        self.r_gather = 0.08
        self.r_craft = 0.12
        self.r_damage = 0.004
        self.r_take_damage = -0.003
        self.r_pick_jewel = 0.6
        self.r_hold_jewel = 0.002
        self.r_win = 3.0
        self.r_lose = -3.0
        self.r_idle = -0.0005

        self._prev_resources = 0
        self._prev_weapon = 0
        self._prev_enemy_hp = self.cfg.max_hp
        self._prev_hp = self.cfg.max_hp
        self._prev_has_jewel = False

        self._renderer = None

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self.game = JewelWar(self.cfg, seed=seed)
        else:
            self.game = JewelWar(self.cfg, seed=None)
        self._episode_steps = 0

        a0 = self.game.agents[0]
        self._prev_resources = a0.resources
        self._prev_weapon = a0.weapon_level
        self._prev_enemy_hp = self.game.agents[1].hp
        self._prev_hp = a0.hp
        self._prev_has_jewel = a0.has_jewel

        obs = self.game.get_obs(0)
        info = {}
        return obs, info

    def step(self, action):
        self._episode_steps += 1
        # Opponent acts
        opp_action = self.opponent.act(self.game, 1)

        # Apply core step
        dt = 1.0 / self.cfg.fps
        self.game.step(int(action), int(opp_action), dt=dt)

        obs = self.game.get_obs(0)

        # Rewards
        reward = 0.0
        a0 = self.game.agents[0]
        a1 = self.game.agents[1]

        # Gather/craft progress
        if a0.resources > self._prev_resources:
            reward += self.r_gather * (a0.resources - self._prev_resources)
        if a0.weapon_level > self._prev_weapon:
            reward += self.r_craft * (a0.weapon_level - self._prev_weapon)

        # Combat shaping
        if a1.hp < self._prev_enemy_hp:
            reward += self.r_damage * (self._prev_enemy_hp - a1.hp)
        if a0.hp < self._prev_hp:
            reward += self.r_take_damage * (self._prev_hp - a0.hp)

        # Jewel shaping
        if (not self._prev_has_jewel) and a0.has_jewel:
            reward += self.r_pick_jewel
        if a0.has_jewel:
            reward += self.r_hold_jewel

        # Small idle penalty
        if int(action) == 0:
            reward += self.r_idle

        terminated = bool(self.game.done)
        truncated = False

        if terminated:
            if self.game.winner == 0:
                reward += self.r_win
            else:
                reward += self.r_lose

        self._prev_resources = a0.resources
        self._prev_weapon = a0.weapon_level
        self._prev_enemy_hp = a1.hp
        self._prev_hp = a0.hp
        self._prev_has_jewel = a0.has_jewel

        info = {"winner": self.game.winner}
        return obs, float(reward), terminated, truncated, info

    def render(self):
        # Rendering is handled by the separate pygame runner in scripts/.
        return None

    def close(self):
        self._renderer = None
