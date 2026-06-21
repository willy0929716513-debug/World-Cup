"""
ML model (LogisticRegression) for football match prediction.

Despite the filename (kept for historical reasons), this uses scikit-learn's
LogisticRegression which is more stable than LightGBM on small datasets and
requires no extra binary dependency.

Features computed from two TeamData objects:
  elo_diff       : home.elo - away.elo
  spi_diff       : home.spi - away.spi
  xg_diff        : home.attack.xg_per_game - away.attack.xg_per_game
  xga_diff       : home.defense.xga_per_game - away.defense.xga_per_game
  ppda_ratio     : away.ppda / home.ppda  (>1 = home presses harder)
  field_tilt_diff: home.field_tilt - away.field_tilt

Trained coefficients are stored in data/ml_coefficients.json.
If that file does not exist (first CI run), falls back to a statistical
approximation based on ELO difference alone.
"""
from __future__ import annotations
import json
import math
import os
from typing import Optional

import numpy as np

from src.data.structures import TeamData, ModelResult
from .dixon_coles import score_matrix as dc_matrix

_COEFF_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../data/ml_coefficients.json")
)

# Cache loaded coefficients
_MODEL_CACHE: Optional[dict] = None


def _load_model() -> Optional[dict]:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    if not os.path.exists(_COEFF_PATH):
        return None
    try:
        with open(_COEFF_PATH, "r", encoding="utf-8") as f:
            _MODEL_CACHE = json.load(f)
        return _MODEL_CACHE
    except Exception:
        return None


def reset_cache() -> None:
    """Force reload of model coefficients (useful for testing)."""
    global _MODEL_CACHE
    _MODEL_CACHE = None


def _extract_features(home: TeamData, away: TeamData) -> np.ndarray:
    """Return a (1, 6) feature array for the given matchup."""
    elo_diff = home.elo_rating - away.elo_rating
    spi_diff = home.spi_rating - away.spi_rating
    xg_diff = home.attack.xg_per_game - away.attack.xg_per_game
    xga_diff = home.defense.xga_per_game - away.defense.xga_per_game
    home_ppda = max(home.advanced.ppda, 0.1)
    away_ppda = max(away.advanced.ppda, 0.1)
    ppda_ratio = away_ppda / home_ppda
    field_tilt_diff = home.advanced.field_tilt - away.advanced.field_tilt
    return np.array([elo_diff, spi_diff, xg_diff, xga_diff, ppda_ratio, field_tilt_diff],
                    dtype=float)


def _softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - x.max())
    return e / e.sum()


def _predict_with_model(features: np.ndarray, model: dict) -> tuple[float, float, float]:
    """
    Apply trained LogisticRegression coefficients.
    model keys: mean, std, coef (shape [n_classes, n_features]), intercept
    Classes are ordered: [-1=away_win, 0=draw, 1=home_win]
    """
    mean = np.array(model["mean"])
    std = np.array(model["std"])
    coef = np.array(model["coef"])       # shape (3, 6)
    intercept = np.array(model["intercept"])  # shape (3,)

    # Standardise features
    std_safe = np.where(std < 1e-9, 1.0, std)
    x = (features - mean) / std_safe

    # Linear scores
    scores = coef @ x + intercept       # shape (3,)
    probs = _softmax(scores)            # [p_away, p_draw, p_home] — sorted by class label

    # Class order from sklearn: classes_ = [-1, 0, 1]
    p_away, p_draw, p_home = float(probs[0]), float(probs[1]), float(probs[2])
    return p_home, p_draw, p_away


def _fallback_predict(features: np.ndarray) -> tuple[float, float, float]:
    """
    Statistical fallback when model coefficients are not available.
    Uses ELO difference (features[0]) to estimate win probabilities.
    """
    elo_diff = features[0]
    # ELO-based win probability
    p_home_win = 1.0 / (1.0 + 10.0 ** (-elo_diff / 400.0))
    # Draw probability: peaks at ~28% when even, less when dominant
    draw_factor = 0.28 * (1.0 - abs(elo_diff) / 600.0)
    draw_factor = max(0.10, min(0.30, draw_factor))
    p_home = p_home_win * (1.0 - draw_factor)
    p_away = (1.0 - p_home_win) * (1.0 - draw_factor)
    p_draw = draw_factor
    total = p_home + p_draw + p_away
    return p_home / total, p_draw / total, p_away / total


def predict(home: TeamData, away: TeamData) -> ModelResult:
    """
    Predict match outcome using trained LogisticRegression (or ELO fallback).

    Returns ModelResult with p_home, p_draw, p_away and estimated lambdas.
    """
    features = _extract_features(home, away)
    model = _load_model()

    if model is not None:
        p_home, p_draw, p_away = _predict_with_model(features, model)
    else:
        p_home, p_draw, p_away = _fallback_predict(features)

    # Ensure valid probabilities
    total = p_home + p_draw + p_away
    if total < 1e-9:
        p_home, p_draw, p_away = 0.40, 0.25, 0.35
        total = 1.0
    p_home /= total
    p_draw /= total
    p_away /= total

    # Estimate lambdas from win probabilities
    # Use: lam_h = 1.35 * p_home / (p_home + p_away) * 2
    denom = max(p_home + p_away, 0.01)
    lam_h = max(0.30, min(3.0, 1.35 * (p_home / denom) * 2.0))
    lam_a = max(0.30, min(3.0, 1.35 * (p_away / denom) * 2.0))

    # Build score matrix from Dixon-Coles using our lambdas
    mat = dc_matrix(lam_h, lam_a)

    return ModelResult(
        model_name="ML",
        p_home=p_home,
        p_draw=p_draw,
        p_away=p_away,
        lambda_home=lam_h,
        lambda_away=lam_a,
        score_matrix=mat,
    )
