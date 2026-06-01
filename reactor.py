"""
RBMK Reactor core geometry and material lookup.
"""

import math
import random
import pygame
from config import (
    ColorPalette,
    Physics,
    MATERIAL_WATER,
    MATERIAL_GRAPHITE,
    MATERIAL_BORON,
    MATERIAL_FUEL,
    MATERIAL_AIR,
)
from control_rod import ControlRod
from neutron import Neutron


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
        self._init_simulation()

    def _init_simulation(self):
        """Initialize the dynamic neutron-transport state."""
        self.neutrons = []
        self.rng_sim = random.Random()
        self.power_history = []
        self._collision_r2 = (self.dot_spacing * 0.6) ** 2

        # Exponentially smoothed neutron-balance counters used to estimate the
        # multiplication factor k_eff (see update()).
        self._ema_fission_neutrons = 0.0
        self._ema_fissions = 0.0
        self._ema_losses = 0.0
        self.k_eff = 0.0
        self.reactivity_dollars = 0.0
        self.fission_rate = 0.0
        self._frame_fissions = 0

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

        initial_positions = [0.05, 0.30, 0.50, 0.95, 0.20, 0.55, 0.45, 0.85, 0.60, 0.10]
        for r, p in zip(self.rods, initial_positions):
            r.set_normalized_position(p)

    def _build_fuel_grid(self):
        """Generate the fuel dot grid with random distribution."""
        rng = random.Random(42)
        self.fuel = {}
        n_cols = max(1, (self.graphite_w - 4) // self.dot_spacing)
        n_rows = max(1, (self.fuel_h - 4) // self.dot_spacing)
        self._n_dot_cols = n_cols
        self._n_dot_rows = n_rows

        self._dot_x_off = (self.graphite_w - n_cols * self.dot_spacing) // 2
        self._dot_y_off = (self.fuel_h - n_rows * self.dot_spacing) // 2

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

    dot_spacing = 9
    dot_radius = 2

    def material_at(self, px, py):
        """Return the material at world coordinates (px, py).

        This is the API that neutrons will use to determine how they interact
        with their environment.

        Args:
            px, py: World coordinates.

        Returns:
            One of the MATERIAL_* constants.
        """
        if (py < self.body_top_y or py > self.body_bottom_y
                or px < self.body_left or px > self.body_right):
            return MATERIAL_AIR

        if py < self.core_top_y or py >= self.core_bottom_y:
            mat = self._rod_material_at(px, py)
            return mat if mat else MATERIAL_WATER

        local = px - self.cols_x0
        col_w = self.graphite_w + self.rod_channel_w
        if local < 0 or local >= self.num_graphite_cols * col_w + self.graphite_w:
            return MATERIAL_WATER

        comp_idx = int(local // col_w)
        within = local - comp_idx * col_w

        if within < self.graphite_w:
            if py < self.fuel_top_y or py >= self.fuel_bottom_y:
                return MATERIAL_GRAPHITE
            return MATERIAL_FUEL

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
            return None

        rod_idx = comp_idx
        if rod_idx < 0 or rod_idx >= len(self.rods):
            return None

        section = self.rods[rod_idx].section_at_y(py)
        if section == "graphite":
            return MATERIAL_GRAPHITE
        if section == "boron":
            return MATERIAL_BORON
        return None

    def fuel_dot_at(self, px, py):
        """Return the nearest fuel dot to world coords, or None.

        Args:
            px, py: World coordinates (expected to be inside a fuel zone).

        Returns:
            Tuple ((ci, r, c), dot_type) for the nearest fuel dot, or None if
            (px, py) is not over the fuelled lattice of a graphite column.
        """
        if py < self.fuel_top_y or py >= self.fuel_bottom_y:
            return None

        local = px - self.cols_x0
        if local < 0:
            return None
        col_w = self.graphite_w + self.rod_channel_w
        comp_idx = int(local // col_w)
        within = local - comp_idx * col_w
        if comp_idx >= self.num_graphite_cols or within >= self.graphite_w:
            return None

        c = int((within - self._dot_x_off) // self.dot_spacing)
        r = int((py - self.fuel_top_y - self._dot_y_off) // self.dot_spacing)
        if not (0 <= c < self._n_dot_cols and 0 <= r < self._n_dot_rows):
            return None

        key = (comp_idx, r, c)
        return key, self.fuel[key]

    def _dot_center(self, key):
        """Return the world-coordinate center of fuel dot `key`."""
        ci, r, c = key
        bx = self.cols_x0 + ci * (self.graphite_w + self.rod_channel_w)
        dx = bx + self._dot_x_off + c * self.dot_spacing + self.dot_spacing // 2
        dy = (self.fuel_top_y + self._dot_y_off
              + r * self.dot_spacing + self.dot_spacing // 2)
        return dx, dy

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------

    def update(self, dt):
        """Advance the neutron-transport simulation by `dt` seconds."""
        if dt <= 0:
            return
        dt = min(dt, 0.05)

        self._f_fissions = 0
        self._f_fission_neutrons = 0
        self._f_losses = 0

        self._spawn_source(dt)
        self._step_neutrons(dt)
        self._regen_fuel(dt)
        self._update_diagnostics(dt)

        self.power_history.append(len(self.neutrons))
        overflow = len(self.power_history) - Physics.POWER_HISTORY_LEN
        if overflow > 0:
            del self.power_history[:overflow]

    def _spawn_source(self, dt):
        """Inject spontaneous-fission source neutrons to seed the chain."""
        expected = Physics.SOURCE_RATE_PER_S * dt
        n = int(expected)
        if self.rng_sim.random() < (expected - n):
            n += 1
        for _ in range(n):
            if len(self.neutrons) >= Physics.MAX_NEUTRONS:
                break
            ci = self.rng_sim.randint(0, self.num_graphite_cols - 1)
            bx = self.cols_x0 + ci * (self.graphite_w + self.rod_channel_w)
            x = bx + self.rng_sim.uniform(0, self.graphite_w)
            y = self.rng_sim.uniform(self.fuel_top_y, self.fuel_bottom_y)
            self.neutrons.append(Neutron(x, y, fast=True, generation=0))

    def _step_neutrons(self, dt):
        """Move every neutron and resolve its interactions for this step."""
        if not self.neutrons:
            return
        n_sub = max(1, int(math.ceil(Physics.FAST_SPEED * dt / 3.0)))
        sub_dt = dt / n_sub
        for _ in range(n_sub):
            spawned = []
            survivors = []
            for nt in self.neutrons:
                nt.advance(sub_dt)
                if not self._interact(nt, sub_dt, spawned):
                    survivors.append(nt)
            self.neutrons = survivors
            if spawned:
                self.neutrons.extend(spawned)
            if len(self.neutrons) > Physics.MAX_NEUTRONS:
                del self.neutrons[Physics.MAX_NEUTRONS:]

    def _interact(self, nt, dt, spawned):
        """Resolve a neutron's interaction with its current material.

        Returns:
            True if the neutron should be removed (absorbed/escaped/fissioned).
        """
        mat = self.material_at(nt.x, nt.y)

        if mat == MATERIAL_AIR:
            self._f_losses += 1
            return True
        if mat == MATERIAL_BORON:
            self._f_losses += 1
            return True
        if mat == MATERIAL_GRAPHITE:
            if nt.fast and self.rng_sim.random() < Physics.GRAPHITE_MODERATION_PER_S * dt:
                nt.moderate()
                nt.scatter(0.3)
            return False
        if mat == MATERIAL_WATER:
            if self.rng_sim.random() < Physics.WATER_ABSORB_PER_S * dt:
                self._f_losses += 1
                return True
            if nt.fast and self.rng_sim.random() < Physics.WATER_MODERATION_PER_S * dt:
                nt.moderate()
            return False
        if mat == MATERIAL_FUEL:
            return self._interact_fuel(nt, dt, spawned)
        return False

    def _interact_fuel(self, nt, dt, spawned):
        """Resolve a neutron inside the fuelled lattice (fission/poisoning)."""
        found = self.fuel_dot_at(nt.x, nt.y)
        if not found:
            return False
        key, dtype = found
        cx, cy = self._dot_center(key)
        if (nt.x - cx) ** 2 + (nt.y - cy) ** 2 > self._collision_r2:
            # Between fuel pins the lattice is graphite moderator, so fast
            # neutrons thermalize here before they can reach a fissile pin.
            if nt.fast and self.rng_sim.random() < Physics.GRAPHITE_MODERATION_PER_S * dt:
                nt.moderate()
            return False

        if dtype == "xenon":
            if not nt.fast:
                self._f_losses += 1
                return True
            return False

        if dtype == "reactive":
            prob = (Physics.THERMAL_FISSION_PROB if not nt.fast
                    else Physics.FAST_FISSION_PROB)
            if self.rng_sim.random() < prob:
                self._do_fission(key, cx, cy, nt.generation, spawned)
                return True

        nt.scatter(0.4)
        return False

    def _do_fission(self, key, cx, cy, parent_gen, spawned):
        """Emit fresh fast neutrons; occasionally leave a xenon poison behind.

        Uranium fuel is abundant, so a fission does not deplete the pin: the
        blue (reactive) dot persists unless a xenon-135 poison is produced,
        which later decays away. This keeps the reactive population alive.
        """
        if self.rng_sim.random() < Physics.XENON_YIELD:
            self.fuel[key] = "xenon"

        lo, hi = Physics.NEUTRONS_PER_FISSION
        nu = self.rng_sim.randint(lo, hi)
        self._f_fissions += 1
        self._f_fission_neutrons += nu

        for _ in range(nu):
            if len(self.neutrons) + len(spawned) >= Physics.MAX_NEUTRONS:
                break
            spawned.append(
                Neutron(cx, cy, fast=True, generation=parent_gen + 1)
            )

    def _regen_fuel(self, dt):
        """Decay xenon and slowly breed fresh reactive uranium.

        This is what keeps a blue (reactive) uranium population present over
        time: spent fuel is gradually replenished and xenon poison decays away,
        so the chain reaction can be sustained rather than burning out.
        """
        p_xe = Physics.XENON_DECAY_PER_S * dt
        p_re = Physics.FUEL_REGEN_PER_S * dt
        rng = self.rng_sim
        for key, t in self.fuel.items():
            if t == "xenon":
                if rng.random() < p_xe:
                    self.fuel[key] = "reactive"
            elif t == "nonreactive":
                if rng.random() < p_re:
                    self.fuel[key] = "reactive"

    def _update_diagnostics(self, dt):
        """Update the smoothed k_eff and reactivity estimates.

        k_eff is estimated from the neutron balance over a sliding window:
            k_eff = (fission neutrons produced) / (fissions + other losses)
                  = nu * P(a neutron causes fission before being lost).
        Reactivity follows as rho = (k - 1) / k, expressed in dollars by
        dividing by the delayed-neutron fraction BETA_EFF (INSAG-7).
        """
        decay = math.exp(-dt / 0.6)
        self._ema_fission_neutrons = self._ema_fission_neutrons * decay + self._f_fission_neutrons
        self._ema_fissions = self._ema_fissions * decay + self._f_fissions
        self._ema_losses = self._ema_losses * decay + self._f_losses

        denom = self._ema_fissions + self._ema_losses
        if denom > 1e-6:
            self.k_eff = self._ema_fission_neutrons / denom
        else:
            self.k_eff = 0.0

        if self.k_eff > 1e-6:
            rho = (self.k_eff - 1.0) / self.k_eff
        else:
            rho = -1.0
        self.reactivity_dollars = rho / Physics.BETA_EFF
        instant_rate = self._f_fissions / dt if dt > 0 else 0.0
        self.fission_rate = self.fission_rate * decay + (1.0 - decay) * instant_rate

    def criticality_state(self):
        """Classify the reactor state from the current reactivity."""
        if self.k_eff <= 1e-6:
            return "Idle"
        d = self.reactivity_dollars
        if d < -0.02:
            return "Subcritical"
        if d > 0.02:
            return "Supercritical"
        return "Critical"

    def set_all_rods(self, p):
        """Set every control rod to normalized insertion `p` (0=out, 1=in)."""
        for rod in self.rods:
            rod.set_normalized_position(p)

    def set_rod(self, i, p):
        """Set control rod `i` to normalized insertion `p`."""
        if 0 <= i < len(self.rods):
            self.rods[i].set_normalized_position(p)

    def get_rod_position(self, i):
        """Return the normalized insertion of control rod `i`."""
        return self.rods[i].position

    def reset(self):
        """Reset fuel composition and clear all neutrons."""
        self._build_fuel_grid()
        self._init_simulation()

    def draw_neutrons(self, surf):
        """Draw all live neutrons on top of the core."""
        for nt in self.neutrons:
            nt.draw(surf)

    def draw(self, surf, font_small):
        """Draw the reactor on the given surface.

        Args:
            surf: Pygame surface to draw on.
            font_small: Small font for labels (reserved for future use).
        """
        self._draw_body(surf)
        self._draw_graphite_and_fuel(surf)
        self._draw_control_rods(surf)
        self.draw_neutrons(surf)

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

            pygame.draw.rect(
                surf,
                ColorPalette.GRAPHITE,
                (bx, self.core_top_y, self.graphite_w, self.graphite_top_h),
            )

            pygame.draw.rect(
                surf,
                ColorPalette.GRAPHITE,
                (bx, self.fuel_bottom_y, self.graphite_w, self.graphite_bottom_h),
            )

            pygame.draw.rect(
                surf,
                ColorPalette.FUEL_BG,
                (bx, self.fuel_top_y, self.graphite_w, self.fuel_h),
            )

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
                else:
                    color = ColorPalette.XENON

                pygame.draw.circle(surf, color, (dx, dy), self.dot_radius)

    def _draw_control_rods(self, surf):
        """Draw all control rods."""
        for rod in self.rods:
            rod.draw(surf)
