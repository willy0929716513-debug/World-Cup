"""
Ensemble model — weighted combination of all prediction models.

Weight order (configurable in settings.py):
  Dixon-Coles (25%) + xG (25%) + ELO (20%) + Market (20%) + MC (10%)
"""
from __future__ import annotations
import numpy as np
from config.settings import MODEL_WEIGHTS, MONTE_CARLO_SIMULATIONS, MAX_GOALS_MATRIX
from src.data.structures import TeamData, ModelResult, EnsembleResult, MarketData

from . import elo, poisson, dixon_coles, xg_model, market, monte_carlo


def run(
    home: TeamData,
    away: TeamData,
    market_data: MarketData | None = None,
    neutral: bool = True,
) -> EnsembleResult:
    # ── Run individual models ────────────────────────────────────────────────
    r_elo = elo.predict(home, away, neutral=neutral)
    r_poi = poisson.predict(home, away)
    r_dc  = dixon_coles.predict(home, away)
    r_xg  = xg_model.predict(home, away)
    r_mkt = market.predict(home, away, market_data)

    # Ensemble lambdas (weighted average)
    w = MODEL_WEIGHTS
    lam_h = (
        w["dixon_coles"] * r_dc.lambda_home +
        w["xg"]          * r_xg.lambda_home +
        w["elo"]         * r_elo.lambda_home +
        w["market"]      * r_mkt.lambda_home +
        w["monte_carlo"] * r_dc.lambda_home    # use DC as MC base
    )
    lam_a = (
        w["dixon_coles"] * r_dc.lambda_away +
        w["xg"]          * r_xg.lambda_away +
        w["elo"]         * r_elo.lambda_away +
        w["market"]      * r_mkt.lambda_away +
        w["monte_carlo"] * r_dc.lambda_away
    )

    # ── Monte Carlo with ensemble lambdas ────────────────────────────────────
    r_mc = monte_carlo.simulate(lam_h, lam_a, n=MONTE_CARLO_SIMULATIONS)

    model_results = [r_elo, r_poi, r_dc, r_xg, r_mkt, r_mc]

    # ── Weighted average of 3-way probabilities ──────────────────────────────
    # Monte Carlo already uses ensemble lambdas; treat its weight from settings
    model_map = {
        "dixon_coles": r_dc,
        "xg":          r_xg,
        "elo":         r_elo,
        "market":      r_mkt,
        "monte_carlo": r_mc,
    }

    p_home = sum(w[k] * v.p_home for k, v in model_map.items())
    p_draw = sum(w[k] * v.p_draw for k, v in model_map.items())
    p_away = sum(w[k] * v.p_away for k, v in model_map.items())
    total  = p_home + p_draw + p_away
    p_home /= total; p_draw /= total; p_away /= total

    # ── Build ensemble score probability matrix ───────────────────────────────
    # 60 % from DC matrix, 40 % from Monte Carlo simulation
    dc_mat  = r_dc.score_matrix
    mc_probs = getattr(r_mc, "_score_probs", {})

    n = MAX_GOALS_MATRIX + 1
    combo_mat = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            dc_p  = float(dc_mat[i, j]) if dc_mat is not None else 0.0
            mc_p  = mc_probs.get((i, j), 0.0)
            combo_mat[i, j] = 0.60 * dc_p + 0.40 * mc_p

    combo_mat /= combo_mat.sum()

    score_probs = {
        (i, j): float(combo_mat[i, j])
        for i in range(n) for j in range(n)
    }

    return EnsembleResult(
        p_home=p_home,
        p_draw=p_draw,
        p_away=p_away,
        lambda_home=lam_h,
        lambda_away=lam_a,
        score_probs=score_probs,
        model_results=model_results,
    )
