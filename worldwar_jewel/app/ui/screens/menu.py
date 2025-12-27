import pygame

from worldwar_jewel.app.ui.widgets import Button


class MenuScreen:
    def __init__(self, surface, fonts):
        self.surface = surface
        self.fonts = fonts
        w, h = surface.get_size()
        cx = w // 2
        start_y = h // 3
        self.buttons = [
            Button((cx - 140, start_y, 280, 56), "Jogar", fonts["btn"], lambda: self._set("play")),
            Button((cx - 140, start_y + 70, 280, 56), "Treinar IA", fonts["btn"], lambda: self._set("train")),
            Button((cx - 140, start_y + 140, 280, 56), "Configurações", fonts["btn"], lambda: self._set("settings")),
            Button((cx - 140, start_y + 210, 280, 56), "Sair", fonts["btn"], lambda: self._set("quit")),
        ]
        self.next_screen = None

    def _set(self, name):
        self.next_screen = name

    def handle_event(self, event):
        for b in self.buttons:
            b.handle_event(event)

    def update(self, dt):
        pass

    def draw(self):
        surf = self.surface
        surf.fill((12, 16, 26))
        title = self.fonts["title"].render("World War Jewel", True, (240, 245, 255))
        surf.blit(title, title.get_rect(center=(surf.get_width() // 2, surf.get_height() // 4)))
        subtitle = self.fonts["sub"].render("Capture-the-Jewel | 3 Fações | 3 unidades por squad", True, (120, 180, 200))
        surf.blit(subtitle, subtitle.get_rect(center=(surf.get_width() // 2, surf.get_height() // 4 + 36)))
        for b in self.buttons:
            b.draw(surf)

