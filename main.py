"""
Main application for the RBMK Reactor Simulation.

Run:  python main.py

Controls:
    * Drag the sliders in the Control Panel to insert/withdraw control rods.
      The master slider moves every rod together; the numbered sliders move a
      single rod each.
    * Start / Pause button (or SPACE) toggles the simulation.
    * Reset button (or R) reloads the fuel and clears all neutrons.

Physics comparison:
    The Plots panel reports dimensionless metrics (k_eff, reactivity in
    dollars) alongside published Chernobyl reference values so the simulated
    behaviour can be compared qualitatively. See physics references in
    config.Physics.
"""

import sys
import pygame
from config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, ColorPalette, Physics
from reactor import Reactor
from ui_panel import UIPanel, Slider, Button


class App:
    """Main application class."""

    def __init__(self):
        """Initialize the application."""
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("RBMK Reactor Simulation")
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("Arial", 20, bold=True)
        self.font = pygame.font.SysFont("Arial", 15)
        self.font_small = pygame.font.SysFont("Arial", 13)

        self.paused = False

        self._setup_layout()
        self._setup_controls()

        self.running = True

    def _setup_layout(self):
        """Configure panel layout and reactor."""
        m = 15

        self.reactor_panel = UIPanel(
            pygame.Rect(m, m, 920, WINDOW_HEIGHT - 2 * m),
            "RBMK Reactor Core",
            self.font_title,
            self.font,
        )

        right_x = self.reactor_panel.rect.right + m
        right_w = WINDOW_WIDTH - right_x - m
        plots_h = 480

        self.plots_panel = UIPanel(
            pygame.Rect(right_x, m, right_w, plots_h),
            "Plots & Diagnostics",
            self.font_title,
            self.font,
        )

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

        rx = self.reactor_panel.rect.x + 10
        ry = self.reactor_panel.rect.y + 45
        rw = self.reactor_panel.rect.w - 20
        rh = self.reactor_panel.rect.h - 55
        self.reactor = Reactor(rx, ry, rw, rh, num_rods=10)

    def _setup_controls(self):
        """Build the sliders and buttons inside the Control Panel."""
        rect = self.ctrl_panel.rect
        cx = rect.x + 14
        inner_w = rect.w - 28

        avg = sum(self.reactor.get_rod_position(i)
                  for i in range(self.reactor.num_rods)) / self.reactor.num_rods
        self.master_slider = Slider(
            pygame.Rect(cx, rect.y + 62, inner_w, 16),
            value=avg,
            label="Master (all rods)",
            font=self.font_small,
        )

        btn_y = rect.y + 100
        self.start_btn = Button(
            pygame.Rect(cx, btn_y, 130, 28), "Pause", self.font_small
        )
        self.reset_btn = Button(
            pygame.Rect(cx + 145, btn_y, 110, 28), "Reset", self.font_small
        )

        self.rod_sliders = []
        self._rods_top = rect.y + 168
        col_w = inner_w // 2
        for i in range(self.reactor.num_rods):
            col = i // 5
            row = i % 5
            cell_x = cx + col * col_w
            cell_y = self._rods_top + row * 30
            slider = Slider(
                pygame.Rect(cell_x + 24, cell_y + 4, col_w - 44, 12),
                value=self.reactor.get_rod_position(i),
                label="",
                font=self.font_small,
                show_value=False,
            )
            self.rod_sliders.append(slider)

    def _handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self._toggle_pause()
                elif event.key == pygame.K_r:
                    self.reactor.reset()

            if self.master_slider.handle_event(event):
                v = self.master_slider.value
                self.reactor.set_all_rods(v)
                for s in self.rod_sliders:
                    s.value = v

            for i, slider in enumerate(self.rod_sliders):
                if slider.handle_event(event):
                    self.reactor.set_rod(i, slider.value)

            if self.start_btn.handle_event(event):
                self._toggle_pause()
            if self.reset_btn.handle_event(event):
                self.reactor.reset()

    def _toggle_pause(self):
        """Toggle the simulation pause state."""
        self.paused = not self.paused
        self.start_btn.set_label("Start" if self.paused else "Pause")

    def _update(self, dt):
        """Advance the simulation if not paused."""
        if not self.paused:
            self.reactor.update(dt)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw(self):
        """Draw the entire scene."""
        self.screen.fill(ColorPalette.APP_BG)

        self.reactor_panel.draw(self.screen, show_placeholder=False)
        self.plots_panel.draw(self.screen, show_placeholder=False)
        self.ctrl_panel.draw(self.screen, show_placeholder=False)

        self.reactor.draw(self.screen, self.font_small)
        self._draw_plots()
        self._draw_controls()

    def _draw_plots(self):
        """Draw the power-history graph and the diagnostic readouts."""
        rect = self.plots_panel.rect
        pad = 14
        graph = pygame.Rect(rect.x + pad, rect.y + 48,
                            rect.w - 2 * pad, 200)
        pygame.draw.rect(self.screen, ColorPalette.PLOT_BG, graph)
        pygame.draw.rect(self.screen, ColorPalette.PLOT_GRID, graph, 1)

        cap = self.font_small.render("Neutron population vs time",
                                     True, ColorPalette.MUTED)
        self.screen.blit(cap, (graph.x, graph.y - 18))

        hist = self.reactor.power_history
        if len(hist) >= 2:
            peak = max(max(hist), 50)
            for frac in (0.25, 0.5, 0.75):
                gy = int(graph.bottom - frac * graph.h)
                pygame.draw.line(self.screen, ColorPalette.PLOT_GRID,
                                 (graph.x, gy), (graph.right, gy))
            pts = []
            n = len(hist)
            for i, v in enumerate(hist):
                px = graph.x + int(i / (n - 1) * (graph.w - 1))
                py = graph.bottom - int(min(v, peak) / peak * (graph.h - 1))
                pts.append((px, py))
            pygame.draw.lines(self.screen, ColorPalette.PLOT_LINE, False, pts, 2)
            peak_lbl = self.font_small.render(f"peak {peak}", True,
                                              ColorPalette.MUTED)
            self.screen.blit(peak_lbl, (graph.right - peak_lbl.get_width() - 4,
                                        graph.y + 4))

        self._draw_diagnostics(rect, graph.bottom + 16)

    def _draw_diagnostics(self, rect, y0):
        """Draw the k_eff / reactivity readouts and reference values."""
        x = rect.x + 16
        y = y0

        k = self.reactor.k_eff
        d = self.reactor.reactivity_dollars
        state = self.reactor.criticality_state()
        state_color = {
            "Subcritical": ColorPalette.STATE_SUB,
            "Critical": ColorPalette.STATE_CRIT,
            "Supercritical": ColorPalette.STATE_SUPER,
        }.get(state, ColorPalette.MUTED)

        def line(text, color=ColorPalette.TEXT, dy=20, bold=False):
            nonlocal y
            font = self.font if not bold else self.font_title
            surf = font.render(text, True, color)
            self.screen.blit(surf, (x, y))
            y += dy

        line(f"k_eff = {k:6.3f}", bold=False)
        sign = "+" if d >= 0 else ""
        line(f"Reactivity = {sign}{d:5.2f} $   (rho/beta)")
        line(f"State: {state}", color=state_color)
        line(f"Fission rate = {self.reactor.fission_rate:5.0f} /s")
        line(f"Neutrons = {len(self.reactor.neutrons)} / {Physics.MAX_NEUTRONS}")

        y += 8
        pygame.draw.line(self.screen, ColorPalette.PANEL_BORDER,
                         (x, y), (rect.right - 16, y))
        y += 10
        line("Chernobyl reference (qualitative):",
             color=ColorPalette.MUTED, dy=19)
        for ref in (
            "beta_eff = 0.0065  (INSAG-7)",
            "Critical when k_eff = 1.00",
            "Void coef. +(4-5) beta  (INSAG-7)",
            "Rod insertion: +396 pcm w/ Xe,",
            "  -344 pcm normal  (EPJ N 2021)",
        ):
            line(ref, color=ColorPalette.MUTED, dy=18)

    def _draw_controls(self):
        """Draw the sliders, buttons and rod labels in the Control Panel."""
        self.master_slider.draw(self.screen)
        self.start_btn.draw(self.screen)
        self.reset_btn.draw(self.screen)

        rect = self.ctrl_panel.rect
        hdr = self.font_small.render("Individual control rods (0=out, 100=in)",
                                     True, ColorPalette.MUTED)
        self.screen.blit(hdr, (rect.x + 14, self._rods_top - 20))

        for i, slider in enumerate(self.rod_sliders):
            lbl = self.font_small.render(str(i + 1), True, ColorPalette.TEXT)
            self.screen.blit(lbl, (slider.rect.x - 20, slider.rect.y - 3))
            slider.draw(self.screen)

    def run(self):
        """Main application loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


def main():
    """Entry point for the application."""
    app = App()
    app.run()


if __name__ == "__main__":
    main()
