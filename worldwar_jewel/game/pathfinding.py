import heapq
from typing import Dict, List, Set, Tuple

GridPos = Tuple[int, int]


def heuristic(a: GridPos, b: GridPos) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def neighbors(pos: GridPos) -> List[GridPos]:
    x, y = pos
    return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]


def a_star(start: GridPos, goal: GridPos, blocked: Set[GridPos], bounds: Tuple[int, int]) -> List[GridPos]:
    """Simple grid A*; returns path including goal (excludes start)."""
    width, height = bounds
    open_set: List[Tuple[float, GridPos]] = []
    heapq.heappush(open_set, (0, start))
    came_from: Dict[GridPos, GridPos] = {}
    g_score: Dict[GridPos, float] = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            break
        for nb in neighbors(current):
            if not (0 <= nb[0] < width and 0 <= nb[1] < height):
                continue
            if nb in blocked:
                continue
            tentative = g_score[current] + 1
            if tentative < g_score.get(nb, 1e9):
                came_from[nb] = current
                g_score[nb] = tentative
                f = tentative + heuristic(nb, goal)
                heapq.heappush(open_set, (f, nb))

    if goal not in came_from and goal != start:
        return []

    path: List[GridPos] = []
    cur = goal
    while cur != start:
        path.append(cur)
        cur = came_from.get(cur, start)
        if cur == start:
            break
    path.reverse()
    return path

