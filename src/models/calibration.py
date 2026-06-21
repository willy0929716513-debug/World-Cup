"""
Probability calibration for ensemble output.

Applies simple linear calibration (Platt scaling) learned from WC2026 results.
Calibration parameters are stored in data/calibration.json.

If calibration data is not available, returns probabilities unchanged.
"""
from __future__ import annotations
import json
import os
from typing import Optional

_CALIB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../data/calibration.json")
)

_CALIB_CACHE: Optional[dict] = None


def _load_calibration() -> Optional[dict]:
    global _CALIB_CACHE
    if _CALIB_CACHE is not None:
        return _CALIB_CACHE
    if not os.path.exists(_CALIB_PATH):
        return None
    try:
        with open(_CALIB_PATH, "r", encoding="utf-8") as f:
            _CALIB_CACHE = json.load(f)
        return _CALIB_CACHE
    except Exception:
        return None


def reset_cache() -> None:
    """Force reload of calibration parameters (useful for testing)."""
    global _CALIB_CACHE
    _CALIB_CACHE = None


def calibrate(
    p_home: float,
    p_draw: float,
    p_away: float,
) -> tuple[float, float, float]:
    """
    Apply learned calibration to ensemble probabilities.

    Loads linear calibration (alpha, beta per class) from data/calibration.json.
    If calibration data is unavailable, returns (p_home, p_draw, p_away) unchanged.

    After applying per-class linear transforms, renormalises to sum to 1.
    """
    calib = _load_calibration()
    if calib is None:
        return p_home, p_draw, p_away

    try:
        # Apply per-class linear transform: calibrated_p = alpha * p + beta
        alpha_h = calib.get("alpha_home", 1.0)
        beta_h  = calib.get("beta_home",  0.0)
        alpha_d = calib.get("alpha_draw", 1.0)
        beta_d  = calib.get("beta_draw",  0.0)
        alpha_a = calib.get("alpha_away", 1.0)
        beta_a  = calib.get("beta_away",  0.0)

        # Dampen calibration: 40% calibrated signal + 60% raw (prevents overcorrection
        # when trained on small WC samples where away wins are underrepresented)
        DAMPING = 0.40
        ch = DAMPING * (alpha_h * p_home + beta_h) + (1 - DAMPING) * p_home
        cd = DAMPING * (alpha_d * p_draw + beta_d) + (1 - DAMPING) * p_draw
        ca = DAMPING * (alpha_a * p_away + beta_a) + (1 - DAMPING) * p_away

        # Minimum 4% for each outcome — no team should ever be below 4%
        ch = max(0.04, ch)
        cd = max(0.04, cd)
        ca = max(0.04, ca)

        total = ch + cd + ca
        return ch / total, cd / total, ca / total

    except Exception:
        return p_home, p_draw, p_away
