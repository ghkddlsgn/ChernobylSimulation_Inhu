"""
plotter.py — Offline matplotlib report generation for the RBMK simulation.

Must be imported before pygame initialises (or after pygame.quit()) because
matplotlib.use('Agg') is set here to avoid any display-window conflicts.
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# Theme — dark Chernobyl control-room palette matching the app's ColorPalette
# ---------------------------------------------------------------------------
_T = dict(
    fig_bg      = '#1a1a2e',
    axes_bg     = '#16213e',
    grid_color  = '#2a2a4a',
    text_color  = '#e0e0e0',
    muted_color = '#888899',
    line        = '#d24646',   # matches PLOT_LINE (210, 70, 60)
    line_fill   = '#d24646',
    zone_sub    = '#1e3a5f',   # darkened STATE_SUB blue
    zone_crit   = '#1a4a2a',   # darkened STATE_CRIT green
    zone_super  = '#4a1a1a',   # darkened STATE_SUPER red
    ref         = '#666677',
    bar_cool    = '#4a8cd4',
    bar_hot     = '#d24646',
    danger      = '#e05c3a',
)

plt.rcParams.update({
    'figure.facecolor' : _T['fig_bg'],
    'axes.facecolor'   : _T['axes_bg'],
    'axes.edgecolor'   : _T['grid_color'],
    'axes.labelcolor'  : _T['text_color'],
    'axes.grid'        : True,
    'grid.color'       : _T['grid_color'],
    'grid.linewidth'   : 0.7,
    'xtick.color'      : _T['muted_color'],
    'ytick.color'      : _T['muted_color'],
    'text.color'       : _T['text_color'],
    'legend.facecolor' : '#22224a',
    'legend.edgecolor' : _T['grid_color'],
    'font.family'      : 'monospace',
    'font.size'        : 9,
    'lines.linewidth'  : 1.8,
})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_plots(reactor, output_dir: str) -> list[str]:
    """Generate and save all simulation plots to output_dir.

    Returns a list of absolute file paths for every PNG written,
    or an empty list if the simulation was never run.
    """
    if not reactor.history_time:
        print("[plotter] No history data — simulation was never run. Skipping plots.")
        return []

    os.makedirs(output_dir, exist_ok=True)

    t = reactor.history_time
    saved = [
        _plot_neutrons(t, reactor.history_neutrons, output_dir),
        _plot_keff(t, reactor.history_k_eff, output_dir),
        _plot_reactivity(t, reactor.history_reactivity, output_dir),
        _plot_void(t, reactor.history_void, output_dir),
        _plot_fission_rate(t, reactor.history_fission_rate, output_dir),
        _plot_channel_temps(reactor.history_col_temp, reactor.num_fuel_cols, output_dir),
        _plot_overview(reactor, output_dir),
    ]
    return saved


# ---------------------------------------------------------------------------
# Axes-level draw helpers (shared by individual plots and the overview)
# ---------------------------------------------------------------------------

def _style(ax, title, xlabel, ylabel):
    ax.set_title(title, color=_T['text_color'], fontsize=10, pad=6)
    ax.set_xlabel(xlabel, color=_T['muted_color'], fontsize=8)
    ax.set_ylabel(ylabel, color=_T['muted_color'], fontsize=8)
    ax.tick_params(colors=_T['muted_color'], labelsize=7)
    for spine in ax.spines.values():
        spine.set_edgecolor(_T['grid_color'])


def _savefig(fig, path: str) -> str:
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=_T['fig_bg'])
    plt.close(fig)
    return os.path.abspath(path)


def _draw_neutrons_ax(ax, t, neutrons):
    ax.plot(t, neutrons, color=_T['line'])
    ax.fill_between(t, neutrons, alpha=0.15, color=_T['line_fill'])
    _style(ax, 'Neutron Population vs Time', 'Simulation time (s)', 'Neutron count')


def _draw_keff_ax(ax, t, k_eff):
    if k_eff:
        ymax = max(max(k_eff) * 1.05, 1.1)
    else:
        ymax = 1.5
    ax.axhspan(0.0,  0.98,  alpha=0.20, color=_T['zone_sub'],   label='Subcritical')
    ax.axhspan(0.98, 1.02,  alpha=0.28, color=_T['zone_crit'],  label='Critical band')
    ax.axhspan(1.02, ymax,  alpha=0.18, color=_T['zone_super'], label='Supercritical')
    ax.axhline(1.0, color=_T['ref'], lw=1.0, ls='--', label='k = 1.0')
    ax.plot(t, k_eff, color=_T['line'])
    ax.set_ylim(bottom=0.0)
    ax.legend(fontsize=7, loc='upper left')
    _style(ax, 'k_eff vs Time', 'Simulation time (s)', 'k_eff')


def _draw_reactivity_ax(ax, t, reactivity):
    if reactivity:
        ymin = min(min(reactivity) * 1.05, -0.2)
        ymax = max(max(reactivity) * 1.05,  0.2)
    else:
        ymin, ymax = -1.0, 1.0
    ax.axhspan(ymin, 0.0,  alpha=0.15, color=_T['zone_sub'],   label='Subcritical (ρ < 0)')
    ax.axhspan(0.0,  ymax, alpha=0.15, color=_T['zone_super'], label='Supercritical (ρ > 0)')
    ax.axhline(0.0, color=_T['ref'], lw=1.0, ls='--', label='ρ = 0 (critical)')
    ax.plot(t, reactivity, color=_T['line'])
    ax.legend(fontsize=7, loc='upper left')
    _style(ax, 'Reactivity vs Time', 'Simulation time (s)', 'Reactivity ($)')


def _draw_void_ax(ax, t, void):
    void_pct = [v * 100.0 for v in void]
    ax.axhspan(50.0, 100.0, alpha=0.15, color=_T['zone_super'], label='Danger zone (> 50%)')
    ax.axhline(50.0, color=_T['danger'], lw=1.0, ls='--', label='50% danger threshold')
    ax.plot(t, void_pct, color=_T['line'])
    ax.set_ylim(0, 105)
    ax.legend(fontsize=7, loc='upper left')
    _style(ax, 'Average Steam Void Fraction vs Time', 'Simulation time (s)', 'Void fraction (%)')


def _draw_fission_ax(ax, t, fission_rate):
    ax.plot(t, fission_rate, color=_T['line'])
    ax.fill_between(t, fission_rate, alpha=0.12, color=_T['line_fill'])
    _style(ax, 'Fission Rate vs Time', 'Simulation time (s)', 'Fissions / second')


def _draw_channel_temps_ax(ax, history_col_temp, num_cols):
    final = history_col_temp[-1] if history_col_temp else [0.0] * num_cols
    x = list(range(num_cols))
    max_t = max(final) if max(final) > 0 else 1.0
    colors = []
    for temp in final:
        frac = min(temp / max_t, 1.0)
        # Interpolate: cool blue (#4a8cd4) → hot red (#d24646)
        r = int(0x4a + (0xd2 - 0x4a) * frac)
        g = int(0x8c + (0x46 - 0x8c) * frac)
        b = int(0xd4 + (0x46 - 0xd4) * frac)
        colors.append(f'#{r:02x}{g:02x}{b:02x}')
    ax.bar(x, final, color=colors, edgecolor=_T['grid_color'], linewidth=0.6)
    ax.axhline(0.45, color=_T['ref'],    lw=1.0, ls='--', label='Boiling point (0.45)')
    ax.axhline(1.3,  color=_T['danger'], lw=1.0, ls='--', label='Full void threshold (1.3)')
    ax.set_xticks(x)
    ax.set_xticklabels([f'Ch{i + 1}' for i in x], fontsize=7)
    ax.legend(fontsize=7)
    _style(ax, 'Channel Temperatures (Final Snapshot)', 'Fuel channel', 'Temperature (normalised)')


# ---------------------------------------------------------------------------
# Individual plot files
# ---------------------------------------------------------------------------

def _plot_neutrons(t, neutrons, output_dir):
    fig, ax = plt.subplots(figsize=(8, 4))
    _draw_neutrons_ax(ax, t, neutrons)
    return _savefig(fig, os.path.join(output_dir, '1_neutrons.png'))


def _plot_keff(t, k_eff, output_dir):
    fig, ax = plt.subplots(figsize=(8, 4))
    _draw_keff_ax(ax, t, k_eff)
    return _savefig(fig, os.path.join(output_dir, '2_keff.png'))


def _plot_reactivity(t, reactivity, output_dir):
    fig, ax = plt.subplots(figsize=(8, 4))
    _draw_reactivity_ax(ax, t, reactivity)
    return _savefig(fig, os.path.join(output_dir, '3_reactivity.png'))


def _plot_void(t, void, output_dir):
    fig, ax = plt.subplots(figsize=(8, 4))
    _draw_void_ax(ax, t, void)
    return _savefig(fig, os.path.join(output_dir, '4_void.png'))


def _plot_fission_rate(t, fission_rate, output_dir):
    fig, ax = plt.subplots(figsize=(8, 4))
    _draw_fission_ax(ax, t, fission_rate)
    return _savefig(fig, os.path.join(output_dir, '5_fission_rate.png'))


def _plot_channel_temps(history_col_temp, num_cols, output_dir):
    fig, ax = plt.subplots(figsize=(9, 4))
    _draw_channel_temps_ax(ax, history_col_temp, num_cols)
    return _savefig(fig, os.path.join(output_dir, '6_channel_temps.png'))


def _plot_overview(reactor, output_dir):
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(
        'RBMK-1000 Simulation — Session Overview',
        color=_T['text_color'], fontsize=13, fontweight='bold',
    )
    t = reactor.history_time
    _draw_neutrons_ax(axes[0, 0], t, reactor.history_neutrons)
    _draw_keff_ax(axes[0, 1], t, reactor.history_k_eff)
    _draw_reactivity_ax(axes[0, 2], t, reactor.history_reactivity)
    _draw_void_ax(axes[1, 0], t, reactor.history_void)
    _draw_fission_ax(axes[1, 1], t, reactor.history_fission_rate)
    _draw_channel_temps_ax(axes[1, 2], reactor.history_col_temp, reactor.num_fuel_cols)
    fig.tight_layout()
    return _savefig(fig, os.path.join(output_dir, '0_overview.png'))
