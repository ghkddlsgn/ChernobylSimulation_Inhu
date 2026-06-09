"""
Control rod implementation for the RBMK reactor.
"""

import pygame
from config import ColorPalette, MATERIAL_GRAPHITE, MATERIAL_BORON


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
    GAP_LEN = 18
    BORON_LEN = 290
    CASING_LEN = 220

    def __init__(self, channel_x, channel_w, body_top_y, body_bottom_y,
                 visible_top_y):
        """Initialize a control rod.

        Args:
            channel_x: X coordinate of the rod's channel.
            channel_w: Width of the rod's channel.
            body_top_y: Y coordinate of the top of the reactor body.
            body_bottom_y: Y coordinate of the bottom of the reactor body.
            visible_top_y: Y coordinate above which the rod is not drawn.
        """
        self.channel_x = channel_x
        self.channel_w = channel_w
        self.body_top_y = body_top_y
        self.body_bottom_y = body_bottom_y
        self.visible_top_y = visible_top_y
        self.tip_y = body_top_y
        self.set_normalized_position(0.5)

    @property
    def total_length(self):
        """Total length of the control rod in pixels."""
        return self.GRAPHITE_LEN + self.GAP_LEN + self.BORON_LEN + self.CASING_LEN

    def set_normalized_position(self, p):
        """Set the rod position using a normalized value.

        Args:
            p: Normalized position from 0.0 (fully withdrawn) to 1.0 (fully inserted).
        """
        p = max(0.0, min(1.0, p))
        self.position = p
        y_high = self.body_top_y - 5
        y_low = self.body_bottom_y
        self.tip_y = int(y_high + p * (y_low - y_high))

    def section_at_y(self, y):
        """Return which rod section sits at world-y coordinate `y`.

        Returns:
            One of: "graphite", "gap", "boron", "casing", or None if no rod.
        """
        graphite_top = self.tip_y - self.GRAPHITE_LEN
        gap_top = graphite_top - self.GAP_LEN
        boron_top = gap_top - self.BORON_LEN
        casing_top = boron_top - self.CASING_LEN

        if y > self.tip_y or y < casing_top:
            return None
        if y > graphite_top:
            return "graphite"
        if y > gap_top:
            return "gap"
        if y > boron_top:
            return "boron"
        return "casing"

    def draw(self, surf):
        """Draw the control rod on the given surface."""
        cx = self.channel_x + self.channel_w // 2
        rod_w = self.channel_w - 4
        thin_w = max(4, rod_w // 2)

        graphite_top = self.tip_y - self.GRAPHITE_LEN
        gap_top = graphite_top - self.GAP_LEN
        boron_top = gap_top - self.BORON_LEN
        casing_top = boron_top - self.CASING_LEN

        clip_y = self.visible_top_y

        def draw_section(color, top, bottom, width):
            """Draw a rod section between [top, bottom], clipping at clip_y."""
            top = max(top, clip_y)
            if bottom <= top:
                return
            pygame.draw.rect(
                surf, color, (cx - width // 2, top, width, bottom - top),
            )

        draw_section(ColorPalette.ROD_CASING, casing_top, boron_top, thin_w)
        draw_section(ColorPalette.BORON, boron_top, boron_top + self.BORON_LEN, rod_w)
        draw_section(ColorPalette.ROD_CASING, gap_top, gap_top + self.GAP_LEN, thin_w)
        draw_section(ColorPalette.GRAPHITE, graphite_top, graphite_top + self.GRAPHITE_LEN, rod_w)
