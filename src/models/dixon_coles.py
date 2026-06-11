"""
Dixon-Coles (1997) corrected Poisson model.

Adds a correlation factor τ that adjusts the probability of low-scoring
outcomes (0-0, 1-0, 0-1, 1-1) where the independence assumption breaks down.
"""
from __future__ import annotations
import numpy as np
from config.settings import DC_RHO, MAX_GOALS_MATRIX
from src.data.structures import TeamData, ModelResult
from .poisson import _compute_lambdas, _poisson_pmf


def _tau(i: int, j: int, lam_h: float, lam_a: float, rho: float) -> float:
    """Dixon-Coles correction factor for score (i, j)."""
    if i == 0 and j == 0:
        return 1.0 - lam_h * lam_a * rho
    if i == 0 and j == 1:
        return 1.0 + lam_h * rho
    if i == 1 and j == 0:
        return 1.0 + lam_a * rho
    if i == 1 and j == 1:
        return 1.0 - rho
    return 1.0


def score_matrix(lam_home: float, lam_away: float, rho: float = DC_RHO) -> np.ndarray:
    n = MAX_GOALS_MATRIX + 1
    mat = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            tau = _tau(i, j, lam_home, lam_away, rho)
            mat[i, j] = tau * _poisson_pmf(i, lam_home) * _poisson_pmf(j, lam_away)
    # Ensure non-negative (rho can occasionally push a cell slightly below 0)
    mat = np.maximum(mat, 0.0)
    mat /= mat.sum()
    return mat


def predict(home: TeamData, away: TeamData) -> ModelResult:
    lam_h, lam_a = _compute_lambdas(home, away)
    mat = score_matrix(lam_h, lam_a)

    p_home = float(np.tril(mat, -1).sum())
    p_draw = float(np.trace(mat))
    p_away = float(np.triu(mat, 1).sum())

    return ModelResult(
        model_name="Dixon-Coles",
        p_home=p_home,
        p_draw=p_draw,
        p_away=p_away,
        lambda_home=lam_h,
        lambda_away=lam_a,
        score_matrix=mat,
    )
