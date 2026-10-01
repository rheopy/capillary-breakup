"""From neck size vs time to rheology.

Newtonian filament thinning
---------------------------
Close to breakup a Newtonian filament follows the Papageorgiou (1995)
similarity solution: the minimum radius shrinks linearly in time,

    R(t) = 0.0709 * (sigma / eta) * (t_c - t)

so a linear fit of radius vs time just before breakup gives the slope
``m = -0.0709 * sigma / eta`` and therefore::

    eta = 0.0709 * sigma / |m|

with ``sigma`` the surface tension. The breakup time ``t_c`` comes from
the same fit (or from the last connected frame).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PAPAGEORGIOU_PREFACTOR = 0.0709


def to_radius(df: pd.DataFrame, mm_per_px: float) -> pd.DataFrame:
    """Add ``radius_mm`` (half the measured neck width) to a measurement frame."""
    out = df.copy()
    out["radius_mm"] = out["neck_px"] / 2.0 * mm_per_px
    return out


def find_breakup(df: pd.DataFrame) -> int:
    """Frame index of the last connected (nonzero neck) measurement."""
    nz = df.index[df["neck_px"] > 0]
    if len(nz) == 0:
        raise ValueError("no connected frames in the measurement")
    return int(nz[-1])


def fit_linear_thinning(
    df: pd.DataFrame,
    *,
    radius_col: str = "radius_mm",
    n_points: int = 30,
    end_offset: int = 2,
) -> dict:
    """Linear fit of radius vs time approaching breakup.

    Fits ``n_points`` connected frames, stopping ``end_offset`` frames
    before the last connected one to skip the pixel-quantization noise
    right at pinch-off.

    Returns a dict with ``slope`` (radius units per second, negative),
    ``intercept``, ``t_c`` (extrapolated breakup time, s), ``r_squared``
    and the fitted ``n_points``.
    """
    breakup = find_breakup(df)
    use = df.loc[:breakup]
    use = use[use["neck_px"] > 0]
    if end_offset:
        use = use.iloc[: len(use) - end_offset]
    use = use.tail(n_points)
    if len(use) < 3:
        raise ValueError("not enough connected frames for a fit")
    t = use["time_s"].to_numpy(dtype=float)
    r = use[radius_col].to_numpy(dtype=float)
    slope, intercept = np.polyfit(t, r, 1)
    r_pred = slope * t + intercept
    ss_res = float(np.sum((r - r_pred) ** 2))
    ss_tot = float(np.sum((r - r.mean()) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "t_c": float(-intercept / slope) if slope != 0 else float("nan"),
        "r_squared": float(r_squared),
        "n_points": len(use),
        "t_start": float(t[0]),
        "t_end": float(t[-1]),
    }


def newtonian_viscosity(
    slope_per_s: float, surface_tension_mN_per_m: float
) -> float:
    """Shear viscosity (Pa.s) from the thinning slope via Papageorgiou.

    ``slope_per_s`` is dR/dt in mm/s (negative); ``surface_tension_mN_per_m``
    is the liquid's surface tension in mN/m.
    """
    sigma = surface_tension_mN_per_m / 1000.0  # N/m
    slope_m_per_s = abs(slope_per_s) / 1000.0  # m/s
    if slope_m_per_s == 0:
        raise ValueError("zero thinning slope")
    return PAPAGEORGIOU_PREFACTOR * sigma / slope_m_per_s


def thinning_summary(
    df: pd.DataFrame,
    *,
    mm_per_px: float,
    fps: float | None = None,
    surface_tension_mN_per_m: float | None = None,
    n_points: int = 20,
) -> dict:
    """One-call summary: radius series + breakup + linear fit (+ viscosity).

    Returns a dict with the radius DataFrame (``df``), the ``breakup``
    frame, the ``fit`` dict, and ``viscosity_Pa_s`` when a surface tension
    is supplied.
    """
    rdf = to_radius(df, mm_per_px)
    breakup = find_breakup(rdf)
    fit = fit_linear_thinning(rdf, n_points=n_points)
    out = {"df": rdf, "breakup": breakup, "fit": fit, "viscosity_Pa_s": None}
    if surface_tension_mN_per_m is not None:
        out["viscosity_Pa_s"] = newtonian_viscosity(
            fit["slope"], surface_tension_mN_per_m
        )
    return out
