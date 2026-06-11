"""
Expected Goals (xG) model.

Uses xG and xGA data to compute lambdas, then applies a Dixon-Coles score
matrix.  Also factors in form and player availability modifiers.
"""
from __future__ import annotations
import numpy as np
from config.settings import XG_REGRESSION_WEIGHT, MAX_GOALS_MATRIX
from src.data.structures import TeamData, ModelResult
from .dixon_coles import score_matrix as dc_matrix


def _availability_modifier(team: TeamData) -> float:
    """Return a multiplier < 1.0 if key attackers are absent."""
    injured_fwd = sum(
        1 for p in team.injured_players + team.suspended_players
        if p.position in ("FWD", "MID")
    )
    return max(0.75, 1.0 - 0.06 * injured_fwd)


def _form_modifier(team: TeamData) -> float:
    """Scale between 0.85–1.15 based on recent form vs. expected."""
    pts = team.form_pts(5)          # pts per game, max=3
    neutral_pts = 1.5
    return 0.85 + 0.30 * (pts / 3.0)


def _compute_xg_lambdas(home: TeamData, away: TeamData) -> tuple[float, float]:
    # Base: blend xG with actual goals
    lam_h = (XG_REGRESSION_WEIGHT * home.attack.xg_per_game +
             (1 - XG_REGRESSION_WEIGHT) * home.attack.goals_per_game)
    lam_a = (XG_REGRESSION_WEIGHT * away.attack.xg_per_game +
             (1 - XG_REGRESSION_WEIGHT) * away.attack.goals_per_game)

    # Adjust for opponent defense quality
    # high xGA opponent = easier to score; low xGA = harder
    away_def_factor = away.defense.xga_per_game / 1.10
    home_def_factor = home.defense.xga_per_game / 1.10
    lam_h *= away_def_factor
    lam_a *= home_def_factor

    # Player availability
    lam_h *= _availability_modifier(home)
    lam_a *= _availability_modifier(away)

    # Form modifier
    lam_h *= _form_modifier(home)
    lam_a *= _form_modifier(away)

    return max(0.30, lam_h), max(0.30, lam_a)


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
