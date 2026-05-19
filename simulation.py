"""
RBMK Reactor Simulation - Prototype
====================================

This is the core layout: window, reactor geometry, control rods, and the fuel-
dot grid. Neutrons, plots and the control panel are intentionally left for
later iterations -- placeholders sit where they will go.

Run:  pip install pygame  &&  python rbmk_sim.py
"""

import random
import sys

import pygame

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
FPS = 60


class C:
    """Color palette, picked to echo the diagram in image 1."""
    APP_BG          = (235, 235, 240)
    PANEL_BG        = (250, 250, 253)
    PANEL_BORDER    = (200, 200, 210)
    TEXT            = (40, 40, 50)
    MUTED           = (140, 140, 150)

    WATER           = (181, 213, 219)
    WATER_OUTLINE   = (130, 170, 180)
    GRAPHITE        = (72, 24, 92)     # dark purple
    BORON           = (76, 187, 23)    # green
    ROD_CASING      = (72, 24, 92)     # same purple as graphite

    FUEL_BG         = (195, 215, 222)  # slightly different blue than WATER
    U_REACTIVE      = (66, 130, 230)   # blue dot
    U_NONREACTIVE   = (165, 165, 170)  # gray dot
    XENON           = (35, 35, 40)     # black dot


# Material constants -- neutrons will query against these later.
MATERIAL_WATER    = "water"
MATERIAL_GRAPHITE = "graphite"
MATERIAL_BORON    = "boron"
MATERIAL_FUEL     = "fuel"
MATERIAL_AIR      = "air"


