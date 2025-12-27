import pygame

from worldwar_jewel.app.ui.widgets import Button, Checkbox, Dropdown
from worldwar_jewel.ai.planner import SimplePlanner
from worldwar_jewel.config import CLASS_PRESETS, TEAM_PROFILES, GameTuning
from worldwar_jewel.game.world import ActionCommand, World


class PlaySetupScreen:
    def __init__(self, surface, fonts):
        self.surface = surface
        self.fonts = fonts
        w, h = surface.get_size()
        cx = w // 2
        self.next_screen = None
        start_y = h // 3 - 20
        gap = 90
        self.team_dd = Dropdown((cx - 160, start_y, 320, 44), [p.name for p in TEAM_PROFILES[:3]], fonts["sub"])
        self.class_dd = Dropdown((cx - 160, start_y + gap, 320, 44), [c.name for c in CLASS_PRESETS.values()], fonts["sub"])
        self.difficulty_dd = Dropdown((cx - 160, start_y + gap * 2, 320, 44), ["Script", "IA Treinada", "Híbrida"], fonts["sub"])
        self.render_cb = Checkbox((cx - 160, start_y + gap * 3 + 10), "Renderizar partida", fonts["sub"], checked=True)

        self.start_btn = Button((cx - 140, start_y + gap * 3 + 60, 280, 56), "Iniciar Partida", fonts["btn"], self._start)
        self.back_btn = Button((20, h - 70, 160, 44), "Voltar", fonts["btn"], self._back, color=(80, 90, 110))

    def _start(self):
        self.next_screen = ("play_match", self.team_dd.selected, self.class_dd.selected, self.difficulty_dd.selected, self.render_cb.checked)

    def _back(self):
        self.next_screen = "menu"

    def handle_event(self, event):
        self.team_dd.handle_event(event)
        self.class_dd.handle_event(event)
        self.difficulty_dd.handle_event(event)
        self.render_cb.handle_event(event)
        self.start_btn.handle_event(event)
        self.back_btn.handle_event(event)

    def update(self, dt):
        pass

    def draw(self):
        surf = self.surface
        surf.fill((14, 18, 28))
        title = self.fonts["title"].render("Jogar", True, (240, 245, 255))
        surf.blit(title, (40, 32))
        label = self.fonts["sub"].render("Selecione time, classe do líder e dificuldade.", True, (150, 180, 200))
        surf.blit(label, (40, 70))

        surf.blit(self.fonts["sub"].render("Time", True, (210, 220, 230)), (self.team_dd.rect.x, self.team_dd.rect.y - 30))
        self.team_dd.draw(surf)

        surf.blit(self.fonts["sub"].render("Classe do Líder", True, (210, 220, 230)), (self.class_dd.rect.x, self.class_dd.rect.y - 30))
        self.class_dd.draw(surf)

        surf.blit(self.fonts["sub"].render("Dificuldade IA", True, (210, 220, 230)), (self.difficulty_dd.rect.x, self.difficulty_dd.rect.y - 30))
        self.difficulty_dd.draw(surf)

        self.render_cb.draw(surf)
        self.start_btn.draw(surf)
        self.back_btn.draw(surf)

        # Draw dropdown overlays last to keep them on top
        self.team_dd.draw_overlay(surf)
        self.class_dd.draw_overlay(surf)
        self.difficulty_dd.draw_overlay(surf)


