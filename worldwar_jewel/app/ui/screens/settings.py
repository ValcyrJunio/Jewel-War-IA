import pygame

from worldwar_jewel.app.ui.widgets import Button, Checkbox


class SettingsScreen:
    def __init__(self, surface, fonts):
        self.surface = surface
        self.fonts = fonts
        self.next_screen = None
        w, h = surface.get_size()
        self.full_cb = Checkbox((50, 120), "Tela cheia", fonts["sub"], checked=False)
        self.sfx_cb = Checkbox((50, 160), "Efeitos sonoros", fonts["sub"], checked=True)
        self.back_btn = Button((20, h - 70, 160, 44), "Voltar", fonts["btn"], self._back, color=(80, 90, 110))

    def _back(self):
        self.next_screen = "menu"

    def handle_event(self, event):
        self.full_cb.handle_event(event)
        self.sfx_cb.handle_event(event)
        self.back_btn.handle_event(event)

    def update(self, dt):
        pass

    def draw(self):
        surf = self.surface
        surf.fill((18, 20, 26))
        title = self.fonts["title"].render("Configurações", True, (240, 245, 255))
        surf.blit(title, (40, 32))
        for cb in [self.full_cb, self.sfx_cb]:
            cb.draw(surf)
        self.back_btn.draw(surf)

