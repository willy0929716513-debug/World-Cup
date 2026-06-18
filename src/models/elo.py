"""ELO-based win/draw/loss probability model."""
from __future__ import annotations
import math
from config.settings import ELO_HOME_ADVANTAGE, ELO_SCALE
from src.data.structures import TeamData, ModelResult
import numpy as np


def _elo_win_prob(elo_a: float, elo_b: float) -> float:
    """P(A beats B) in a two-outcome ELO model."""
    return 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / ELO_SCALE))


def _elo_to_lambda(elo_diff: float, base_goals: float = 1.25) -> float:
    """Convert ELO difference to expected goals (simple linear mapping)."""
    return base_goals * math.exp(elo_diff / 1000.0)


def _composite_diff(home: TeamData, away: TeamData, neutral: bool) -> float:
    """
    Blend ELO + SPI + FIFA ranking into a single composite strength difference.

    Weights: 60 % ELO · 25 % SPI (FiveThirtyEight) · 15 % FIFA ranking.
    SPI and FIFA are converted to an ELO-equivalent scale before blending.
    """
    home_elo = home.elo_rating + (0 if neutral else ELO_HOME_ADVANTAGE)
    elo_diff = home_elo - away.elo_rating

    # SPI: higher = stronger; ~8 ELO pts per SPI point (empirical)
    spi_diff = (home.spi_rating - away.spi_rating) * 8.0

    # FIFA ranking: lower = better; 2.5 ELO pts per rank position
    fifa_diff = (away.fifa_ranking - home.fifa_ranking) * 2.5

    return 0.60 * elo_diff + 0.25 * spi_diff + 0.15 * fifa_diff


def predict(home: TeamData, away: TeamData, neutral: bool = True) -> ModelResult:
    """
    Produce 3-way probabilities from a composite ELO + SPI + FIFA rating.
    """
    home_elo = home.elo_rating + (0 if neutral else ELO_HOME_ADVANTAGE)
    elo_diff = home_elo - away.elo_rating
    composite_diff = _composite_diff(home, away, neutral)

    # Raw P(home win) using composite-adjusted effective ELO
    away_elo_adj = away.elo_rating - (composite_diff - elo_diff)
    p_home_raw = _elo_win_prob(home_elo, away_elo_adj)

    # Convert composite difference to expected goals
    base_h, base_a = 1.40, 1.10
    lam_home = _elo_to_lambda(composite_diff, base_h)
    lam_away = _elo_to_lambda(-composite_diff, base_a)

    # Cap lambdas to sensible range
    lam_home = max(0.40, min(lam_home, 4.00))
    lam_away = max(0.40, min(lam_away, 4.00))

    # Poisson draw probability: P(X=Y), summed to 5 (k>5 negligible in WC)
    p_draw = sum(
        math.exp(-lam_home) * (lam_home ** k) / math.factorial(k) *
        math.exp(-lam_away) * (lam_away ** k) / math.factorial(k)
        for k in range(6)
    )
    p_draw = min(p_draw, 0.36)  # WC group stage: observed ~27-30% draws historically

    # Distribute remaining probability between home/away win
    remaining = 1.0 - p_draw
    # Re-scale raw win probs to sum to `remaining`
    p_home = p_home_raw * remaining
    p_away = remaining - p_home

    # Normalise
    total = p_home + p_draw + p_away
    p_home /= total
    p_draw /= total
    p_away /= total

    return ModelResult(
        model_name="ELO",
        p_home=p_home,
        p_draw=p_draw,
        p_away=p_away,
        lambda_home=lam_home,
        lambda_away=lam_away,
    )
