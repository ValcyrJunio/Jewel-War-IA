import pygame


class Button:
    def __init__(self, rect, text, font, callback, color=(30, 140, 200), text_color=(18, 18, 24)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.callback = callback
        self.color = color
        self.text_color = text_color
        self.hover = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, surf):
        c = tuple(min(255, int(v * (1.08 if self.hover else 1.0))) for v in self.color)
        pygame.draw.rect(surf, c, self.rect, border_radius=8)
        txt = self.font.render(self.text, True, self.text_color)
        surf.blit(txt, txt.get_rect(center=self.rect.center))


class Checkbox:
    def __init__(self, pos, label, font, checked=False):
        self.pos = pos
        self.label = label
        self.font = font
        self.checked = checked
        self.box = pygame.Rect(pos[0], pos[1], 20, 20)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.box.collidepoint(event.pos):
                self.checked = not self.checked

    def draw(self, surf):
        pygame.draw.rect(surf, (60, 70, 80), self.box, border_radius=4, width=2)
        if self.checked:
            pygame.draw.rect(surf, (70, 200, 120), self.box.inflate(-6, -6), border_radius=3)
        txt = self.font.render(self.label, True, (230, 234, 240))
        surf.blit(txt, (self.box.right + 10, self.box.top - 2))


class Dropdown:
    def __init__(self, rect, options, font, selected_index=0):
        self.rect = pygame.Rect(rect)
        self.options = options
        self.font = font
        self.selected = selected_index
        self.expanded = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.expanded = not self.expanded
            elif self.expanded:
                # Check option clicks
                for i, opt in enumerate(self.options):
                    opt_rect = self.rect.move(0, (i + 1) * self.rect.height)
                    if opt_rect.collidepoint(event.pos):
                        self.selected = i
                        self.expanded = False
                        break
                else:
                    self.expanded = False

    def draw(self, surf):
        pygame.draw.rect(surf, (50, 60, 70), self.rect, border_radius=6)
        txt = self.font.render(self.options[self.selected], True, (230, 230, 230))
        surf.blit(txt, (self.rect.x + 10, self.rect.y + 8))
        pygame.draw.polygon(
            surf,
            (220, 220, 220),
            [
                (self.rect.right - 16, self.rect.y + 12),
                (self.rect.right - 6, self.rect.y + 12),
                (self.rect.right - 11, self.rect.y + 20),
            ],
        )

    def draw_overlay(self, surf):
        """Draw expanded options over everything else."""
        if not self.expanded:
            return
        for i, opt in enumerate(self.options):
            opt_rect = self.rect.move(0, (i + 1) * self.rect.height)
            pygame.draw.rect(surf, (40, 44, 52), opt_rect, border_radius=4)
            pygame.draw.rect(surf, (30, 34, 40), opt_rect, width=2, border_radius=4)
            t = self.font.render(opt, True, (200, 200, 200))
            surf.blit(t, (opt_rect.x + 10, opt_rect.y + 8))


class Slider:
    def __init__(self, rect, min_val, max_val, value, font, label=""):
        self.rect = pygame.Rect(rect)
        self.min = min_val
        self.max = max_val
        self.value = value
        self.dragging = False
        self.font = font
        self.label = label

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self._update_value(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_value(event.pos[0])

    def _update_value(self, mouse_x):
        t = (mouse_x - self.rect.x) / self.rect.width
        t = max(0.0, min(1.0, t))
        self.value = self.min + t * (self.max - self.min)

    def draw(self, surf):
        pygame.draw.rect(surf, (60, 70, 80), self.rect, border_radius=4)
        t = (self.value - self.min) / (self.max - self.min)
        knob_x = self.rect.x + int(t * self.rect.width)
        pygame.draw.circle(surf, (90, 190, 140), (knob_x, self.rect.centery), 10)
        lbl = f"{self.label}: {self.value:.1f}" if self.label else f"{self.value:.1f}"
        txt = self.font.render(lbl, True, (230, 230, 230))
        surf.blit(txt, (self.rect.x, self.rect.y - 22))
