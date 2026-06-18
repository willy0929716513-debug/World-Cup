"""Global configuration for the football prediction system."""

# ── Model Weights (must sum to 1.0) ──────────────────────────────────────────
# Calibrated against WC2026 group stage results (16 matches, 50% draw rate):
# - ELO boosted: most reliable signal for international football
# - xG reduced: club xG stats don't transfer well to WC neutral-venue matches
MODEL_WEIGHTS = {
    "dixon_coles": 0.25,
    "xg":          0.15,   # was 0.25 — xG over-inflates favourites vs weak teams
    "elo":         0.30,   # was 0.20 — ELO more stable for international tournaments
    "market":      0.20,
    "monte_carlo": 0.10,
}

# ── Monte Carlo ───────────────────────────────────────────────────────────────
MONTE_CARLO_SIMULATIONS = 100_000

# ── ELO ───────────────────────────────────────────────────────────────────────
ELO_HOME_ADVANTAGE = 100        # ELO points added for true home team
ELO_SCALE = 400                 # Standard ELO scale factor

# ── Dixon-Coles ───────────────────────────────────────────────────────────────
DC_RHO = -0.04                  # WC-calibrated: domestic -0.10 inflates 1-1 too much

# ── Poisson Base Rates (international / neutral) ──────────────────────────────
INT_AVG_GOALS_HOME = 1.35       # Slightly reduced: WC group stage is tactically cautious
INT_AVG_GOALS_AWAY = 1.05       # 2026 group stage trending ~2.3 goals/game average

# ── Score matrix cap ─────────────────────────────────────────────────────────
MAX_GOALS_MATRIX = 8            # Compute score probability up to this

# ── xG Model ─────────────────────────────────────────────────────────────────
XG_REGRESSION_WEIGHT = 0.70     # How much to trust xG vs raw goals
XG_LAMBDA_CAP       = 2.60     # Hard cap — no team realistically creates >2.6 xG
                                # against an organised WC defence
XG_DEF_FACTOR_WEIGHT = 0.55    # Regression-to-mean on opponent defence factor:
                                # 0 = ignore club stats, 1 = full weight.
                                # 0.55 prevents extreme multipliers from weak teams

# ── Group Stage Draw Boost ────────────────────────────────────────────────────
# WC group stage draws ~27-30% historically; ensemble underestimates draws.
# Applied after combining all models.
GROUP_STAGE_DRAW_BOOST = 1.18

# ── Market overround removal ──────────────────────────────────────────────────
MARKET_MARGIN_REMOVAL = True    # Remove bookmaker margin

# ── Report aesthetics ────────────────────────────────────────────────────────
CONFIDENCE_STARS = 10           # Out of 10