class PlayMatchScreen:
    def __init__(self, surface, fonts, team_index: int, leader_class_index: int, difficulty_index: int, render: bool = True):
        self.surface = surface
        self.fonts = fonts
        self.cfg = GameTuning()
        # Screen size matches map tile size
        self.world = World(self.cfg, team_classes={team_index: [list(CLASS_PRESETS.keys())[leader_class_index]]})
        self.player_team = team_index
        self.difficulty_index = difficulty_index
        self.render_enabled = render
        self.next_screen = None
        self.planners = {tid: SimplePlanner(tid) for tid in range(self.cfg.team_count) if tid != self.player_team}
        self.clock = pygame.time.Clock()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.next_screen = "menu"

    def update(self, dt):
        actions = {}
        # AI actions
        for tid, planner in self.planners.items():
            actions.update(planner.act(self.world))
        # Player leader (unit 0) manual input
        leader_action = self._leader_action()
        actions[(self.player_team, 0)] = leader_action
        info = self.world.step(actions, dt)
        if info.get("done"):
            self.next_screen = "menu"

    def _leader_action(self) -> ActionCommand:
        keys = pygame.key.get_pressed()
        dx = dy = 0.0
        if keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_s]:
            dy += 1
        if keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_d]:
            dx += 1
        if dx != 0 or dy != 0:
            return ActionCommand(kind="move", target=(dx, dy))
        if keys[pygame.K_e]:
            return ActionCommand(kind="gather")
        if keys[pygame.K_f]:
            return ActionCommand(kind="interact")
        if keys[pygame.K_SPACE]:
            return ActionCommand(kind="attack")
        if keys[pygame.K_q]:
            return ActionCommand(kind="build_wall")
        if keys[pygame.K_r]:
            return ActionCommand(kind="build_turret")
        if keys[pygame.K_t]:
            return ActionCommand(kind="plant_explosive")
        if keys[pygame.K_h]:
            return ActionCommand(kind="repair")
        return ActionCommand(kind="noop")

    def draw(self):
        if not self.render_enabled:
            return
        surf = self.surface
        surf.fill((10, 12, 16))
        tile = self.cfg.tile

        # Grid background
        for x in range(self.cfg.width):
            pygame.draw.line(surf, (24, 28, 34), (x * tile, 0), (x * tile, self.cfg.height * tile))
        for y in range(self.cfg.height):
            pygame.draw.line(surf, (24, 28, 34), (0, y * tile), (self.cfg.width * tile, y * tile))

        # Walls
        for (wx, wy) in self.world.layout.walls:
            pygame.draw.rect(surf, (60, 70, 86), pygame.Rect(wx * tile, wy * tile, tile, tile), border_radius=4)

        # Resources
        for r in self.world.resources:
            if not r.alive:
                continue
            color = {"wood": (110, 170, 100), "metal": (170, 170, 190), "fuel": (240, 170, 80)}.get(r.rtype, (140, 140, 140))
            pygame.draw.circle(surf, color, (int(r.pos[0] * tile), int(r.pos[1] * tile)), 6)

        # Buildings
        for b in self.world.buildings:
            if not b.is_alive():
                continue
            color = TEAM_PROFILES[b.team_id % len(TEAM_PROFILES)].color
            rect = pygame.Rect(int((b.pos[0] - 0.5) * tile), int((b.pos[1] - 0.5) * tile), tile, tile)
            pygame.draw.rect(surf, color, rect, width=0, border_radius=6)
            hpw = int(rect.width * (b.hp / b.stats.max_hp))
            pygame.draw.rect(surf, (20, 20, 24), rect.inflate(0, 10).move(0, -6), border_radius=4)
            pygame.draw.rect(surf, (90, 200, 130), rect.inflate(0, 10).move(0, -6).clip(pygame.Rect(rect.x, rect.y - 8, hpw, rect.height)), border_radius=4)

        # Jewels
        for j in self.world.jewels:
            color = TEAM_PROFILES[j.home_team % len(TEAM_PROFILES)].color
            pygame.draw.circle(surf, (255, 235, 120), (int(j.pos[0] * tile), int(j.pos[1] * tile)), 9)
            pygame.draw.circle(surf, color, (int(j.pos[0] * tile), int(j.pos[1] * tile)), 11, 2)

        # Units
        for u in self.world.units:
            if not u.is_alive():
                continue
            color = TEAM_PROFILES[u.team_id % len(TEAM_PROFILES)].color
            x, y = int(u.pos[0] * tile), int(u.pos[1] * tile)
            pygame.draw.circle(surf, color, (x, y), 10)
            letter = u.cls_id[0].upper()
            txt = self.fonts["tiny"].render(letter, True, (12, 12, 14))
            surf.blit(txt, txt.get_rect(center=(x, y)))
            if u.has_jewel:
                pygame.draw.circle(surf, (255, 230, 120), (x, y - 14), 5)

        # HUD
        team = self.world.teams[self.player_team]
        hud = f"Recursos: W{team.resources.get('wood',0)} M{team.resources.get('metal',0)} F{team.resources.get('fuel',0)} | Pressione ESC para sair"
        hudsurf = self.fonts["sub"].render(hud, True, (230, 230, 240))
        surf.blit(hudsurf, (12, 8))
        if self.world.done:
            txt = f"Vitória do time {self.world.winner}"
            wtxt = self.fonts["title"].render(txt, True, (255, 255, 255))
            surf.blit(wtxt, wtxt.get_rect(center=(surf.get_width() // 2, 30)))
