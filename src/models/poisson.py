"""Independent Poisson model for score prediction."""
from __future__ import annotations
import math
import numpy as np
from config.settings import INT_AVG_GOALS_HOME, INT_AVG_GOALS_AWAY, MAX_GOALS_MATRIX
from src.data.structures import TeamData, ModelResult


def _compute_lambdas(home: TeamData, away: TeamData) -> tuple[float, float]:
    """
    Compute expected goals using attack/defense strength ratio against
    a league-average baseline.

    lambda_home = base_home × (home_att_strength) × (away_def_weakness)
    where strength = team_stat / league_avg
    """
    # Attack strength: team xG / league avg
    home_att = home.attack.xg_per_game / INT_AVG_GOALS_HOME
    away_att = away.attack.xg_per_game / INT_AVG_GOALS_AWAY

    # Defense weakness: how many more/fewer goals than avg they concede
    home_def = home.defense.xga_per_game / INT_AVG_GOALS_AWAY
    away_def = away.defense.xga_per_game / INT_AVG_GOALS_HOME

    lam_home = INT_AVG_GOALS_HOME * home_att * away_def
    lam_away = INT_AVG_GOALS_AWAY * away_att * home_def

    # Blend with exponentially-weighted recent form (last 10 matches)
    matches_h = home.recent_matches[-10:]
    matches_a = away.recent_matches[-10:]

    def _exp_goals(matches, fallback):
        if not matches:
            return fallback
        n = len(matches)
        weights = [1.6 ** i for i in range(n)]
        total_w = sum(weights)
        return sum(w * m.goals_for for w, m in zip(weights, matches)) / total_w

    recent_home_scored = _exp_goals(matches_h, home.attack.goals_per_game)
    recent_away_scored = _exp_goals(matches_a, away.attack.goals_per_game)
    lam_home = 0.65 * lam_home + 0.35 * recent_home_scored
    lam_away = 0.65 * lam_away + 0.35 * recent_away_scored

    return max(0.30, lam_home), max(0.30, lam_away)


def _poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def score_matrix(lam_home: float, lam_away: float) -> np.ndarray:
    """Return (MAX+1) × (MAX+1) matrix of P(home=i, away=j)."""
    n = MAX_GOALS_MATRIX + 1
    mat = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            mat[i, j] = _poisson_pmf(i, lam_home) * _poisson_pmf(j, lam_away)
    # Normalise residual probability into last row/col
    mat /= mat.sum()
    return mat


def predict(home: TeamData, away: TeamData) -> ModelResult:
    lam_h, lam_a = _compute_lambdas(home, away)
    mat = score_matrix(lam_h, lam_a)

    p_home = float(np.tril(mat, -1).sum())   # home goals > away goals
    p_draw = float(np.trace(mat))
    p_away = float(np.triu(mat, 1).sum())

    return ModelResult(
        model_name="Poisson",
        p_home=p_home,
        p_draw=p_draw,
        p_away=p_away,
        lambda_home=lam_h,
        lambda_away=lam_a,
        score_matrix=mat,
    )
