"""
Expected Goals (xG) model.

Factors applied:
  - xG/xGA base (blended with actual goals via XG_REGRESSION_WEIGHT)
  - Opponent defence quality
  - Player availability (injuries/suspensions), partially offset by squad depth
  - Exponentially-weighted recent form (last 10 matches)
  - Coach rating modifier (±3%)
  - Set-piece quality differential (±6%)
  - Press-intensity vs PPDA matchup (≤+4%)
"""
from __future__ import annotations
import math
import numpy as np
from config.settings import XG_REGRESSION_WEIGHT, MAX_GOALS_MATRIX, XG_LAMBDA_CAP, XG_DEF_FACTOR_WEIGHT
from src.data.structures import TeamData, ModelResult
from .dixon_coles import score_matrix as dc_matrix


def _availability_modifier(team: TeamData) -> float:
    """Multiplier for absent FWD/MID, partially offset by squad depth."""
    injured_fwd = sum(
        1 for p in team.injured_players + team.suspended_players
        if p.position in ("FWD", "MID")
    )
    if injured_fwd == 0:
        return 1.0
    base = max(0.75, 1.0 - 0.06 * injured_fwd)
    # Deeper squads cover absences better (squad_depth 0–10, neutral ≈ 5)
    depth_bonus = (team.squad_depth - 5.0) * 0.005 * injured_fwd
    return min(1.0, max(0.72, base + depth_bonus))


def _form_modifier(team: TeamData) -> float:
    """
    Scale 0.85–1.15 using exponentially-weighted recent form (last 10 matches).
    Most recent match has the highest weight (decay base 1.6).
    """
    matches = team.recent_matches[-10:]
    if not matches:
        return 1.0
    n = len(matches)
    # weights[0] = oldest, weights[-1] = newest
    weights = [1.6 ** i for i in range(n)]
    total_w = sum(weights)
    pts_norm = sum(
        w * (3 if m.outcome == "W" else 1 if m.outcome == "D" else 0)
        for w, m in zip(weights, matches)
    ) / (total_w * 3.0)     # normalise to [0, 1]
    return 0.85 + 0.30 * pts_norm


def _coach_modifier(team: TeamData) -> float:
    """Small boost/penalty from coach quality. ±3% (neutral at 7.0)."""
    return max(0.93, min(1.07, 1.0 + 0.015 * (team.coach_rating - 7.0)))


def _tactical_modifier(home: TeamData, away: TeamData) -> tuple[float, float]:
    """
    Two tactical effects:
    1. Set-piece quality differential: ±6% max.
    2. High press vs passive opponent (PPDA > 10): up to +4%.
    """
    # Set-piece quality gap [-10, +10] → ±6%
    sp_gap = home.tactics.set_piece_quality - away.tactics.set_piece_quality
    h_sp = 1.0 + 0.006 * sp_gap
    a_sp = 1.0 - 0.006 * sp_gap

    # Press intensity [0-10] vs PPDA: lower PPDA = opponent presses hard → harder to exploit
    # Benefit only when pressing hard (>6) against passive defence (PPDA>10)
    h_press = 1.0 + max(0.0, home.tactics.press_intensity - 6.0) * max(0.0, away.advanced.ppda - 10.0) * 0.0015
    a_press = 1.0 + max(0.0, away.tactics.press_intensity - 6.0) * max(0.0, home.advanced.ppda - 10.0) * 0.0015

    return (
        max(0.90, min(1.10, h_sp * h_press)),
        max(0.90, min(1.10, a_sp * a_press)),
    )


def _compute_xg_lambdas(home: TeamData, away: TeamData) -> tuple[float, float]:
    # Base: blend xG with actual goals
    lam_h = (XG_REGRESSION_WEIGHT * home.attack.xg_per_game +
             (1 - XG_REGRESSION_WEIGHT) * home.attack.goals_per_game)
    lam_a = (XG_REGRESSION_WEIGHT * away.attack.xg_per_game +
             (1 - XG_REGRESSION_WEIGHT) * away.attack.goals_per_game)

    # Adjust for opponent defence quality vs international average.
    # XG_DEF_FACTOR_WEIGHT dampens the raw club-stat multiplier toward 1.0:
    #   raw_factor = xGA / 1.10  (e.g. CPV: 1.6/1.10 = 1.45)
    #   dampened   = 1 + 0.55*(raw_factor - 1) = 1 + 0.55*0.45 = 1.25
    # This prevents extreme multipliers from weak teams' club statistics.
    raw_away_def = away.defense.xga_per_game / 1.10
    raw_home_def = home.defense.xga_per_game / 1.10
    away_def_factor = 1.0 + XG_DEF_FACTOR_WEIGHT * (raw_away_def - 1.0)
    home_def_factor = 1.0 + XG_DEF_FACTOR_WEIGHT * (raw_home_def - 1.0)
    lam_h *= max(0.60, min(1.50, away_def_factor))
    lam_a *= max(0.60, min(1.50, home_def_factor))

    # Player availability (injuries / suspensions)
    lam_h *= _availability_modifier(home)
    lam_a *= _availability_modifier(away)

    # Exponentially-weighted form
    lam_h *= _form_modifier(home)
    lam_a *= _form_modifier(away)

    # Coach quality
    lam_h *= _coach_modifier(home)
    lam_a *= _coach_modifier(away)

    # Tactical matchup (set pieces + press vs PPDA)
    tac_h, tac_a = _tactical_modifier(home, away)
    lam_h *= tac_h
    lam_a *= tac_a

    # Hard cap: no team realistically creates >XG_LAMBDA_CAP xG against
    # an organised World Cup defence, regardless of club-level statistics
    return max(0.30, min(XG_LAMBDA_CAP, lam_h)), max(0.30, min(XG_LAMBDA_CAP, lam_a))


def predict(home: TeamData, away: TeamData) -> ModelResult:
    lam_h, lam_a = _compute_xg_lambdas(home, away)
    mat = dc_matrix(lam_h, lam_a)

    p_home = float(np.tril(mat, -1).sum())
    p_draw = float(np.trace(mat))
    p_away = float(np.triu(mat, 1).sum())

    return ModelResult(
        model_name="xG Model",
        p_home=p_home,
        p_draw=p_draw,
        p_away=p_away,
        lambda_home=lam_h,
        lambda_away=lam_a,
        score_matrix=mat,
    )
