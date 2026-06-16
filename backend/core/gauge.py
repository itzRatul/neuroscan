"""
NeuroScan — Gauge Chart Generator
===================================
Notebook: Stroke_detection_V_08.ipynb — Section 8 Cell 3

draw_gauge() taken directly from the notebook.
Produces a semicircular gauge with GREEN / ORANGE / RED zones and a needle.
Dark background (#0f0f1a) matching notebook style.
"""

import io
import logging
import numpy as np
import matplotlib
matplotlib.use('Agg')   # Non-interactive backend — required for server-side use
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# draw_gauge — hbubu notebook Section 8 Cell 3
# Source: Stroke_detection_V_08.ipynb — Section 8 Cell 3
# ─────────────────────────────────────────────────────────────────────────────
def draw_gauge(risk_prob: float, ax, prediction: dict) -> None:
    """
    Draw a semicircular gauge chart on the given matplotlib Axes.

    Taken directly from Stroke_detection_V_08.ipynb Section 8 Cell 3.

    Parameters
    ----------
    risk_prob  : float  — probability in [0, 1]
    ax         : matplotlib Axes
    prediction : dict   — output of predict_stroke_risk() for color_hint
    """
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-0.22, 1.35)
    ax.set_aspect('equal')
    ax.axis('off')

    # Arc zones (start_deg, end_deg, color, label)
    zones = [
        (180, 135, '#27ae60', 'LOW\n< 25%'),
        (135,  81, '#f39c12', 'MODERATE\n25-55%'),
        ( 81,   0, '#e74c3c', 'HIGH\n> 55%'),
    ]
    for sd, ed, col, lbl in zones:
        th = np.linspace(np.radians(sd), np.radians(ed), 120)
        ro, ri = 1.0, 0.60
        xs = np.concatenate([ro * np.cos(th), ri * np.cos(th[::-1])])
        ys = np.concatenate([ro * np.sin(th), ri * np.sin(th[::-1])])
        ax.fill(xs, ys, color=col, alpha=0.88, zorder=2)
        mt = np.radians((sd + ed) / 2)
        ax.text(
            0.8 * np.cos(mt), 0.8 * np.sin(mt), lbl,
            ha='center', va='center', fontsize=8.5,
            color='white', fontweight='bold', zorder=4, multialignment='center',
        )

    # Tick marks
    for ang_pct in np.linspace(0, 100, 11):
        ang = np.radians(180 - ang_pct * 1.8)
        ax.plot(
            [0.62 * np.cos(ang), 1.02 * np.cos(ang)],
            [0.62 * np.sin(ang), 1.02 * np.sin(ang)],
            'w-', lw=1.2, alpha=0.4, zorder=3,
        )
        if ang_pct % 25 == 0:
            ax.text(
                1.15 * np.cos(ang), 1.15 * np.sin(ang),
                f'{ang_pct:.0f}%',
                ha='center', va='center', fontsize=7.5, color='#bbb',
            )

    # Needle with shadow
    na = np.radians(180 - risk_prob * 180)
    nl = 0.85
    nx, ny = nl * np.cos(na), nl * np.sin(na)
    ax.plot([0, nx + 0.01], [0, ny - 0.01], color='#333', lw=4, zorder=5, solid_capstyle='round')
    ax.annotate(
        '', xy=(nx, ny), xytext=(0, 0),
        arrowprops=dict(arrowstyle='->', color='white', lw=3.2, mutation_scale=20),
        zorder=6,
    )
    ax.add_patch(plt.Circle((0, 0), 0.075, color='white',   zorder=7))
    ax.add_patch(plt.Circle((0, 0), 0.045, color='#1a1a2e', zorder=8))

    # Percentage readout
    color_map = {'green': '#2ecc71', 'orange': '#f39c12', 'red': '#e74c3c'}
    tcol = color_map.get(prediction['color_hint'], '#2ecc71')

    ax.text(0, -0.05, f'{risk_prob * 100:.1f}%',
            ha='center', va='top', fontsize=30,
            fontweight='bold', color=tcol, zorder=9)
    ax.text(0, -0.14, 'Overall Asymmetry Score',
            ha='center', va='top', fontsize=9, color='#aaa', zorder=9)


def generate_gauge_bytes(prediction: dict, dpi: int = 150) -> bytes:
    """
    Generate gauge chart PNG and return as bytes.

    Parameters
    ----------
    prediction : dict — output of predict_stroke_risk()
    dpi        : int  — output resolution

    Returns
    -------
    bytes : PNG image bytes
    """
    risk_prob  = prediction['probability']
    risk_label = prediction['risk_level'].split('—')[0].strip()

    fig, ax = plt.subplots(figsize=(9, 5.8))
    fig.patch.set_facecolor('#0f0f1a')
    ax.set_facecolor('#0f0f1a')

    draw_gauge(risk_prob, ax, prediction)

    fig.suptitle(
        f"Asymmetry Score Gauge  |  {risk_label}\n"
        f"Thresholds: FAST/BEFAST Protocol",
        color='white', fontsize=12,
    )
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, dpi=dpi, bbox_inches='tight', facecolor='#0f0f1a', format='png')
    plt.close(fig)
    buf.seek(0)
    return buf.read()
