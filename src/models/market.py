"""
Market Odds Model.

Back-calculates true probabilities from bookmaker 1X2 decimal odds
by removing the overround (vig).  Uses market-implied lambdas via
a simple iterative Poisson inversion.
"""
from __future__ import annotations
import math
from src.data.structures import TeamData, ModelResult, MarketData
from src.data.loader import get_market_data, get_match_market_data


def _remove_overround(odds_h: float, odds_d: float, odds_a: float
                      ) -> tuple[float, float, float]:
    """Shin method approximation: normalise raw probabilities."""
    raw_h = 1.0 / odds_h
    raw_d = 1.0 / odds_d
    raw_a = 1.0 / odds_a
    total = raw_h + raw_d + raw_a
    return raw_h / total, raw_d / total, raw_a / total


def _poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def _lambda_from_probs(p_home: float, p_draw: float) -> tuple[float, float]:
    """
    Iteratively find Poisson lambdas that match market-implied 1X2 probabilities.

    Two decoupled adjustments per iteration:
    - Scale (lam_h + lam_a): controls draw probability.
    - Ratio (lam_h / lam_a): controls home vs away win probability.
    Converges in ~15 steps for typical football odds.
    """
    p_away = max(0.05, 1.0 - p_home - p_draw)

    # Initial guess via crude approximation
    total = max(0.8, -2.0 * math.log(max(p_draw, 0.05)))
    ratio = math.sqrt(max(p_home / p_away, 0.04))
    lam_h = total * ratio / (1.0 + ratio)
    lam_a = max(0.25, total - lam_h)

    n_pmf = 9   # truncate at 8 goals (residual <0.2% for typical lambdas)
    for _ in range(15):
        phv = [_poisson_pmf(k, lam_h) for k in range(n_pmf)]
        pav = [_poisson_pmf(k, lam_a) for k in range(n_pmf)]

        act_h = sum(phv[h] * pav[a] for h in range(n_pmf) for a in range(h))
        act_d = sum(phv[k] * pav[k] for k in range(n_pmf))
        norm = act_h + act_d + sum(phv[a] * pav[h] for h in range(n_pmf) for a in range(h))
        if norm > 0:
            act_h /= norm
            act_d /= norm

        # Adjust scale to match draw probability
        err_d = act_d - p_draw
        if abs(err_d) > 0.003:
            scale = max(0.80, min(1.20, 1.0 + 0.35 * err_d / max(p_draw, 0.05)))
            lam_h *= scale
            lam_a *= scale

        # Adjust ratio to match home win probability
        err_h = act_h - p_home
        if abs(err_h) > 0.004:
            adj = max(0.80, min(1.20, 1.0 - 0.40 * err_h / max(p_home, 0.05)))
            lam_h *= adj
            lam_a /= adj

        lam_h = max(0.25, lam_h)
        lam_a = max(0.25, lam_a)

    return max(0.30, lam_h), max(0.30, lam_a)


def _movement_signal(market: MarketData) -> tuple[float, float, float]:
    """
    Additive probability adjustments (adj_h, adj_d, adj_a) from three signals:

    1. 1X2 implied-probability drift (closing vs opening odds) — tracks where
       money flowed; 65% of the drift is treated as signal, rest as noise.
    2. Asian Handicap line movement — each 0.5-ball move ≈ 5-6% probability
       shift and is a very reliable sharp-money indicator.
    3. Sharp money index — composite 0-1 score: >0.5 = smart money on home,
       <0.5 = smart money on away; max ±4% effect.

    Total adjustment is capped at ±15% per outcome to prevent over-reaction.
    """
    adj_h = adj_d = adj_a = 0.0

    # 1. 1X2 drift
    if market.odds_open_home > 1.01 and market.odds_open_draw > 1.01:
        def fair(oh, od, oa):
            r = 1/oh + 1/od + 1/oa
            return (1/oh)/r, (1/od)/r, (1/oa)/r
        fh_o, fd_o, fa_o = fair(market.odds_open_home, market.odds_open_draw, market.odds_open_away)
        fh_c, fd_c, fa_c = fair(market.odds_home, market.odds_draw, market.odds_away)
        dh = fh_c - fh_o   # positive = home odds shortened (money came in)
        da = fa_c - fa_o
        dd = fd_c - fd_o
        adj_h += dh * 0.65
        adj_a += da * 0.65
        adj_d += dd * 0.50

    # 2. AH line movement
    if market.ah_open_line < 900:
        ah_move = market.asian_handicap_line - market.ah_open_line
        # negative ah_move = home handicap grew (more money on home)
        ah_boost = -ah_move * 0.055
        adj_h += ah_boost
        adj_a -= ah_boost

    # 3. Sharp index (0.5=neutral; ±0.5 range → ±4% max effect)
    sharp_boost = (market.sharp_index - 0.5) * 0.08
    adj_h += sharp_boost
    adj_a -= sharp_boost

    return (
        max(-0.15, min(0.15, adj_h)),
        max(-0.08, min(0.08, adj_d)),
        max(-0.15, min(0.15, adj_a)),
    )


def predict(home: TeamData, away: TeamData,
            market: MarketData | None = None) -> ModelResult:
    if market is None:
        market = get_match_market_data(home.code, away.code) or get_market_data(home.code)

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

    # Apply market movement / sharp-money signal
    adj_h, adj_d, adj_a = _movement_signal(market)
    p_home = max(0.02, p_home + adj_h)
    p_draw = max(0.02, p_draw + adj_d)
    p_away = max(0.02, p_away + adj_a)
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
