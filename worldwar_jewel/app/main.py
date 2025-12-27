import pygame

from worldwar_jewel.app.ui.screens import MenuScreen, PlayMatchScreen, PlaySetupScreen, SettingsScreen, TrainingScreen
from worldwar_jewel.config import GameTuning


def build_fonts():
    return {
        "title": pygame.font.SysFont("bahnschrift", 42, bold=True),
        "sub": pygame.font.SysFont("bahnschrift", 22),
        "btn": pygame.font.SysFont("bahnschrift", 24, bold=True),
        "tiny": pygame.font.SysFont("bahnschrift", 14),
    }


def main():
    pygame.init()
    cfg = GameTuning()
    screen = pygame.display.set_mode((cfg.width * cfg.tile, cfg.height * cfg.tile))
    pygame.display.set_caption("World War Jewel (V2)")
    fonts = build_fonts()
    clock = pygame.time.Clock()

    current = MenuScreen(screen, fonts)
    running = True
    while running:
        dt = clock.tick(cfg.fps) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                current.handle_event(event)

        current.update(dt)
        current.draw()
        pygame.display.flip()

        nxt = current.next_screen
        if nxt:
            if nxt == "quit":
                running = False
            elif nxt == "menu":
                current = MenuScreen(screen, fonts)
            elif nxt == "play":
                current = PlaySetupScreen(screen, fonts)
            elif nxt == "train":
                current = TrainingScreen(screen, fonts)
            elif nxt == "settings":
                current = SettingsScreen(screen, fonts)
            elif isinstance(nxt, tuple) and nxt[0] == "play_match":
                _, team_idx, cls_idx, diff_idx, render = nxt
                current = PlayMatchScreen(screen, fonts, team_idx, cls_idx, diff_idx, render)
            current.next_screen = None

    pygame.quit()


if __name__ == "__main__":
    main()

