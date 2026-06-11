"""
Market Odds Model.

Back-calculates true probabilities from bookmaker 1X2 decimal odds
by removing the overround (vig).  Uses market-implied lambdas via
a simple iterative Poisson inversion.
"""
from __future__ import annotations
import math
from src.data.structures import TeamData, ModelResult, MarketData
from src.data.loader import get_market_data


def _remove_overround(odds_h: float, odds_d: float, odds_a: float
                      ) -> tuple[float, float, float]:
    """Shin method approximation: normalise raw probabilities."""
    raw_h = 1.0 / odds_h
    raw_d = 1.0 / odds_d
    raw_a = 1.0 / odds_a
    total = raw_h + raw_d + raw_a
    return raw_h / total, raw_d / total, raw_a / total


def _lambda_from_probs(p_home: float, p_draw: float) -> tuple[float, float]:
    """
    Approximate lambdas from win/draw probabilities using the
    relationship: lambda ≈ -log(P_draw + P_away) for one side.
    A simple search approach is used.
    """
    # Rough inversion: use P_draw ≈ e^(-(lh+la)) * sum of equal terms
    # Approximate: total expected goals = -2 * log(P_draw) (crude)
    total_goals = max(0.5, -2.0 * math.log(max(p_draw, 0.10)))
    # Allocate proportionally to P_home vs P_away
    p_away = 1.0 - p_home - p_draw
    ratio = p_home / max(p_away, 0.01)
    # lh/la ≈ ratio^0.5 (rough calibration from historical data)
    lam_h = total_goals * (ratio ** 0.4) / (1.0 + ratio ** 0.4)
    lam_a = total_goals - lam_h
    return max(0.30, lam_h), max(0.30, lam_a)


def predict(home: TeamData, away: TeamData,
            market: MarketData | None = None) -> ModelResult:
    if market is None:
        market = get_market_data(home.code)

    if market is None:
        # Fallback: use xG lambdas as proxy
        from .xg_model import _compute_xg_lambdas
        lam_h, lam_a = _compute_xg_lambdas(home, away)
        from .dixon_coles import score_matrix as dc_mat
        import numpy as np
        mat = dc_mat(lam_h, lam_a)
        p_h = float(np.tril(mat, -1).sum())
        p_d = float(np.trace(mat))
        p_a = float(np.triu(mat, 1).sum())
        return ModelResult("Market", p_h, p_d, p_a, lam_h, lam_a, mat)

    p_h, p_d, p_a = _remove_overround(
        market.odds_home, market.odds_draw, market.odds_away
    )
    lam_h, lam_a = _lambda_from_probs(p_h, p_d)

    # Build score matrix
    from .dixon_coles import score_matrix as dc_mat
    import numpy as np
    mat = dc_mat(lam_h, lam_a)
    # Re-normalise p_home/draw/away from matrix to stay consistent
    p_home = float(np.tril(mat, -1).sum())
    p_draw = float(np.trace(mat))
    p_away = float(np.triu(mat, 1).sum())

    # Blend market 1X2 (70%) with matrix-derived (30%) for calibration
    p_home = 0.70 * p_h + 0.30 * p_home
    p_draw = 0.70 * p_d + 0.30 * p_draw
    p_away = 0.70 * p_a + 0.30 * p_away
    total = p_home + p_draw + p_away
    p_home /= total; p_draw /= total; p_away /= total

    return ModelResult(
        model_name="Market",
        p_home=p_home,
        p_draw=p_draw,
        p_away=p_away,
        lambda_home=lam_h,
        lambda_away=lam_a,
        score_matrix=mat,
    )
