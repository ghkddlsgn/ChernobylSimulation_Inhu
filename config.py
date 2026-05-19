"""
Configuration and constants for the RBMK Reactor Simulation.
"""

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
FPS = 60

MATERIAL_WATER = "water"
MATERIAL_GRAPHITE = "graphite"
MATERIAL_BORON = "boron"
MATERIAL_FUEL = "fuel"
MATERIAL_AIR = "air"


class ColorPalette:
    """Color palette, picked to echo the reactor diagram."""
    APP_BG = (235, 235, 240)
    PANEL_BG = (250, 250, 253)
    PANEL_BORDER = (200, 200, 210)
    TEXT = (40, 40, 50)
    MUTED = (140, 140, 150)

    WATER = (181, 213, 219)
    WATER_OUTLINE = (130, 170, 180)
    GRAPHITE = (72, 24, 92)
    BORON = (76, 187, 23)
    ROD_CASING = (72, 24, 92)

    FUEL_BG = (195, 215, 222)
    U_REACTIVE = (66, 130, 230)
    U_NONREACTIVE = (165, 165, 170)
    XENON = (35, 35, 40)
