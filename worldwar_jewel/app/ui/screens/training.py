import multiprocessing as mp
import pygame

from worldwar_jewel.app.ui.widgets import Button, Checkbox, Dropdown, Slider
from worldwar_jewel.ai.train_worker import TrainConfig, train_worker
from worldwar_jewel.ai.planner import SimplePlanner
from worldwar_jewel.config import GameTuning, TEAM_PROFILES
from worldwar_jewel.game.world import World


class TrainingScreen:
    def __init__(self, surface, fonts):
        self.surface = surface
        self.fonts = fonts
        self.next_screen = None
        self.cfg = GameTuning()
        w, h = surface.get_size()
        cx = w // 2
        self.mode_dd = Dropdown((cx - 180, h // 3, 360, 44), ["Self-play", "IA vs Script", "IA vs Replay (futuro)"], fonts["sub"])
        self.time_slider = Slider((cx - 180, h // 3 + 70, 360, 14), 1, 30, 5, fonts["sub"], label="Tempo (min)")
        self.render_cb = Checkbox((cx - 180, h // 3 + 110), "Treinar com render", fonts["sub"], checked=False)
        self.fast_cb = Checkbox((cx + 40, h // 3 + 110), "Treino rapido", fonts["sub"], checked=True)
        self.start_btn = Button((cx - 120, h // 3 + 170, 240, 50), "Comecar", fonts["btn"], self._start)
        self.stop_btn = Button((cx - 120, h // 3 + 230, 240, 40), "Parar e salvar", fonts["btn"], self._stop, color=(200, 120, 70))
        self.stop_full_btn = Button((surface.get_width() - 180, 20, 160, 40), "Parar", fonts["btn"], self._stop, color=(200, 120, 70))
        self.back_btn = Button((20, h - 70, 160, 44), "Voltar", fonts["btn"], self._back, color=(80, 90, 110))

        self.worker: mp.Process | None = None
        self.queue: mp.Queue | None = None
        self.progress_msg = ""
        self.winrate = {}
        self.render_world: World | None = None
        self.render_planners = []
        self.rendering = False

    def _start(self):
        if self.worker and self.worker.is_alive():
            return
        if self.render_cb.checked:
            # Render mode: run self-play locally with planners and show on screen
            self.fast_cb.checked = False
            self.render_world = World(self.cfg)
            self.render_planners = [SimplePlanner(tid) for tid in range(self.render_world.cfg.team_count)]
            self.rendering = True
            self.progress_msg = "Treinando (render)..."
            self.winrate = {}
            return
        steps = int(self.time_slider.value * 60)  # roughly seconds of episodes
        cfg = TrainConfig(steps=steps, render=self.render_cb.checked, opponents="selfplay")
        self.queue = mp.Queue()
        self.worker = mp.Process(target=train_worker, args=(cfg, self.queue))
        self.worker.start()
        self.progress_msg = "Treinando..."

    def _stop(self):
        if self.worker and self.worker.is_alive():
            self.worker.terminate()
        if self.rendering:
            self.rendering = False
            self.render_world = None
        self.progress_msg = "Treino parado."

    def _back(self):
        self.next_screen = "menu"

    def handle_event(self, event):
        if self.rendering:
            self.stop_full_btn.handle_event(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._stop()
        else:
            self.mode_dd.handle_event(event)
            self.time_slider.handle_event(event)
            self.render_cb.handle_event(event)
            self.fast_cb.handle_event(event)
            self.start_btn.handle_event(event)
            self.stop_btn.handle_event(event)
            self.back_btn.handle_event(event)

    def update(self, dt):
        # Rendered training loop (local self-play with planners)
        if self.rendering and self.render_world:
            actions = {}
            for planner in self.render_planners:
                actions.update(planner.act(self.render_world))
            info = self.render_world.step(actions, dt)
            if info.get("done"):
                winner = info.get("winner")
                if winner is not None:
                    self.winrate[winner] = self.winrate.get(winner, 0) + 1
                # restart new episode
                self.render_world = World(self.cfg)
                self.render_planners = [SimplePlanner(tid) for tid in range(self.render_world.cfg.team_count)]
            return

        if self.queue:
            try:
                msg = self.queue.get_nowait()
                status = msg.get("status")
                if status == "progress":
                    self.winrate = msg.get("wins", {})
                    self.progress_msg = f"Episodio {msg.get('episode', 0)}"
                elif status == "finished":
                    self.winrate = msg.get("wins", {})
                    self.progress_msg = "Treino completo."
                    if self.worker:
                        self.worker.join(timeout=0.1)
                elif status == "started":
                    self.progress_msg = "Treinando..."
            except Exception:
                pass

    def draw(self):
        surf = self.surface
        if self.rendering and self.render_world:
            surf.fill((10, 12, 16))
            self._draw_full_world(surf, tile=self.render_world.cfg.tile)
            self.stop_full_btn.draw(surf)
            # HUD info
            msg = self.progress_msg or "Treinando (render)..."
            hud = self.fonts["sub"].render(msg, True, (230, 230, 240))
            surf.blit(hud, (12, 12))
            if self.winrate:
                wr_txt = ", ".join([f"{k}: {v}" for k, v in self.winrate.items()])
                wr = self.fonts["sub"].render(f"Winrate: {wr_txt}", True, (200, 220, 160))
                surf.blit(wr, (12, 40))
            return

        surf.fill((16, 18, 24))
        title = self.fonts["title"].render("Treinar IA", True, (240, 245, 255))
        surf.blit(title, (40, 32))
        subtitle = self.fonts["sub"].render("Self-play, IA vs Script ou replay. Sem terminal, clique e acompanhe.", True, (150, 180, 200))
        surf.blit(subtitle, (40, 70))

        surf.blit(self.fonts["sub"].render("Modo de treino", True, (210, 220, 230)), (self.mode_dd.rect.x, self.mode_dd.rect.y - 26))
        self.mode_dd.draw(surf)
        self.time_slider.draw(surf)
        self.render_cb.draw(surf)
        self.fast_cb.draw(surf)

        self.start_btn.draw(surf)
        self.stop_btn.draw(surf)
        self.back_btn.draw(surf)

        # Progress
        prog = self.fonts["sub"].render(self.progress_msg, True, (230, 230, 240))
        surf.blit(prog, (40, 140))
        if self.winrate:
            wr_txt = ", ".join([f"{k}: {v if self.rendering else v*100:.0f}{'' if self.rendering else '%'}" for k, v in self.winrate.items()])
            wr = self.fonts["sub"].render(f"Winrate: {wr_txt}", True, (200, 220, 160))
            surf.blit(wr, (40, 170))

        # dropdown overlay on top
        self.mode_dd.draw_overlay(surf)

    def _draw_full_world(self, surf, tile=20):
        w = self.render_world
        if w is None:
            return
        for x in range(w.cfg.width):
            pygame.draw.line(surf, (24, 28, 34), (x * tile, 0), (x * tile, w.cfg.height * tile))
        for y in range(w.cfg.height):
            pygame.draw.line(surf, (24, 28, 34), (0, y * tile), (w.cfg.width * tile, y * tile))

        for (wx, wy) in w.layout.walls:
            pygame.draw.rect(surf, (60, 70, 86), pygame.Rect(wx * tile, wy * tile, tile, tile), border_radius=4)

        for r in w.resources:
            if not r.alive:
                continue
            color = {"wood": (110, 170, 100), "metal": (170, 170, 190), "fuel": (240, 170, 80)}.get(r.rtype, (140, 140, 140))
            pygame.draw.circle(surf, color, (int(r.pos[0] * tile), int(r.pos[1] * tile)), 6)

        for b in w.buildings:
            if not b.is_alive():
                continue
            color = TEAM_PROFILES[b.team_id % len(TEAM_PROFILES)].color
            rect = pygame.Rect(int((b.pos[0] - 0.5) * tile), int((b.pos[1] - 0.5) * tile), tile, tile)
            pygame.draw.rect(surf, color, rect, width=0, border_radius=6)

        for j in w.jewels:
            color = TEAM_PROFILES[j.home_team % len(TEAM_PROFILES)].color
            pygame.draw.circle(surf, (255, 235, 120), (int(j.pos[0] * tile), int(j.pos[1] * tile)), 9)
            pygame.draw.circle(surf, color, (int(j.pos[0] * tile), int(j.pos[1] * tile)), 11, 2)

        for u in w.units:
            if not u.is_alive():
                continue
            color = TEAM_PROFILES[u.team_id % len(TEAM_PROFILES)].color
            x, y = int(u.pos[0] * tile), int(u.pos[1] * tile)
            pygame.draw.circle(surf, color, (x, y), 10)
            letter = u.cls_id[0].upper()
            txt_font = self.fonts["tiny"] if "tiny" in self.fonts else self.fonts["sub"]
            txt = txt_font.render(letter, True, (12, 12, 14))
            surf.blit(txt, txt.get_rect(center=(x, y)))
            if u.has_jewel:
                pygame.draw.circle(surf, (255, 230, 120), (x, y - 14), 5)





