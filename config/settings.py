"""Global configuration for the football prediction system."""

# ── Model Weights (must sum to 1.0) ──────────────────────────────────────────
MODEL_WEIGHTS = {
    "dixon_coles": 0.25,
    "xg":          0.25,
    "elo":         0.20,
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
INT_AVG_GOALS_HOME = 1.40       # Average goals per game by "home" side (neutral)
INT_AVG_GOALS_AWAY = 1.10       # Average goals per game by "away" side (neutral)

# ── Score matrix cap ─────────────────────────────────────────────────────────
MAX_GOALS_MATRIX = 8            # Compute score probability up to this

# ── xG Model ─────────────────────────────────────────────────────────────────
XG_REGRESSION_WEIGHT = 0.70     # How much to trust xG vs raw goals

# ── Market ov/und removal (overround) ────────────────────────────────────────
MARKET_MARGIN_REMOVAL = True    # Remove bookmaker margin

# ── Report aesthetics ────────────────────────────────────────────────────────
CONFIDENCE_STARS = 10           # Out of 10
