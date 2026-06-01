# ChernobylSimulation

An interactive 2D particle simulation of an RBMK-1000 reactor core (the
Chernobyl reactor type), built with `pygame`.

Neutrons are simulated as individual particles: source neutrons seed the chain,
graphite moderates fast neutrons into thermal neutrons, thermal neutrons cause
fission on the blue (reactive) uranium dots producing more fast neutrons, and
the boron sections of the control rods absorb them. Inserting the control rods
absorbs neutrons and kills the chain reaction; withdrawing them lets it grow.

## Run

```bash
python main.py
```

(Requires `pygame`; a virtual environment with it is included under `.venv`.)

## Controls

- **Master slider** moves every control rod together; the numbered sliders move
  one rod each (0 = withdrawn, 100 = fully inserted).
- **Pause / Start** button or `SPACE` toggles the simulation.
- **Reset** button or `R` reloads the fuel and clears all neutrons.
- `ESC` quits.

## Legend

- Blue dot = reactive uranium (fissile), gray = non-fissile, black = xenon poison.
- Filled dark dot = thermal neutron, hollow ring = fast neutron.
- Purple = graphite, green = boron absorber band of the control rod.

## Physics comparison with Chernobyl data

This is a qualitative toy model: absolute power (MW) and neutron flux are not
comparable to a real reactor. Instead the Plots & Diagnostics panel reports
**dimensionless** metrics that *can* be compared with published data:

- **k_eff** (multiplication factor): critical at 1.0.
- **Reactivity** in dollars: `rho = (k_eff - 1) / k_eff`, divided by the
  delayed-neutron fraction `beta_eff = 0.0065`.
- **Criticality state**: Subcritical / Critical / Supercritical.

Reference values shown on screen for comparison of sign and order of magnitude:

- INSAG-7 (IAEA Safety Series 75-INSAG-7, 1992): `beta_eff ≈ 0.0065`, void
  coefficient `+(4–5) beta` for the steady-state refuelling regime.
  https://www-pub.iaea.org/MTCD/publications/PDF/Pub913e_web.pdf
- World Nuclear Association, RBMK Reactors appendix.
  https://world-nuclear.org/information-library/appendices/rbmk-reactors
- EPJ N (2021), "A simplified analysis of the Chernobyl accident": control-rod
  insertion reactivity `+396 pcm` with xenon poisoning vs `-344 pcm` without.
  https://www.epj-n.org/articles/epjn/full_html/2021/01/epjn200018/epjn200018.html

Note: the headline cause of the accident — the positive *void* (steam)
coefficient — is out of scope here (no boiling/steam model). The simulation
focuses on control-rod criticality control and the k_eff / reactivity behaviour.

## Project layout

- `main.py` — application, UI layout, main loop, plots and diagnostics.
- `reactor.py` — core geometry, material lookup, neutron-transport `update()`.
- `neutron.py` — the `Neutron` particle.
- `control_rod.py` — control-rod geometry and positioning.
- `ui_panel.py` — panel, slider and button widgets.
- `config.py` — colors and the `Physics` constants (with references).
