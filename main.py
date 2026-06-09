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

import os
import sys
import datetime
import pygame
from config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, ColorPalette, Physics
from reactor import Reactor
from ui_panel import UIPanel, Slider, Button
from plotter import generate_plots
from chernobyl_script import EVENTS as CHERNOBYL_EVENTS


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

        # Chernobyl replay state
        self.chernobyl_mode    = False
        self.chernobyl_elapsed = 0.0
        self.chernobyl_ev_idx  = -1
        self._cher_title       = ""
        self._cher_lines       = []
        self._cher_exploded    = False
        self._cher_rod_start   = [0.0] * self.reactor.num_rods
        self._cher_rod_target  = [0.0] * self.reactor.num_rods
        self._cher_rod_t       = 1.0   # 1.0 = transition complete
        self._cher_rod_dur     = 4.0   # seconds per rod transition

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
        plots_h = 515

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
        self.reactor = Reactor(rx, ry, rw, rh, num_fuel_cols=11, num_rods=10)

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
        self.save_btn = Button(
            pygame.Rect(cx + 270, btn_y, 125, 28), "Stop & Save", self.font_small
        )
        self.chernobyl_btn = Button(
            pygame.Rect(cx, rect.y + 135, inner_w, 28),
            "⚡ Chernobyl Replay", self.font_small,
        )

        self.rod_sliders = []
        self._rods_top = rect.y + 200
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
            if self.save_btn.handle_event(event):
                self._stop_and_save()
            if self.chernobyl_btn.handle_event(event):
                self._toggle_chernobyl()

    def _toggle_pause(self):
        """Toggle the simulation pause state."""
        self.paused = not self.paused
        self.start_btn.set_label("Start" if self.paused else "Pause")

    def _stop_and_save(self):
        """Pause the simulation, queue plot generation, then close the app."""
        if not self.paused:
            self._toggle_pause()
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self._pending_plot_dir = os.path.join('plots', timestamp)
        os.makedirs(self._pending_plot_dir, exist_ok=True)
        self.running = False

    def _toggle_chernobyl(self):
        """Start or cancel the automated Chernobyl replay."""
        if self.chernobyl_mode:
            self.chernobyl_mode = False
            self._cher_exploded = False
            self.chernobyl_btn.set_label("⚡ Chernobyl Replay")
        else:
            self.reactor.reset()
            self.paused = False
            self.start_btn.set_label("Pause")
            self.chernobyl_mode    = True
            self.chernobyl_elapsed = 0.0
            self.chernobyl_ev_idx  = -1
            self._cher_exploded    = False
            self.chernobyl_btn.set_label("■ Stop Replay")
            self._apply_chernobyl_event(CHERNOBYL_EVENTS[0])

    def _apply_chernobyl_event(self, ev):
        """Load an event's description and start a smooth rod transition."""
        self._cher_title = ev["title"]
        self._cher_lines = ev["lines"]
        self._cher_rod_start  = [self.reactor.get_rod_position(i)
                                  for i in range(self.reactor.num_rods)]
        self._cher_rod_target = list(ev["rods"])
        self._cher_rod_t      = 0.0
        self._cher_rod_dur    = ev.get("duration", 4.0)

    def _advance_chernobyl(self, dt):
        """Drive rod interpolation and advance through the event script."""
        self.chernobyl_elapsed += dt

        # Smooth rod interpolation (linear over _cher_rod_dur seconds)
        if self._cher_rod_t < 1.0:
            self._cher_rod_t = min(1.0, self._cher_rod_t + dt / self._cher_rod_dur)
            for i in range(self.reactor.num_rods):
                pos = (self._cher_rod_start[i]
                       + (self._cher_rod_target[i] - self._cher_rod_start[i])
                       * self._cher_rod_t)
                self.reactor.set_rod(i, pos)
                self.rod_sliders[i].value = pos
            avg = sum(self.reactor.get_rod_position(i)
                      for i in range(self.reactor.num_rods)) / self.reactor.num_rods
            self.master_slider.value = avg

        # Fire the next event when its timestamp is reached
        next_idx = self.chernobyl_ev_idx + 1
        if next_idx < len(CHERNOBYL_EVENTS):
            if self.chernobyl_elapsed >= CHERNOBYL_EVENTS[next_idx]["time"]:
                self.chernobyl_ev_idx = next_idx
                self._apply_chernobyl_event(CHERNOBYL_EVENTS[next_idx])
                if next_idx == len(CHERNOBYL_EVENTS) - 1:
                    self._cher_exploded = True

        # Auto-pause 5 s after the final explosion event
        if self._cher_exploded:
            explosion_time = CHERNOBYL_EVENTS[-1]["time"]
            if self.chernobyl_elapsed >= explosion_time + 5.0 and not self.paused:
                self._toggle_pause()

    def _update(self, dt):
        """Advance the simulation if not paused."""
        if not self.paused:
            if self.chernobyl_mode:
                self._advance_chernobyl(dt)
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
        if self.chernobyl_mode:
            self._draw_chernobyl_overlay()

    def _draw_plots(self):
        """Draw the power-history graph and the diagnostic readouts."""
        rect = self.plots_panel.rect
        pad = 14
        graph = pygame.Rect(rect.x + pad, rect.y + 48,
                            rect.w - 2 * pad, 185)
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

        def line(text, color=ColorPalette.TEXT, dy=19, bold=False):
            nonlocal y
            font = self.font if not bold else self.font_title
            surf = font.render(text, True, color)
            self.screen.blit(surf, (x, y))
            y += dy

        void_pct = self.reactor.avg_void * 100.0
        void_color = (ColorPalette.STATE_SUPER if void_pct > 50
                      else ColorPalette.TEXT)

        line(f"k_eff = {k:6.3f}", bold=False)
        sign = "+" if d >= 0 else ""
        line(f"Reactivity = {sign}{d:5.2f} $   (rho/beta)")
        line(f"State: {state}", color=state_color)
        line(f"Steam void = {void_pct:4.0f} %  (+ feedback)", color=void_color)
        line(f"Fission rate = {self.reactor.fission_rate:5.0f} /s")
        line(f"Neutrons = {len(self.reactor.neutrons)} / {Physics.MAX_NEUTRONS}")
        line(f"Fuel channels = {self.reactor.num_fuel_cols}, "
             f"rods = {self.reactor.num_rods}",
             color=ColorPalette.MUTED)

        y += 6
        pygame.draw.line(self.screen, ColorPalette.PANEL_BORDER,
                         (x, y), (rect.right - 16, y))
        y += 8
        line("Chernobyl reference (qualitative):",
             color=ColorPalette.MUTED, dy=18)
        for ref in (
            "beta_eff = 0.0065  (INSAG-7)",
            "Void coef. +(4-5) beta  (INSAG-7)",
            "Rod insertion: +396 pcm w/ Xe,",
            "  -344 pcm normal  (EPJ N 2021)",
        ):
            line(ref, color=ColorPalette.MUTED, dy=17)

    def _draw_controls(self):
        """Draw the sliders, buttons and rod labels in the Control Panel."""
        self.master_slider.draw(self.screen)
        self.start_btn.draw(self.screen)
        self.reset_btn.draw(self.screen)
        self.save_btn.draw(self.screen)
        self.chernobyl_btn.draw(self.screen)

        rect = self.ctrl_panel.rect
        hdr = self.font_small.render("Individual control rods (0=out, 100=in)",
                                     True, ColorPalette.MUTED)
        self.screen.blit(hdr, (rect.x + 14, self._rods_top - 20))

        for i, slider in enumerate(self.rod_sliders):
            lbl = self.font_small.render(str(i + 1), True, ColorPalette.TEXT)
            self.screen.blit(lbl, (slider.rect.x - 20, slider.rect.y - 3))
            slider.draw(self.screen)

    def _draw_chernobyl_overlay(self):
        """Draw the semi-transparent event description over the reactor panel."""
        r = self.reactor_panel.rect
        PAD, BOX_H = 18, 140
        box = pygame.Rect(r.x + PAD, r.bottom - BOX_H - PAD,
                          r.w - 2 * PAD, BOX_H)

        overlay = pygame.Surface((box.w, box.h), pygame.SRCALPHA)
        bg = (180, 20, 20, 210) if self._cher_exploded else (10, 10, 30, 210)
        pygame.draw.rect(overlay, bg, overlay.get_rect(), border_radius=6)
        pygame.draw.rect(overlay, (255, 255, 255, 60),
                         overlay.get_rect(), 1, border_radius=6)
        self.screen.blit(overlay, box.topleft)

        title_color = (255, 80, 60) if self._cher_exploded else (255, 220, 100)
        ts = self.font.render(self._cher_title, True, title_color)
        self.screen.blit(ts, (box.x + 12, box.y + 10))

        for i, ln in enumerate(self._cher_lines):
            ls = self.font_small.render(ln, True, (230, 230, 230))
            self.screen.blit(ls, (box.x + 12, box.y + 34 + i * 22))

    def run(self):
        """Main application loop."""
        self._pending_plot_dir = None
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()

        pygame.quit()

        if self._pending_plot_dir is not None:
            saved = generate_plots(self.reactor, self._pending_plot_dir)
            if saved:
                print(f"[App] {len(saved)} plot(s) saved to: {self._pending_plot_dir}")
                for p in saved:
                    print(f"      {p}")
            else:
                print("[App] No history data — simulation was never run.")

        sys.exit()


def main():
    """Entry point for the application."""
    app = App()
    app.run()


if __name__ == "__main__":
    main()
