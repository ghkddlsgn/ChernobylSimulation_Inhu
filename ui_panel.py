"""
UI panels and rendering for the application.
"""

import pygame
from config import ColorPalette


class UIPanel:
    """A UI panel with a title and border."""

    def __init__(self, rect, title, font_title, font_regular):
        """Initialize a UI panel.

        Args:
            rect: pygame.Rect defining the panel's position and size.
            title: Title text for the panel.
            font_title: Font for the title.
            font_regular: Font for regular text.
        """
        self.rect = rect
        self.title = title
        self.font_title = font_title
        self.font_regular = font_regular

    def draw(self, surf, show_placeholder=False):
        """Draw the panel on the given surface.

        Args:
            surf: Pygame surface to draw on.
            show_placeholder: If True, show a placeholder message.
        """
        pygame.draw.rect(surf, ColorPalette.PANEL_BG, self.rect, border_radius=10)
        pygame.draw.rect(surf, ColorPalette.PANEL_BORDER, self.rect, width=1, border_radius=10)

        title_surf = self.font_title.render(self.title, True, ColorPalette.TEXT)
        surf.blit(title_surf, (self.rect.x + 14, self.rect.y + 10))

        pygame.draw.line(
            surf,
            ColorPalette.PANEL_BORDER,
            (self.rect.x + 12, self.rect.y + 38),
            (self.rect.right - 12, self.rect.y + 38),
        )

        if show_placeholder:
            text = self.font_regular.render("(placeholder)", True, ColorPalette.MUTED)
            text_rect = text.get_rect(center=self.rect.center)
            surf.blit(text, text_rect)


class Slider:
    """A horizontal slider returning a normalized value in [0, 1]."""

    def __init__(self, rect, value=0.5, label="", font=None, show_value=True):
        """Initialize a slider.

        Args:
            rect: pygame.Rect bounding box (label sits to the left/top).
            value: Initial normalized value (0..1).
            label: Optional text label.
            font: Font for the label.
            show_value: Whether to render the value as a percentage.
        """
        self.rect = pygame.Rect(rect)
        self.value = max(0.0, min(1.0, value))
        self.label = label
        self.font = font
        self.show_value = show_value
        self.dragging = False

    @property
    def _track_rect(self):
        """Bounding rect of the draggable track portion."""
        return pygame.Rect(self.rect.x, self.rect.centery - 3, self.rect.w, 6)

    def _knob_x(self):
        """Current knob center x in pixels."""
        return int(self.rect.x + self.value * self.rect.w)

    def _value_from_x(self, x):
        """Convert an absolute x to a clamped normalized value."""
        if self.rect.w <= 0:
            return self.value
        return max(0.0, min(1.0, (x - self.rect.x) / self.rect.w))

    def handle_event(self, event):
        """Process a pygame event. Returns True if the value changed."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            hit = self.rect.inflate(12, 16).collidepoint(event.pos)
            if hit:
                self.dragging = True
                new_val = self._value_from_x(event.pos[0])
                changed = new_val != self.value
                self.value = new_val
                return changed
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            new_val = self._value_from_x(event.pos[0])
            changed = new_val != self.value
            self.value = new_val
            return changed
        return False

    def draw(self, surf):
        """Draw the slider and its label."""
        if self.label and self.font:
            label_surf = self.font.render(self.label, True, ColorPalette.TEXT)
            surf.blit(label_surf, (self.rect.x, self.rect.y - 17))
            if self.show_value:
                pct = f"{int(round(self.value * 100))}%"
                val_surf = self.font.render(pct, True, ColorPalette.MUTED)
                surf.blit(val_surf, (self.rect.right - val_surf.get_width(),
                                     self.rect.y - 17))

        track = self._track_rect
        pygame.draw.rect(surf, ColorPalette.SLIDER_TRACK, track, border_radius=3)
        knob_x = self._knob_x()
        fill = pygame.Rect(track.x, track.y, max(0, knob_x - track.x), track.h)
        pygame.draw.rect(surf, ColorPalette.SLIDER_FILL, fill, border_radius=3)
        pygame.draw.circle(surf, ColorPalette.SLIDER_KNOB,
                           (knob_x, track.centery), 7)


class Button:
    """A simple clickable button."""

    def __init__(self, rect, label, font):
        """Initialize a button.

        Args:
            rect: pygame.Rect bounding box.
            label: Button text.
            font: Font for the label.
        """
        self.rect = pygame.Rect(rect)
        self.label = label
        self.font = font
        self._hover = False

    def handle_event(self, event):
        """Process a pygame event. Returns True if the button was clicked."""
        if event.type == pygame.MOUSEMOTION:
            self._hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def set_label(self, label):
        """Update the button's label text."""
        self.label = label

    def draw(self, surf):
        """Draw the button."""
        bg = ColorPalette.BUTTON_BG_HOVER if self._hover else ColorPalette.BUTTON_BG
        pygame.draw.rect(surf, bg, self.rect, border_radius=6)
        pygame.draw.rect(surf, ColorPalette.BUTTON_BORDER, self.rect, width=1,
                         border_radius=6)
        text = self.font.render(self.label, True, ColorPalette.TEXT)
        surf.blit(text, text.get_rect(center=self.rect.center))
