"""
Neutron particle for the RBMK reactor simulation.
"""

import math
import random
import pygame
from config import ColorPalette, Physics


class Neutron:
    """A single neutron travelling through the reactor core.

    A neutron is either *fast* (just born from fission, high speed, weak
    fission cross-section) or *thermal* (moderated by graphite, slow, strong
    fission cross-section). The simulation tracks a generation index so that
    the multiplication factor k_eff can be estimated downstream.
    """

    __slots__ = ("x", "y", "vx", "vy", "fast", "generation")

    def __init__(self, x, y, angle=None, fast=True, generation=0):
        """Initialize a neutron.

        Args:
            x, y: World spawn coordinates.
            angle: Travel direction in radians. Random if None.
            fast: True for a fast neutron, False for a thermal one.
            generation: Fission generation index (source neutrons are 0).
        """
        self.x = float(x)
        self.y = float(y)
        self.fast = fast
        self.generation = generation
        if angle is None:
            angle = random.uniform(0, 2 * math.pi)
        self._set_direction(angle)

    def _set_direction(self, angle):
        """Point the neutron along `angle` at its energy-appropriate speed."""
        speed = Physics.FAST_SPEED if self.fast else Physics.THERMAL_SPEED
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def moderate(self):
        """Slow a fast neutron to thermal energy, keeping its heading."""
        if not self.fast:
            return
        self.fast = False
        angle = math.atan2(self.vy, self.vx)
        self._set_direction(angle)

    def scatter(self, max_rad=0.5):
        """Randomly perturb the travel direction (elastic scattering)."""
        angle = math.atan2(self.vy, self.vx) + random.uniform(-max_rad, max_rad)
        self._set_direction(angle)

    def advance(self, dt):
        """Move the neutron forward by `dt` seconds."""
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surf):
        """Draw the neutron: thermal as a filled dot, fast as a hollow ring."""
        pos = (int(self.x), int(self.y))
        if self.fast:
            pygame.draw.circle(surf, ColorPalette.NEUTRON_FAST, pos, 3, 1)
        else:
            pygame.draw.circle(surf, ColorPalette.NEUTRON_THERMAL, pos, 3)
