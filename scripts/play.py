import argparse
import time
import numpy as np

import pygame

from jewel_war.config import GameConfig
from jewel_war.core import JewelWar
from jewel_war.bots import ScriptBot

try:
    from stable_baselines3 import PPO
except Exception:
    PPO = None


def load_ai(path: str):
    if PPO is None:
        raise RuntimeError("stable-baselines3 not installed. Install requirements.txt")
    return PPO.load(path)


def draw_world(screen, cfg: GameConfig, game: JewelWar, font):
    tile = cfg.tile
    screen.fill((18, 18, 22))

    # draw grid background faint
    for x in range(cfg.width):
        pygame.draw.line(screen, (25, 25, 30), (x*tile, 0), (x*tile, cfg.height*tile))
    for y in range(cfg.height):
        pygame.draw.line(screen, (25, 25, 30), (0, y*tile), (cfg.width*tile, y*tile))

    # walls
    for (wx, wy) in game.walls:
        pygame.draw.rect(screen, (60, 60, 70), pygame.Rect(wx*tile, wy*tile, tile, tile), border_radius=4)

    # resources
    for r in game.resources:
        if r.alive:
            pygame.draw.circle(screen, (90, 180, 90), (int(r.pos[0]*tile), int(r.pos[1]*tile)), 6)

    # bases
    for i, b in enumerate(game.bases):
        color = (70, 120, 255) if i == 0 else (255, 90, 90)
        pygame.draw.rect(screen, color, pygame.Rect(int((b[0]-0.8)*tile), int((b[1]-0.8)*tile), int(1.6*tile), int(1.6*tile)), 2, border_radius=6)

    # jewels
    for j in game.jewels:
        if j.home_team == 0:
            c = (120, 170, 255)
        else:
            c = (255, 140, 140)
        pygame.draw.circle(screen, c, (int(j.pos[0]*tile), int(j.pos[1]*tile)), 10)
        pygame.draw.circle(screen, (10,10,10), (int(j.pos[0]*tile), int(j.pos[1]*tile)), 10, 2)

    # agents
    for team, a in enumerate(game.agents):
        color = (70, 120, 255) if team == 0 else (255, 90, 90)
        x, y = int(a.pos[0]*tile), int(a.pos[1]*tile)
        pygame.draw.circle(screen, color, (x, y), 12)
        if a.has_jewel:
            pygame.draw.circle(screen, (255, 230, 120), (x, y-18), 6)

        # hp bar
        w = 30
        hpw = int(w * (a.hp / cfg.max_hp))
        pygame.draw.rect(screen, (40,40,40), pygame.Rect(x-w//2, y+16, w, 6), border_radius=3)
        pygame.draw.rect(screen, (80,220,120), pygame.Rect(x-w//2, y+16, hpw, 6), border_radius=3)

    # HUD
    a0, a1 = game.agents[0], game.agents[1]
    txt = f"Blue: hp={a0.hp} res={a0.resources} w={a0.weapon_level} jewel={int(a0.has_jewel)}   |   Red: hp={a1.hp} res={a1.resources} w={a1.weapon_level} jewel={int(a1.has_jewel)}"
    surf = font.render(txt, True, (220,220,230))
    screen.blit(surf, (10, 10))

    if game.done:
        wtxt = "BLUE WINS!" if game.winner == 0 else "RED WINS!"
        surf2 = font.render(wtxt, True, (255,255,255))
        screen.blit(surf2, (10, 40))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=str, default="", help="Path to PPO model zip (trained). If empty, uses scripted bot for red.")
    ap.add_argument("--human", action="store_true", help="Control Blue with WASD. If not set, Blue also uses AI/script.")
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    cfg = GameConfig()
    pygame.init()
    screen = pygame.display.set_mode((cfg.width*cfg.tile, cfg.height*cfg.tile))
    pygame.display.set_caption("Jewel War (Capture the Jewel)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18)

    game = JewelWar(cfg, seed=args.seed)

    blue_ai = None
    if args.model:
        blue_ai = load_ai(args.model)

    red_bot = ScriptBot(aggressiveness=0.75)

    running = True
    while running:
        dt = 1.0 / cfg.fps
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        # Decide blue action
        blue_action = 0
        if args.human:
            if keys[pygame.K_w]:
                blue_action = 1
            elif keys[pygame.K_s]:
                blue_action = 2
            elif keys[pygame.K_a]:
                blue_action = 3
            elif keys[pygame.K_d]:
                blue_action = 4
            elif keys[pygame.K_e]:
                blue_action = 5  # gather
            elif keys[pygame.K_c]:
                blue_action = 6  # craft
            elif keys[pygame.K_SPACE]:
                blue_action = 7  # attack
            elif keys[pygame.K_f]:
                blue_action = 8  # interact (steal/deliver)
            else:
                blue_action = 0
        else:
            if blue_ai is not None:
                obs = game.get_obs(0)
                blue_action, _ = blue_ai.predict(obs, deterministic=True)
                blue_action = int(blue_action)
            else:
                # scripted blue if no model and not human
                blue_action = ScriptBot(aggressiveness=0.65).act(game, 0)

        red_action = red_bot.act(game, 1)

        game.step(blue_action, red_action, dt)

        draw_world(screen, cfg, game, font)
        pygame.display.flip()
        clock.tick(cfg.fps)

    pygame.quit()

if __name__ == "__main__":
    main()
