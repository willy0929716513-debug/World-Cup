"""
Ensemble model — weighted combination of all prediction models.

Weight order (configurable in settings.py):
  Dixon-Coles (10%) + xG (10%) + ELO (20%) + Market (30%) + ML (20%) + MC (10%)

Monte Carlo receives the ensemble lambdas and contributes its uncertainty
structure to the final score matrix.  Its weight applies to 3-way probs only;
it does not double-count any other model's lambdas.

Form multiplier (from WC2026 actual results) adjusts lambdas AFTER computing
the base ensemble lambdas.

Calibration is applied as the final step to the ensemble probabilities.

Optional: altitude_m (metres above sea level) applies a small goal-rate
multiplier based on historical World Cup data (~+9% at Mexico City 2240m).
"""
from __future__ import annotations
import json
import os
import numpy as np
from config.settings import MODEL_WEIGHTS, MONTE_CARLO_SIMULATIONS, MAX_GOALS_MATRIX, GROUP_STAGE_DRAW_BOOST
from src.data.structures import TeamData, ModelResult, EnsembleResult, MarketData

from . import elo, poisson, dixon_coles, xg_model, market, monte_carlo, lgbm_model, form_model, calibration

# ── H2H bias cache (loaded once at module import) ───────────────────────────
_H2H_BIAS: dict = {}
try:
    _h2h_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../data/h2h_bias.json")
    )
    with open(_h2h_path, "r", encoding="utf-8") as _f:
        _H2H_BIAS = {k: v for k, v in json.load(_f).items() if not k.startswith("_")}
except Exception:
    pass


def run(
    home: TeamData,
    away: TeamData,
    market_data: MarketData | None = None,
    neutral: bool = True,
    altitude_m: int = 0,
    group_stage: bool = True,
) -> EnsembleResult:
    # ── Run individual models ────────────────────────────────────────────────
    r_elo  = elo.predict(home, away, neutral=neutral)
    r_poi  = poisson.predict(home, away)
    r_dc   = dixon_coles.predict(home, away)
    r_xg   = xg_model.predict(home, away)
    r_mkt  = market.predict(home, away, market_data)
    r_lgbm = lgbm_model.predict(home, away)

    # ── Ensemble lambdas (weighted average, MC excluded — it uses these) ────
    w = MODEL_WEIGHTS
    base_w = w["dixon_coles"] + w["xg"] + w["elo"] + w["market"] + w["lgbm"]
    lam_h = (
        w["dixon_coles"] * r_dc.lambda_home +
        w["xg"]          * r_xg.lambda_home +
        w["elo"]         * r_elo.lambda_home +
        w["market"]      * r_mkt.lambda_home +
        w["lgbm"]        * r_lgbm.lambda_home
    ) / base_w
    lam_a = (
        w["dixon_coles"] * r_dc.lambda_away +
        w["xg"]          * r_xg.lambda_away +
        w["elo"]         * r_elo.lambda_away +
        w["market"]      * r_mkt.lambda_away +
        w["lgbm"]        * r_lgbm.lambda_away
    ) / base_w

    # ── Form adjustment (from WC2026 actual results) ─────────────────────────
    home_form = form_model.get_form_multiplier(home.code)
    away_form = form_model.get_form_multiplier(away.code)
    lam_h *= home_form
    lam_a *= away_form

    # ── Altitude factor: thin air increases goal rates ───────────────────────
    # Calibrated to ~+9% at Mexico City (2240 m); capped at 2500 m.
    if altitude_m > 0:
        alt_factor = 1.0 + min(altitude_m, 2500) * 0.000038
        lam_h *= alt_factor
        lam_a *= alt_factor

    # ── ELO-gap dominance adjustment ─────────────────────────────────────────
    # Large ELO gaps mean the favourite wins more cleanly (fewer draws,
    # more clean sheets).  Scales from 0 % at 200-point gap to 10 % at 600+.
    elo_gap = home.elo_rating - away.elo_rating
    if abs(elo_gap) > 200:
        adj = min(0.10, (abs(elo_gap) - 200) * 0.00025)
        if elo_gap > 0:
            lam_h *= (1.0 + adj)
            lam_a *= max(0.70, 1.0 - adj)
        else:
            lam_a *= (1.0 + adj)
            lam_h *= max(0.70, 1.0 - adj)

    # Final cap on ensemble lambdas — even after weighting, keep realistic
    lam_h = min(lam_h, 3.0)
    lam_a = min(lam_a, 3.0)

    # ── Monte Carlo with ensemble lambdas ────────────────────────────────────
    r_mc = monte_carlo.simulate(lam_h, lam_a, n=MONTE_CARLO_SIMULATIONS)

    model_results = [r_elo, r_poi, r_dc, r_xg, r_mkt, r_lgbm, r_mc]

    # ── Weighted 3-way probabilities ─────────────────────────────────────────
    model_map = {
        "dixon_coles": r_dc,
        "xg":          r_xg,
        "elo":         r_elo,
        "market":      r_mkt,
        "lgbm":        r_lgbm,
        "monte_carlo": r_mc,
    }

    p_home = sum(w[k] * v.p_home for k, v in model_map.items())
    p_draw = sum(w[k] * v.p_draw for k, v in model_map.items())
    p_away = sum(w[k] * v.p_away for k, v in model_map.items())

    # Group stage tactical conservatism boost: teams play more defensively early
    # on, producing more draws than club-football models predict.
    if group_stage:
        p_draw *= GROUP_STAGE_DRAW_BOOST

    total  = p_home + p_draw + p_away
    p_home /= total; p_draw /= total; p_away /= total

    # ── H2H historical bias (small adjustment for key rivalries) ─────────────
    h2h_key = f"{home.code}_vs_{away.code}"
    if h2h_key in _H2H_BIAS:
        bias = _H2H_BIAS[h2h_key]
        p_home = max(0.04, p_home + bias.get("h", 0))
        p_draw = max(0.04, p_draw + bias.get("d", 0))
        p_away = max(0.04, p_away + bias.get("a", 0))
        total = p_home + p_draw + p_away
        p_home /= total; p_draw /= total; p_away /= total

    # ── Probability calibration (final step) ────────────────────────────────
    p_home, p_draw, p_away = calibration.calibrate(p_home, p_draw, p_away)

    # ── Build ensemble score probability matrix ───────────────────────────────
    # 60 % from DC matrix, 40 % from Monte Carlo simulation
    dc_mat   = r_dc.score_matrix
    mc_probs = getattr(r_mc, "_score_probs", {})

    n = MAX_GOALS_MATRIX + 1
    combo_mat = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            dc_p = float(dc_mat[i, j]) if dc_mat is not None else 0.0
            mc_p = mc_probs.get((i, j), 0.0)
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
