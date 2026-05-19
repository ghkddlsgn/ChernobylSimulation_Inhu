"""
RBMK Reactor core geometry and material lookup.
"""

import random
import pygame
from config import (
    ColorPalette,
    MATERIAL_WATER,
    MATERIAL_GRAPHITE,
    MATERIAL_BORON,
    MATERIAL_FUEL,
    MATERIAL_AIR,
)
from control_rod import ControlRod


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
        """Initialize the reactor geometry.

        Args:
            x, y: Top-left corner of the reactor panel.
            w, h: Width and height of the reactor panel.
            num_rods: Number of control rod channels.
        """
        self.x, self.y, self.w, self.h = x, y, w, h
        self.num_rods = num_rods
        self.num_graphite_cols = num_rods + 1

        self._setup_vertical_layout()
        self._setup_horizontal_layout()
        self._setup_control_rods()
        self._build_fuel_grid()

    def _setup_vertical_layout(self):
        """Configure vertical geometry of the reactor."""
        self.rod_extension_h = 170
        self.water_top_h = 50
        self.graphite_top_h = 75
        self.fuel_h = 230
        self.graphite_bottom_h = 75
        self.water_bottom_h = 40

        self.top_padding = 10
        self.water_top_y = self.y + self.top_padding + self.rod_extension_h
        self.core_top_y = self.water_top_y + self.water_top_h
        self.fuel_top_y = self.core_top_y + self.graphite_top_h
        self.fuel_bottom_y = self.fuel_top_y + self.fuel_h
        self.core_bottom_y = self.fuel_bottom_y + self.graphite_bottom_h
        self.water_bot_y = self.core_bottom_y

        self.body_top_y = self.water_top_y
        self.body_bottom_y = self.water_bot_y + self.water_bottom_h

        self.rod_visible_top_y = self.y + self.top_padding

    def _setup_horizontal_layout(self):
        """Configure horizontal geometry of the reactor."""
        self.rod_channel_w = 16
        side_margin = 25
        usable = self.w - 2 * side_margin
        used_rod = self.num_rods * self.rod_channel_w
        self.graphite_w = (usable - used_rod) // self.num_graphite_cols
        total_w = self.num_graphite_cols * self.graphite_w + used_rod
        self.cols_x0 = self.x + (self.w - total_w) // 2
        self.body_left = self.cols_x0 - 8
        self.body_right = self.cols_x0 + total_w + 8

    def _setup_control_rods(self):
        """Initialize control rods with varied starting positions."""
        self.rods = []
        for i in range(self.num_rods):
            cx = self.cols_x0 + (i + 1) * self.graphite_w + i * self.rod_channel_w
            rod = ControlRod(
                channel_x=cx,
                channel_w=self.rod_channel_w,
                body_top_y=self.body_top_y,
                body_bottom_y=self.body_bottom_y,
                visible_top_y=self.rod_visible_top_y,
            )
            self.rods.append(rod)

        # Varied initial positions to mirror different control rod groups
        initial_positions = [0.05, 0.30, 0.50, 0.95, 0.20, 0.55, 0.45, 0.85, 0.60, 0.10]
        for r, p in zip(self.rods, initial_positions):
            r.set_normalized_position(p)

    def _build_fuel_grid(self):
        """Generate the fuel dot grid with random distribution."""
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

    # Fuel dot parameters
    dot_spacing = 9
    dot_radius = 2

    # ---- Material Lookup API (for neutrons) --------------------------------
    def material_at(self, px, py):
        """Return the material at world coordinates (px, py).

        This is the API that neutrons will use to determine how they interact
        with their environment.

        Args:
            px, py: World coordinates.

        Returns:
            One of the MATERIAL_* constants.
        """
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
        if section == "graphite":
            return MATERIAL_GRAPHITE
        if section == "boron":
            return MATERIAL_BORON
        return None

    # ---- Drawing --------------------------------------------------------
    def draw(self, surf, font_small):
        """Draw the reactor on the given surface.

        Args:
            surf: Pygame surface to draw on.
            font_small: Small font for labels (reserved for future use).
        """
        self._draw_body(surf)
        self._draw_graphite_and_fuel(surf)
        self._draw_control_rods(surf)

    def _draw_body(self, surf):
        """Draw the reactor body (water outline)."""
        body_rect = pygame.Rect(
            self.body_left,
            self.body_top_y,
            self.body_right - self.body_left,
            self.body_bottom_y - self.body_top_y,
        )
        pygame.draw.rect(surf, ColorPalette.WATER, body_rect)
        pygame.draw.rect(surf, ColorPalette.WATER_OUTLINE, body_rect, 1)

    def _draw_graphite_and_fuel(self, surf):
        """Draw graphite columns and fuel zones with dots."""
        for ci in range(self.num_graphite_cols):
            bx = self.cols_x0 + ci * (self.graphite_w + self.rod_channel_w)

            # Top graphite block
            pygame.draw.rect(
                surf,
                ColorPalette.GRAPHITE,
                (bx, self.core_top_y, self.graphite_w, self.graphite_top_h),
            )

            # Bottom graphite block
            pygame.draw.rect(
                surf,
                ColorPalette.GRAPHITE,
                (bx, self.fuel_bottom_y, self.graphite_w, self.graphite_bottom_h),
            )

            # Fuel zone background
            pygame.draw.rect(
                surf,
                ColorPalette.FUEL_BG,
                (bx, self.fuel_top_y, self.graphite_w, self.fuel_h),
            )

            # Fuel dots
            self._draw_fuel_dots(surf, ci, bx)

    def _draw_fuel_dots(self, surf, col_idx, bx):
        """Draw fuel dots for a specific column."""
        n_c, n_r = self._n_dot_cols, self._n_dot_rows
        x_off = (self.graphite_w - n_c * self.dot_spacing) // 2
        y_off = (self.fuel_h - n_r * self.dot_spacing) // 2

        for r in range(n_r):
            for c in range(n_c):
                dot_type = self.fuel[(col_idx, r, c)]
                dx = bx + x_off + c * self.dot_spacing + self.dot_spacing // 2
                dy = self.fuel_top_y + y_off + r * self.dot_spacing + self.dot_spacing // 2

                if dot_type == "reactive":
                    color = ColorPalette.U_REACTIVE
                elif dot_type == "nonreactive":
                    color = ColorPalette.U_NONREACTIVE
                else:  # xenon
                    color = ColorPalette.XENON

                pygame.draw.circle(surf, color, (dx, dy), self.dot_radius)

    def _draw_control_rods(self, surf):
        """Draw all control rods."""
        for rod in self.rods:
            rod.draw(surf)
