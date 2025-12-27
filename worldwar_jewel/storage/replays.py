"""
Replay serialization placeholder.
"""

from typing import List, Tuple

Frame = Tuple[int, dict]


def save_replay(path: str, frames: List[Frame]):
    with open(path, "w", encoding="utf-8") as f:
        for t, data in frames:
            f.write(f"{t}|{data}\n")

