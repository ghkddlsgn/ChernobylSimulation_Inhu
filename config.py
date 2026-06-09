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
    """Dark control-room palette matching the matplotlib plot theme."""
    # Chrome — dark navy matching plotter fig_bg / axes_bg
    APP_BG          = (20,  20,  38 )
    PANEL_BG        = (22,  33,  62 )
    PANEL_BORDER    = (42,  42,  74 )
    TEXT            = (224, 224, 224)
    MUTED           = (136, 136, 153)

    # Reactor materials
    WATER           = (40,  85,  115)
    WATER_OUTLINE   = (55,  115, 145)
    WATER_HOT       = (210, 70,  55 )
    STEAM           = (175, 170, 188)
    GRAPHITE        = (90,  30,  115)
    BORON           = (80,  200, 30 )
    ROD_CASING      = (90,  30,  115)

    FUEL_BG         = (35,  80,  110)
    U_REACTIVE      = (80,  155, 255)
    U_NONREACTIVE   = (110, 110, 120)
    XENON           = (65,  65,  78 )

    # Neutrons — bright so they read on the dark reactor background
    NEUTRON_THERMAL = (150, 210, 255)
    NEUTRON_FAST    = (255, 200, 65 )

    # Live plot panel
    PLOT_BG         = (22,  33,  62 )
    PLOT_GRID       = (42,  42,  74 )
    PLOT_LINE       = (210, 70,  60 )
    PLOT_REF        = (102, 102, 119)

    # Controls
    SLIDER_TRACK    = (42,  42,  74 )
    SLIDER_FILL     = (74,  140, 212)
    SLIDER_KNOB     = (210, 70,  60 )
    BUTTON_BG       = (30,  45,  85 )
    BUTTON_BG_HOVER = (50,  70,  120)
    BUTTON_BORDER   = (60,  80,  130)

    # Criticality states
    STATE_SUB       = (70,  140, 220)
    STATE_CRIT      = (40,  160, 90 )
    STATE_SUPER     = (210, 70,  60 )


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

    HISTORY_SAMPLE_FRAMES = 6  # sample every ~0.1 s at 60 FPS
