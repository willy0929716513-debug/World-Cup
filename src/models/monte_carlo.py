"""
Monte Carlo Simulation — 100,000 match simulations.

Each simulation:
  1. Samples λ_home and λ_away from Gamma distributions centred on
     the ensemble lambdas (variance captures model uncertainty).
  2. Draws Poisson-distributed goals.
  3. Tallies outcomes and score frequencies.
"""
from __future__ import annotations
import numpy as np
from config.settings import MONTE_CARLO_SIMULATIONS, MAX_GOALS_MATRIX
from src.data.structures import TeamData, ModelResult


def simulate(
    lam_home: float,
    lam_away: float,
    n: int = MONTE_CARLO_SIMULATIONS,
    uncertainty: float = 0.18,    # coefficient of variation for Gamma
    seed: int = 42,
) -> ModelResult:
    """
    Run Monte Carlo simulation.

    Lambda uncertainty is modelled as Gamma(shape, scale) where:
      mean = lambda
      std  = uncertainty * lambda
    → shape = 1/cv², scale = lambda/shape
    """
    rng = np.random.default_rng(seed)

    cv = uncertainty
    shape_h = 1.0 / (cv ** 2)
    scale_h = lam_home / shape_h

    shape_a = 1.0 / (cv ** 2)
    scale_a = lam_away / shape_a

    # Sample lambdas (model uncertainty)
    sampled_lam_h = rng.gamma(shape_h, scale_h, size=n)
    sampled_lam_a = rng.gamma(shape_a, scale_a, size=n)

    # Sample actual goals
    goals_h = rng.poisson(sampled_lam_h)
    goals_a = rng.poisson(sampled_lam_a)

    # Tally outcomes
    home_wins = np.sum(goals_h > goals_a)
    draws     = np.sum(goals_h == goals_a)
    away_wins = np.sum(goals_h < goals_a)

    p_home = home_wins / n
    p_draw = draws / n
    p_away = away_wins / n

    # Build score probability dictionary
    max_g = MAX_GOALS_MATRIX
    score_counts: dict[tuple[int,int], int] = {}
    for gh, ga in zip(goals_h, goals_a):
        key = (int(min(gh, max_g)), int(min(ga, max_g)))
        score_counts[key] = score_counts.get(key, 0) + 1

    score_probs = {k: v / n for k, v in score_counts.items()}

    result = ModelResult(
        model_name="Monte Carlo",
        p_home=p_home,
        p_draw=p_draw,
        p_away=p_away,
        lambda_home=lam_home,
        lambda_away=lam_away,
    )
    # Attach score_probs as an attribute (not in dataclass, stored externally)
    result._score_probs = score_probs  # type: ignore[attr-defined]
    return result