# ---------------------------------------------------------------------------
# Control Rod
# ---------------------------------------------------------------------------
class ControlRod:
    """An RBMK control rod.

    From bottom to top, the rod consists of:
      * a graphite displacer (the "tip", same material as the moderator),
      * a thin gap (water-filled in reality, drawn as a narrow casing strut),
      * a long boron-iron alloy absorber,
      * an upper casing/handle that protrudes above the reactor body.

    `tip_y` is the world y-coordinate of the very bottom of the rod (the bottom
    of the graphite displacer). Sections grow upward from there.
    """

    GRAPHITE_LEN = 75
    GAP_LEN      = 18
    BORON_LEN    = 290
    CASING_LEN   = 220

    def __init__(self, channel_x, channel_w, body_top_y, body_bottom_y,
                 visible_top_y):
        self.channel_x = channel_x
        self.channel_w = channel_w
        self.body_top_y = body_top_y          # top of the reactor body
        self.body_bottom_y = body_bottom_y    # bottom-most y the tip can reach
        self.visible_top_y = visible_top_y    # rod is not drawn above this y
        self.tip_y = body_top_y               # placeholder, set via set_normalized_position
        self.set_normalized_position(0.5)

    @property
    def total_length(self):
        return self.GRAPHITE_LEN + self.GAP_LEN + self.BORON_LEN + self.CASING_LEN

    def set_normalized_position(self, p):
        """0.0 = fully withdrawn ("prohibited", tip just above body).
        1.0 = fully inserted ("shutdown", tip at the bottom of the body)."""
        p = max(0.0, min(1.0, p))
        y_high = self.body_top_y - 5            # tip just above the body
        y_low  = self.body_bottom_y             # tip at bottom of body
        self.tip_y = int(y_high + p * (y_low - y_high))

    # ---- material queries ------------------------------------------------
    def section_at_y(self, y):
        """Return which rod section sits at world-y `y`, or None if no rod."""
        graphite_top = self.tip_y - self.GRAPHITE_LEN
        gap_top      = graphite_top - self.GAP_LEN
        boron_top    = gap_top - self.BORON_LEN
        casing_top   = boron_top - self.CASING_LEN
        if y > self.tip_y or y < casing_top:
            return None
        if y > graphite_top: return "graphite"
        if y > gap_top:      return "gap"
        if y > boron_top:    return "boron"
        return "casing"

    # ---- drawing ---------------------------------------------------------
    def draw(self, surf):
        cx     = self.channel_x + self.channel_w // 2
        rod_w  = self.channel_w - 4
        thin_w = max(4, rod_w // 2)

        graphite_top = self.tip_y - self.GRAPHITE_LEN
        gap_top      = graphite_top - self.GAP_LEN
        boron_top    = gap_top - self.BORON_LEN
        casing_top   = boron_top - self.CASING_LEN

        clip_y = self.visible_top_y

        def draw_section(color, top, bottom, width):
            """Draw a rod section between [top, bottom], clipping at clip_y."""
            top = max(top, clip_y)
            if bottom <= top:
                return
            pygame.draw.rect(
                surf, color, (cx - width // 2, top, width, bottom - top),
            )

        # Top casing (thin stem above the boron)
        draw_section(C.ROD_CASING, casing_top, boron_top, thin_w)
        # Boron absorber
        draw_section(C.BORON, boron_top, boron_top + self.BORON_LEN, rod_w)
        # Gap (thin connector)
        draw_section(C.ROD_CASING, gap_top, gap_top + self.GAP_LEN, thin_w)
        # Graphite displacer (the tip)
        draw_section(C.GRAPHITE, graphite_top, graphite_top + self.GRAPHITE_LEN, rod_w)


# ---------------------------------------------------------------------------
# Reactor
# ---------------------------------------------------------------------------
class Reactor:
    """The full reactor cross-section.

    Horizontally:  graphite | rod-channel | graphite | rod-channel | ... | graphite
        (num_rods rod channels, num_rods + 1 graphite columns)

    Vertically, top to bottom:
        top padding (empty, keeps rods off the title bar)
        rod-extension area  (rods stick up out of the body)
        water (top)
        core: graphite block | fuel zone | graphite block
        water (bottom)
    """

    def __init__(self, x, y, w, h, num_rods=10):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.num_rods = num_rods
        self.num_graphite_cols = num_rods + 1

        # ---- vertical layout (heights) ----------------------------------
        self.rod_extension_h    = 170   # area where rod casings are visible above the body
        self.water_top_h        = 50
        self.graphite_top_h     = 75
        self.fuel_h             = 230
        self.graphite_bottom_h  = 75
        self.water_bottom_h     = 40

        # ---- vertical layout (y coordinates) -----------------------------
        # Push the whole reactor down by this offset to leave clean space at
        # the top of the panel (so rods don't run into the title bar).
        self.top_padding    = 10
        self.water_top_y    = y + self.top_padding + self.rod_extension_h
        self.core_top_y     = self.water_top_y + self.water_top_h
        self.fuel_top_y     = self.core_top_y + self.graphite_top_h
        self.fuel_bottom_y  = self.fuel_top_y + self.fuel_h
        self.core_bottom_y  = self.fuel_bottom_y + self.graphite_bottom_h
        self.water_bot_y    = self.core_bottom_y

        self.body_top_y     = self.water_top_y
        self.body_bottom_y  = self.water_bot_y + self.water_bottom_h

        # Rod casings only render below this y -- ensures they disappear
        # well before reaching the panel edge.
        self.rod_visible_top_y = y + self.top_padding

        # ---- horizontal layout -----------------------------------------
        self.rod_channel_w = 16
        side_margin = 25
        usable = w - 2 * side_margin
        used_rod = num_rods * self.rod_channel_w
        self.graphite_w = (usable - used_rod) // self.num_graphite_cols
        total_w = self.num_graphite_cols * self.graphite_w + used_rod
        self.cols_x0 = x + (w - total_w) // 2
        self.body_left  = self.cols_x0 - 8
        self.body_right = self.cols_x0 + total_w + 8

        # ---- control rods ------------------------------------------------
        self.rods = []
        for i in range(num_rods):
            cx = self.cols_x0 + (i + 1) * self.graphite_w + i * self.rod_channel_w
            rod = ControlRod(
                channel_x=cx,
                channel_w=self.rod_channel_w,
                body_top_y=self.body_top_y,
                body_bottom_y=self.body_bottom_y,
                visible_top_y=self.rod_visible_top_y,
            )
            self.rods.append(rod)
        # Varied initial positions to mirror image 1's I/II/III/IV layout.
        initial_positions = [0.05, 0.30, 0.50, 0.95, 0.20, 0.55, 0.45, 0.85, 0.60, 0.10]
        for r, p in zip(self.rods, initial_positions):
            r.set_normalized_position(p)

        # ---- fuel dot grid ----------------------------------------------
        self.dot_spacing = 9
        self.dot_radius  = 2
        self._build_fuel_grid()

    def _build_fuel_grid(self):
        rng = random.Random(42)
        self.fuel = {}  # (col_index, row, col) -> 'reactive'|'nonreactive'|'xenon'
        n_cols = max(1, (self.graphite_w - 4) // self.dot_spacing)
        n_rows = max(1, (self.fuel_h - 4) // self.dot_spacing)
        self._n_dot_cols = n_cols
        self._n_dot_rows = n_rows
        for ci in range(self.num_graphite_cols):
            for r in range(n_rows):
                for c in range(n_cols):
                    v = rng.random()
                    if v < 0.22:
                        t = "reactive"
                    elif v < 0.98:
                        t = "nonreactive"
                    else:
                        t = "xenon"
                    self.fuel[(ci, r, c)] = t

    # ---- material lookup (the API neutrons will use) --------------------
    def material_at(self, px, py):
        """Return the material at world coordinates (px, py)."""
        # Outside the reactor body
        if (py < self.body_top_y or py > self.body_bottom_y
                or px < self.body_left or px > self.body_right):
            return MATERIAL_AIR

        # Above-core or below-core water region: maybe a rod is here
        if py < self.core_top_y or py >= self.core_bottom_y:
            mat = self._rod_material_at(px, py)
            return mat if mat else MATERIAL_WATER

        # Inside the core -- pick column
        local = px - self.cols_x0
        col_w = self.graphite_w + self.rod_channel_w
        if local < 0 or local >= self.num_graphite_cols * col_w + self.graphite_w:
            return MATERIAL_WATER
        comp_idx = int(local // col_w)
        within = local - comp_idx * col_w
        if within < self.graphite_w:
            # Graphite column
            if py < self.fuel_top_y or py >= self.fuel_bottom_y:
                return MATERIAL_GRAPHITE
            return MATERIAL_FUEL
        # Rod channel: rod or water
        mat = self._rod_material_at(px, py)
        return mat if mat else MATERIAL_WATER

    def _rod_material_at(self, px, py):
        """If px,py falls on a rod section, return that material; else None."""
        local = px - self.cols_x0
        col_w = self.graphite_w + self.rod_channel_w
        if local < 0:
            return None
        comp_idx = int(local // col_w)
        within = local - comp_idx * col_w
        if within < self.graphite_w:
            return None  # graphite column, no rod here
        rod_idx = comp_idx
        if rod_idx < 0 or rod_idx >= len(self.rods):
            return None
        section = self.rods[rod_idx].section_at_y(py)
        if section == "graphite": return MATERIAL_GRAPHITE
        if section == "boron":    return MATERIAL_BORON
        return None

    # ---- drawing --------------------------------------------------------
    def draw(self, surf, font_small):
        # Reactor body (water fills it everywhere, then we overlay solids)
        body_rect = pygame.Rect(
            self.body_left, self.body_top_y,
            self.body_right - self.body_left,
            self.body_bottom_y - self.body_top_y,
        )
        pygame.draw.rect(surf, C.WATER, body_rect)
        pygame.draw.rect(surf, C.WATER_OUTLINE, body_rect, 1)

        # Graphite columns + fuel zone with dots
        for ci in range(self.num_graphite_cols):
            bx = self.cols_x0 + ci * (self.graphite_w + self.rod_channel_w)
            # Top graphite block
            pygame.draw.rect(
                surf, C.GRAPHITE,
                (bx, self.core_top_y, self.graphite_w, self.graphite_top_h),
            )
            # Bottom graphite block
            pygame.draw.rect(
                surf, C.GRAPHITE,
                (bx, self.fuel_bottom_y, self.graphite_w, self.graphite_bottom_h),
            )
            # Fuel zone background
            pygame.draw.rect(
                surf, C.FUEL_BG,
                (bx, self.fuel_top_y, self.graphite_w, self.fuel_h),
            )
            # Dots
            n_c, n_r = self._n_dot_cols, self._n_dot_rows
            x_off = (self.graphite_w - n_c * self.dot_spacing) // 2
            y_off = (self.fuel_h - n_r * self.dot_spacing) // 2
            for r in range(n_r):
                for c in range(n_c):
                    t = self.fuel[(ci, r, c)]
                    dx = bx + x_off + c * self.dot_spacing + self.dot_spacing // 2
                    dy = self.fuel_top_y + y_off + r * self.dot_spacing + self.dot_spacing // 2
                    if t == "reactive":
                        pygame.draw.circle(surf, C.U_REACTIVE, (dx, dy), self.dot_radius)
                    elif t == "nonreactive":
                        pygame.draw.circle(surf, C.U_NONREACTIVE, (dx, dy), self.dot_radius)
                    else:
                        pygame.draw.circle(surf, C.XENON, (dx, dy), self.dot_radius)

        # Control rods on top of everything
        for rod in self.rods:
            rod.draw(surf)


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("RBMK Reactor Simulation - Prototype")
        self.clock = pygame.time.Clock()
        self.font_title = pygame.font.SysFont("Arial", 20, bold=True)
        self.font       = pygame.font.SysFont("Arial", 15)
        self.font_small = pygame.font.SysFont("Arial", 13)

        # Layout: reactor on the left, plots top-right, controls bottom-right
        m = 15
        self.reactor_panel = pygame.Rect(m, m, 920, WINDOW_HEIGHT - 2 * m)
        right_x = self.reactor_panel.right + m
        right_w = WINDOW_WIDTH - right_x - m
        plots_h = 480
        self.plots_panel = pygame.Rect(right_x, m, right_w, plots_h)
        self.ctrl_panel  = pygame.Rect(
            right_x, m + plots_h + m,
            right_w, WINDOW_HEIGHT - 2 * m - plots_h - m,
        )

        # Reactor sits inside its panel with some padding for the title bar.
        rx = self.reactor_panel.x + 10
        ry = self.reactor_panel.y + 45
        rw = self.reactor_panel.w - 20
        rh = self.reactor_panel.h - 55
        self.reactor = Reactor(rx, ry, rw, rh, num_rods=10)

        self.running = True

    def draw_panel(self, rect, title, placeholder=False):
        pygame.draw.rect(self.screen, C.PANEL_BG, rect, border_radius=10)
        pygame.draw.rect(self.screen, C.PANEL_BORDER, rect, width=1, border_radius=10)
        title_surf = self.font_title.render(title, True, C.TEXT)
        self.screen.blit(title_surf, (rect.x + 14, rect.y + 10))
        pygame.draw.line(
            self.screen, C.PANEL_BORDER,
            (rect.x + 12, rect.y + 38), (rect.right - 12, rect.y + 38),
        )
        if placeholder:
            text = self.font.render("(placeholder)", True, C.MUTED)
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False

            self.screen.fill(C.APP_BG)
            self.draw_panel(self.reactor_panel, "RBMK Reactor Core")
            self.reactor.draw(self.screen, self.font_small)
            self.draw_panel(self.plots_panel, "Plots", placeholder=True)
            self.draw_panel(self.ctrl_panel,  "Control Panel", placeholder=True)

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    App().run()