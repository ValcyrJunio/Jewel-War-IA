"""
Multiprocess training worker placeholder.
The UI can start this worker to run headless training; currently it just loops self-play episodes.
"""

import multiprocessing as mp
from dataclasses import dataclass
from typing import Callable, Dict

from worldwar_jewel.ai.selfplay import rollout_once


@dataclass
class TrainConfig:
    steps: int = 1000
    render: bool = False
    opponents: str = "selfplay"


def train_loop(cfg: TrainConfig, progress_cb: Callable[[Dict], None] | None = None):
    wins: Dict[int, int] = {}
    for i in range(cfg.steps):
        winner, _ = rollout_once()
        if winner is not None:
            wins[winner] = wins.get(winner, 0) + 1
        if progress_cb and i % 10 == 0:
            total = sum(wins.values()) or 1
            progress_cb(
                {
                    "episode": i,
                    "wins": {k: v / total for k, v in wins.items()},
                }
            )


def train_worker(cfg: TrainConfig, queue: mp.Queue):
    def push(msg: Dict):
        try:
            queue.put(msg, timeout=1)
        except Exception:
            pass

    push({"status": "started"})
    wins: Dict[int, int] = {}
    for i in range(cfg.steps):
        winner, _ = rollout_once()
        if winner is not None:
            wins[winner] = wins.get(winner, 0) + 1
        if i % 10 == 0:
            total = sum(wins.values()) or 1
            push({"status": "progress", "episode": i, "wins": {k: v / total for k, v in wins.items()}})
    push({"status": "finished", "wins": wins})

