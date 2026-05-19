"""
Main application for the RBMK Reactor Simulation.

Run:  python main.py
"""

import sys
import pygame
from config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, ColorPalette
from reactor import Reactor
from ui_panel import UIPanel


class App:
    """Main application class."""

    def __init__(self):
        """Initialize the application."""
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("RBMK Reactor Simulation - Prototype")
        self.clock = pygame.time.Clock()

        # Setup fonts
        self.font_title = pygame.font.SysFont("Arial", 20, bold=True)
        self.font = pygame.font.SysFont("Arial", 15)
        self.font_small = pygame.font.SysFont("Arial", 13)

        # Setup layout
        self._setup_layout()

        self.running = True

    def _setup_layout(self):
        """Configure panel layout and reactor."""
        m = 15

        # Reactor panel (left side)
        self.reactor_panel = UIPanel(
            pygame.Rect(m, m, 920, WINDOW_HEIGHT - 2 * m),
            "RBMK Reactor Core",
            self.font_title,
            self.font,
        )

        # Right side panels
        right_x = self.reactor_panel.rect.right + m
        right_w = WINDOW_WIDTH - right_x - m
        plots_h = 480

        # Plots panel (top-right)
        self.plots_panel = UIPanel(
            pygame.Rect(right_x, m, right_w, plots_h),
            "Plots",
            self.font_title,
            self.font,
        )

        # Control panel (bottom-right)
        self.ctrl_panel = UIPanel(
            pygame.Rect(
                right_x,
                m + plots_h + m,
                right_w,
                WINDOW_HEIGHT - 2 * m - plots_h - m,
            ),
            "Control Panel",
            self.font_title,
            self.font,
        )

        # Create reactor inside its panel
        rx = self.reactor_panel.rect.x + 10
        ry = self.reactor_panel.rect.y + 45
        rw = self.reactor_panel.rect.w - 20
        rh = self.reactor_panel.rect.h - 55
        self.reactor = Reactor(rx, ry, rw, rh, num_rods=10)

    def _handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    def _draw(self):
        """Draw the entire scene."""
        self.screen.fill(ColorPalette.APP_BG)

        # Draw panels
        self.reactor_panel.draw(self.screen, show_placeholder=False)
        self.plots_panel.draw(self.screen, show_placeholder=True)
        self.ctrl_panel.draw(self.screen, show_placeholder=True)

        # Draw reactor
        self.reactor.draw(self.screen, self.font_small)

    def run(self):
        """Main application loop."""
        while self.running:
            self._handle_events()
            self._draw()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


def main():
    """Entry point for the application."""
    app = App()
    app.run()


if __name__ == "__main__":
    main()
