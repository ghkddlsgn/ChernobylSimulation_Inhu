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
    WATER_HOT = (205, 70, 55)
    STEAM = (228, 222, 226)
    GRAPHITE = (72, 24, 92)
    BORON = (76, 187, 23)
    ROD_CASING = (72, 24, 92)

    FUEL_BG = (195, 215, 222)
    U_REACTIVE = (66, 130, 230)
    U_NONREACTIVE = (165, 165, 170)
    XENON = (35, 35, 40)

    NEUTRON_THERMAL = (30, 30, 35)
    NEUTRON_FAST = (90, 90, 100)

    PLOT_BG = (245, 246, 250)
    PLOT_GRID = (220, 222, 230)
    PLOT_LINE = (210, 70, 60)
    PLOT_REF = (150, 150, 160)

    SLIDER_TRACK = (210, 213, 222)
    SLIDER_FILL = (120, 70, 150)
    SLIDER_KNOB = (72, 24, 92)
    BUTTON_BG = (225, 227, 235)
    BUTTON_BG_HOVER = (210, 213, 225)
    BUTTON_BORDER = (180, 183, 195)

    STATE_SUB = (70, 140, 220)
    STATE_CRIT = (40, 160, 90)
    STATE_SUPER = (210, 70, 60)


class Physics:
    """Neutronics parameters for the toy particle simulation.

    These are tuned for plausible *qualitative* behaviour (correct signs and
    relative magnitudes), not absolute reactor values. Dimensionless metrics
    (k_eff, reactivity in dollars) are what we compare against published
    Chernobyl data.

    References for the comparison targets:
      * INSAG-7 (IAEA Safety Series 75-INSAG-7, 1992): beta_eff ~ 0.0065,
        void coefficient +(4-5) beta for the steady-state refuelling regime.
      * EPJ N (2021), "A simplified analysis of the Chernobyl accident":
        control-rod insertion reactivity +396 pcm (with xenon poisoning) vs
        -344 pcm (without).
      * World Nuclear Association, RBMK Reactors appendix.
    """

    BETA_EFF = 0.0065

    FAST_SPEED = 260.0
    THERMAL_SPEED = 120.0

    GRAPHITE_MODERATION_PER_S = 9.0
    WATER_MODERATION_PER_S = 1.2
    WATER_ABSORB_PER_S = 1.7

    # Coolant water *inside* the fuel channel absorbs neutrons between the fuel
    # pins. This absorption is scaled by (1 - void): when the coolant boils to
    # steam, the absorption drops and reactivity rises -> the positive void
    # coefficient. This is the dominant void-feedback term.
    FUEL_COOLANT_ABSORB_PER_S = 1.9

    # Control-rod worth over the fuel it borders. A boron rod doesn't only
    # absorb neutrons that wander into its own thin channel: when inserted it
    # depresses the neutron flux in the adjacent fuel columns too. This term is
    # applied per bordering rod whose boron section covers the neutron's height,
    # and is what gives a fully inserted rod the authority to override even a
    # fully voided column and guarantee shutdown.
    ROD_FUEL_ABSORB_PER_S = 8.5

    THERMAL_FISSION_PROB = 0.92
    FAST_FISSION_PROB = 0.05
    NEUTRONS_PER_FISSION = (2, 3)
    XENON_YIELD = 0.05
    # Fraction of fissions that visibly burn the fissile pin away
    # (reactive -> nonreactive). Makes the chain reaction visible while
    # _regen_fuel breeds fresh fuel back to hold the equilibrium fraction.
    BURNUP_YIELD = 0.12

    SOURCE_RATE_PER_S = 9.0

    XENON_DECAY_PER_S = 0.04
    FUEL_REGEN_PER_S = 0.15

    # Equilibrium fissile (reactive/blue) fraction of the fuel lattice. Real
    # low-enriched fuel is mostly non-fissile U-238, so only a fraction of the
    # dots are reactive. _regen_fuel holds the lattice near this value instead
    # of letting every dot breed into fissile uranium (which would make each
    # column wildly over-reactive and able to self-sustain with the rods in).
    TARGET_REACTIVE_FRAC = 0.28

    # Water / void mechanism -- the source of the POSITIVE void coefficient
    # that drove the Chernobyl excursion. Fissions heat the coolant water in
    # each fuel channel; once it boils to steam (void), it absorbs far fewer
    # neutrons, which raises reactivity and produces more power -> more heat
    # -> more void: a self-amplifying (positive feedback) runaway, unless the
    # boron control rods hold absorption up.
    WATER_HEAT_PER_FISSION = 0.035
    WATER_COOL_PER_S = 0.5
    WATER_BOIL_T = 0.45
    WATER_VOID_FULL_T = 1.3
    FLUX_TAU_S = 0.5

    MAX_NEUTRONS = 2600

    POWER_HISTORY_LEN = 600
