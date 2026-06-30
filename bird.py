"""
═══════════════════════════════════════════════════════════════════════
MATHEMATICAL BIRD — Parametric Surface Formulation  (v8 — Vivid)
═══════════════════════════════════════════════════════════════════════

Target: A symmetric bird viewed from front-slightly-above.
Wings form a V-shape (dihedral), curved and swept.
The surface is rendered with GRADIENT COLORING on a dark background.

RULED WING SURFACE:
    S(u, v) = (1−v)·α(u)  +  v·β(u)
where
    α(u) = leading-edge curve    [Cubic Bézier in 3-D]
    β(u) = trailing-edge curve   [Cubic Bézier in 3-D]
    u ∈ [0,1] : span (root→tip)
    v ∈ [0,1] : chord (leading→trailing)

Lines drawn:
    Span-wise:  fix u, vary v  → ribbons along wing chord
    Chord-wise: fix v, vary u  → lines from root to tip

BODY/TORSO:
    Bicubic swept tube along vertical axis (head↔tail)

TAIL:
    Fan of K Bézier curves  γⱼ(t)  spread in azimuth angle

═══════════════════════════════════════════════════════════════════════
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.colors as mcolors
from matplotlib.collections import LineCollection
from mpl_toolkits.mplot3d.art3d import Line3DCollection

# ═══════════════════════════════════════════════════
#  COLOR PALETTES
# ═══════════════════════════════════════════════════

# Wing gradient: deep indigo → electric cyan → golden tip
WING_COLORS = [
    '#1a0533',  # deep purple root
    '#2d1b69',  # indigo
    '#4a2c8a',  # purple
    '#6b3fa0',  # violet
    '#8b5cf6',  # bright violet
    '#7c3aed',  # purple
    '#6366f1',  # indigo
    '#3b82f6',  # blue
    '#06b6d4',  # cyan
    '#14b8a6',  # teal
    '#f59e0b',  # amber tip
    '#f97316',  # orange tip
]

# Body gradient: dark core → luminous highlights
BODY_COLORS = [
    '#1e1b4b',  # deep indigo
    '#312e81',  # indigo
    '#4338ca',  # blue-violet
    '#6366f1',  # indigo
    '#818cf8',  # light indigo
]

# Tail gradient: warm spectrum
TAIL_COLORS = [
    '#7c2d12',  # deep brown
    '#9a3412',  # brown-orange
    '#c2410c',  # orange-red
    '#ea580c',  # orange
    '#f59e0b',  # amber
    '#fbbf24',  # yellow
    '#fde68a',  # light gold
]

# Head spike: fiery
SPIKE_COLORS = [
    '#4338ca',  # indigo base
    '#6366f1',  # violet
    '#a78bfa',  # light violet
    '#c4b5fd',  # lavender
    '#ede9fe',  # pale lavender tip
]

BG_COLOR = '#0a0a1a'        # deep dark blue-black
BG_COLOR_LIGHT = '#f8fafc'  # for light version


# ═══════════════════════════════════════════════════
#  UTILITY: Cubic Bézier
# ═══════════════════════════════════════════════════

def B3(P0, P1, P2, P3, t):
    """Cubic Bézier curve.  t can be scalar or 1-D array."""
    t = np.asarray(t)
    scalar = t.ndim == 0
    t = np.atleast_1d(t)
    t3d = t[:, np.newaxis]
    result = ((1-t3d)**3*P0 + 3*(1-t3d)**2*t3d*P1
              + 3*(1-t3d)*t3d**2*P2 + t3d**3*P3)
    return result[0] if scalar else result

def B2(P0, P1, P2, t):
    """Quadratic Bézier curve.  t can be scalar or 1-D array."""
    t = np.asarray(t)
    scalar = t.ndim == 0
    t = np.atleast_1d(t)
    t3d = t[:, np.newaxis]
    result = (1-t3d)**2*P0 + 2*(1-t3d)*t3d*P1 + t3d**2*P2
    return result[0] if scalar else result


def color_lerp(colors, t):
    """Interpolate through a list of hex colors at parameter t ∈ [0,1]."""
    t = np.clip(t, 0, 1)
    n = len(colors) - 1
    idx = t * n
    i = int(np.floor(idx))
    i = min(i, n - 1)
    frac = idx - i
    c1 = np.array(mcolors.to_rgb(colors[i]))
    c2 = np.array(mcolors.to_rgb(colors[i + 1]))
    return c1 + frac * (c2 - c1)


# ═══════════════════════════════════════════════════
#  WING EDGE CURVES  (3-D: x=lateral, y=depth, z=vertical)
# ═══════════════════════════════════════════════════
#
#  Origin (0,0,0) = body centre.
#  x > 0 → right wing,   z > 0 → up,   y > 0 → forward (toward viewer).
#
#  LEFT WING: x < 0.  Mirror gives right wing.

# Control points for the LEFT wing LEADING EDGE
LL0 = np.array([ 0.00,  0.10,  0.10])  # root, near body
LL1 = np.array([-1.80,  0.05,  0.55])  # inner panel, curving up
LL2 = np.array([-3.80, -0.08,  0.60])  # outer panel
LL3 = np.array([-5.50, -0.20,  0.15])  # wingtip

# Control points for the LEFT wing TRAILING EDGE
LT0 = np.array([ 0.00,  0.10, -0.22])  # root trailing
LT1 = np.array([-1.40,  0.00, -0.05])  # inner trailing
LT2 = np.array([-3.60, -0.12,  0.25])  # outer trailing
LT3 = np.array([-5.40, -0.20,  0.12])  # tip trailing (≈ same as tip leading)


def left_leading(u):
    return B3(LL0, LL1, LL2, LL3, u)

def left_trailing(u):
    return B3(LT0, LT1, LT2, LT3, u)

def mirror_x(p):
    """Reflect a 3-D point or array of points across the x=0 plane."""
    p = np.asarray(p).copy()
    p[..., 0] = -p[..., 0]
    return p

def right_leading(u):
    return mirror_x(left_leading(u))

def right_trailing(u):
    return mirror_x(left_trailing(u))


# ═══════════════════════════════════════════════════
#  WING SURFACE SAMPLING
# ═══════════════════════════════════════════════════

N_SPAN  = 110   # span-wise parameter samples (chord-dir lines)
N_CHORD = 75    # chord-wise parameter samples (span-dir lines)
N_PTS   = 200   # points along each line

u_vals = np.linspace(0, 1, N_PTS)
v_vals = np.linspace(0, 1, N_PTS)


def surface_pt(u, v, lead_fn, trail_fn):
    """S(u,v) = (1-v)·lead(u) + v·trail(u)"""
    L = lead_fn(u)
    T = trail_fn(u)
    return (1-v)*L + v*T


# ═══════════════════════════════════════════════════
#  ROTATION-MINIMIZING FRAME  (for swept body tube)
# ═══════════════════════════════════════════════════

def rmf(gamma):
    n = len(gamma)
    T = np.gradient(gamma, axis=0)
    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-10)
    N = np.zeros((n, 3)); B = np.zeros((n, 3))
    for ref in (np.array([1.,0,0]), np.array([0,1.,0]), np.array([0,0,1.])):
        N0 = np.cross(T[0], ref)
        if np.linalg.norm(N0) > 0.1: break
    N[0] = N0/np.linalg.norm(N0)
    B[0] = np.cross(T[0], N[0])
    for i in range(1, n):
        Ni = N[i-1] - np.dot(N[i-1], T[i])*T[i]
        nrm = np.linalg.norm(Ni)
        N[i] = Ni/nrm if nrm > 1e-10 else N[i-1]
        B[i] = np.cross(T[i], N[i])
        bn = np.linalg.norm(B[i])
        if bn > 1e-10: B[i] /= bn
    return N, B


def draw_tube_3d(ax, gamma, r, n_theta=28, lw=0.32, alpha=0.80,
                 colors=None, glow=False):
    """Render S(t,θ) = γ(t) + r(t)·[N cosθ + B sinθ] with color gradient."""
    if len(gamma) < 3: return
    Nv, Bv = rmf(gamma)
    th = np.linspace(0, 2*np.pi, n_theta)
    ct, st = np.cos(th), np.sin(th)
    n_pts = len(gamma)
    for i in range(n_pts):
        if r[i] < 0.003: continue
        ring = gamma[i] + r[i]*(np.outer(ct, Nv[i]) + np.outer(st, Bv[i]))
        t_param = i / max(n_pts - 1, 1)
        if colors:
            c = color_lerp(colors, t_param)
        else:
            c = 'white'
        ax.plot(ring[:,0], ring[:,1], ring[:,2],
                color=c, lw=lw, alpha=alpha)
        # Glow pass: slightly wider, more transparent
        if glow:
            ax.plot(ring[:,0], ring[:,1], ring[:,2],
                    color=c, lw=lw * 2.5, alpha=alpha * 0.15)


# ═══════════════════════════════════════════════════
#  RENDER FUNCTION (supports multiple styles)
# ═══════════════════════════════════════════════════

def render_bird(filename, bg_color=BG_COLOR, style='dark',
                elev=18, azim=-90, figsize=(14, 9)):
    """Render the full bird with the given style and save to filename."""

    is_dark = (style == 'dark')

    fig = plt.figure(figsize=figsize, facecolor=bg_color)
    ax = fig.add_subplot(111, projection='3d', facecolor=bg_color)
    ax.set_axis_off()

    LW_WING = 0.28 if is_dark else 0.25
    ALF_WING = 0.65 if is_dark else 0.55

    # ─── DRAW WINGS ─────────────────────────────────
    for lead_fn, trail_fn in [
            (left_leading,  left_trailing),
            (right_leading, right_trailing)]:

        # Span lines (fixed u, vary v) — colored by span position
        for idx, u in enumerate(np.linspace(0, 1, N_SPAN)):
            pts = np.array([surface_pt(u, v, lead_fn, trail_fn) for v in v_vals])
            if is_dark:
                c = color_lerp(WING_COLORS, u)
                ax.plot(pts[:,0], pts[:,1], pts[:,2],
                        color=c, lw=LW_WING, alpha=ALF_WING)
                # Glow layer
                ax.plot(pts[:,0], pts[:,1], pts[:,2],
                        color=c, lw=LW_WING * 3, alpha=0.06)
            else:
                ax.plot(pts[:,0], pts[:,1], pts[:,2],
                        color='black', lw=LW_WING, alpha=ALF_WING)

        # Chord lines (fixed v, vary u) — colored by chord position
        for v in np.linspace(0, 1, N_CHORD):
            pts = np.array([surface_pt(u, v, lead_fn, trail_fn) for u in u_vals])
            if is_dark:
                # Color each segment based on its u position
                for seg_i in range(len(pts) - 1):
                    u_param = seg_i / max(len(pts) - 2, 1)
                    c = color_lerp(WING_COLORS, u_param)
                    ax.plot(pts[seg_i:seg_i+2, 0],
                            pts[seg_i:seg_i+2, 1],
                            pts[seg_i:seg_i+2, 2],
                            color=c, lw=LW_WING * 0.8, alpha=ALF_WING * 0.7)
            else:
                ax.plot(pts[:,0], pts[:,1], pts[:,2],
                        color='black', lw=LW_WING, alpha=ALF_WING)

    # ─── BODY TUBE ──────────────────────────────────
    N_BODY = 140
    t_body = np.linspace(0, 1, N_BODY)

    BH0 = np.array([0.00, 0.00,  0.90])
    BH1 = np.array([0.00, 0.05,  0.50])
    BH2 = np.array([0.00, 0.00, -0.15])
    BH3 = np.array([0.00,-0.05, -0.70])

    gamma_body = B3(BH0, BH1, BH2, BH3, t_body)
    r_body = 0.06 + 0.28 * np.sin(np.pi * t_body)**1.2
    r_body = np.maximum(r_body, 0.01)

    body_cols = BODY_COLORS if is_dark else None
    draw_tube_3d(ax, gamma_body, r_body, n_theta=38, lw=0.32,
                 alpha=0.90, colors=body_cols, glow=is_dark)

    # ─── HEAD SPIKE ─────────────────────────────────
    N_SPIKE = 50
    t_spike = np.linspace(0, 1, N_SPIKE)

    HEAD_TOP  = gamma_body[0].copy()
    SPIKE_TIP = HEAD_TOP + np.array([0, 0, 0.45])

    gamma_spike = np.column_stack([
        np.linspace(HEAD_TOP[0], SPIKE_TIP[0], N_SPIKE),
        np.linspace(HEAD_TOP[1], SPIKE_TIP[1], N_SPIKE),
        np.linspace(HEAD_TOP[2], SPIKE_TIP[2], N_SPIKE),
    ])
    r_spike = 0.10 * (1 - t_spike)**1.4
    r_spike = np.maximum(r_spike, 0.002)

    spike_cols = SPIKE_COLORS if is_dark else None
    draw_tube_3d(ax, gamma_spike, r_spike, n_theta=24, lw=0.30,
                 alpha=0.90, colors=spike_cols, glow=is_dark)

    # ─── TAIL FEATHERS ──────────────────────────────
    M_TAIL = 18
    N_TAIL = 120
    t4 = np.linspace(0, 1, N_TAIL)

    TAIL_BASE = gamma_body[-1].copy()

    phi_min_tail = np.radians(200)
    phi_max_tail = np.radians(340)

    L_TAIL_MID  = 2.2
    L_TAIL_SIDE = 0.80

    for j in range(M_TAIL):
        s_j  = j / (M_TAIL - 1)
        phi_j = phi_min_tail + s_j * (phi_max_tail - phi_min_tail)

        L_j = L_TAIL_SIDE + (L_TAIL_MID - L_TAIL_SIDE) * np.sin(np.pi * s_j)

        tip_j = TAIL_BASE + L_j * np.array([
            np.cos(phi_j),
            0.0,
            np.sin(phi_j)
        ])

        ctrl_j = 0.5*(TAIL_BASE + tip_j) + np.array([
            0.10 * L_j * np.cos(phi_j + np.pi/2),
            0.04 * L_j,
            0.10 * L_j * np.sin(phi_j + np.pi/2),
        ])

        gamma_j = B2(TAIL_BASE, ctrl_j, tip_j, t4)

        r_j = np.maximum(0.18*(1 - t4)**0.55 + 0.008, 0.005)

        # Each tail feather gets a slightly different hue
        if is_dark:
            feather_colors = []
            for tc in TAIL_COLORS:
                rgb = np.array(mcolors.to_rgb(tc))
                # Shift hue slightly per feather
                shift = (s_j - 0.5) * 0.15
                rgb = np.clip(rgb + shift * np.array([0.1, -0.05, 0.05]), 0, 1)
                feather_colors.append(mcolors.to_hex(rgb))
        else:
            feather_colors = None

        draw_tube_3d(ax, gamma_j, r_j, n_theta=22, lw=0.32,
                     alpha=0.70, colors=feather_colors, glow=is_dark)

    # ─── CAMERA ─────────────────────────────────────
    ax.view_init(elev=elev, azim=azim)
    ax.set_box_aspect([2.2, 0.6, 1.5])

    plt.tight_layout()
    plt.savefig(filename, dpi=350, bbox_inches='tight',
                facecolor=bg_color, transparent=False)
    plt.close(fig)
    print(f"  ✓ Saved: {filename}")


# ═══════════════════════════════════════════════════
#  GENERATE ALL VIEWS
# ═══════════════════════════════════════════════════

if __name__ == '__main__':
    print("╔══════════════════════════════════════════════╗")
    print("║  MATHEMATICAL BIRD — Rendering Gallery v8   ║")
    print("╚══════════════════════════════════════════════╝")
    print()

    # 1. Hero shot — dark mode, front view
    print("[1/4] Rendering hero shot (dark, front view)...")
    render_bird('mathematical_bird.png',
                bg_color=BG_COLOR, style='dark',
                elev=18, azim=-90, figsize=(14, 9))

    # 2. Three-quarter view — dark mode
    print("[2/4] Rendering 3/4 view (dark)...")
    render_bird('bird_three_quarter.png',
                bg_color=BG_COLOR, style='dark',
                elev=25, azim=-65, figsize=(14, 9))

    # 3. Top-down view — dark mode
    print("[3/4] Rendering top-down view (dark)...")
    render_bird('bird_top_view.png',
                bg_color='#0d1117', style='dark',
                elev=75, azim=-90, figsize=(14, 9))

    # 4. Classic wireframe — light mode
    print("[4/4] Rendering classic wireframe (light)...")
    render_bird('bird_wireframe_classic.png',
                bg_color=BG_COLOR_LIGHT, style='light',
                elev=18, azim=-90, figsize=(14, 9))

    print()
    print("═══ All renders complete! ═══")