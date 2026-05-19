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
