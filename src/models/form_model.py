"""
Form model — computes WC2026 in-tournament form multiplier from actual results.

Reads docs/data/results.json (which contains all played WC2026 matches) and
returns a lambda multiplier per team based on:
  - Points per game (W=3, D=1, L=0), normalised to [0, 1]
  - Goal difference per game
  - Momentum: recent 2 games weighted 1.5× vs earlier games
  - Opponent ELO weighting: results vs stronger opponents weighted higher

Range: 0.85 – 1.15 (1.0 = neutral / no data)
"""
from __future__ import annotations
import json
import os

# Cache so we don't re-read the file on every ensemble call
_FORM_CACHE: dict[str, float] | None = None

_RESULTS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../docs/data/results.json")
)
_TEAMS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../data/teams.json")
)


def _load_elo_lookup() -> dict[str, float]:
    """Load ELO ratings from teams.json as a code → elo_rating dict."""
    if not os.path.exists(_TEAMS_PATH):
        return {}
    try:
        with open(_TEAMS_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {code: float(data.get("elo_rating", 1800)) for code, data in raw.items()}
    except Exception:
        return {}


def _compute_form_cache() -> dict[str, float]:
    """
    Parse docs/data/results.json and compute a form multiplier for each team
    that has played at least one WC2026 match.

    Each match contribution is weighted by opponent ELO / 1800 so that
    results against stronger opponents carry more weight.
    """
    if not os.path.exists(_RESULTS_PATH):
        return {}

    with open(_RESULTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    matches = data.get("matches", [])
    if not matches:
        return {}

    # Load ELO lookup for opponent weighting
    elo_lookup = _load_elo_lookup()

    # Collect per-team match records in chronological order
    # Each entry: (goals_for, goals_against, date, opponent_code)
    team_records: dict[str, list[tuple[int, int, str, str]]] = {}
    for m in matches:
        if not m.get("played", True):
            continue
        t1 = m.get("t1", "")
        t2 = m.get("t2", "")
        s1 = m.get("score1", 0)
        s2 = m.get("score2", 0)
        date = m.get("date", "2026-01-01")

        if t1:
            team_records.setdefault(t1, []).append((s1, s2, date, t2))
        if t2:
            team_records.setdefault(t2, []).append((s2, s1, date, t1))

    form_scores: dict[str, float] = {}

    for team, records in team_records.items():
        # Sort by date (oldest first)
        records.sort(key=lambda x: x[2])
        n = len(records)
        if n == 0:
            continue

        # Points: W=3, D=1, L=0
        pts = []
        gd = []
        opp_elo_weights = []
        for gf, ga, _, opp_code in records:
            if gf > ga:
                pts.append(3)
            elif gf == ga:
                pts.append(1)
            else:
                pts.append(0)
            gd.append(gf - ga)
            # Opponent ELO weight: default 1800 if not found → weight 1.0
            opp_elo = elo_lookup.get(opp_code, 1800)
            opp_elo_weights.append(opp_elo / 1800.0)

        # Momentum weighting: last 2 games get 1.5× weight
        momentum_weights = [1.0] * n
        for i in range(max(0, n - 2), n):
            momentum_weights[i] = 1.5

        # Combined weight: momentum × opponent ELO strength
        weights = [m * e for m, e in zip(momentum_weights, opp_elo_weights)]

        total_w = sum(weights)
        weighted_pts = sum(w * p for w, p in zip(weights, pts))
        weighted_gd = sum(w * g for w, g in zip(weights, gd))

        # Normalise points to [0, 1]: max is 3 pts per game
        pts_norm = (weighted_pts / total_w) / 3.0

        # Goal difference factor: clamp to [-3, +3] per game, scale to [-0.1, +0.1]
        gd_norm = max(-3.0, min(3.0, weighted_gd / total_w)) / 3.0

        # Combine: 70% points, 30% goal difference
        raw_score = 0.70 * pts_norm + 0.30 * (0.5 + 0.5 * gd_norm)

        # Map [0, 1] → [0.85, 1.15]
        multiplier = 0.85 + 0.30 * raw_score
        multiplier = max(0.85, min(1.15, multiplier))

        form_scores[team] = multiplier

    return form_scores


def get_form_multiplier(team_code: str) -> float:
    """
    Returns a lambda multiplier 0.85–1.15 based on WC2026 actual results.
    Returns 1.0 (neutral) if the team has played 0 WC2026 games.
    """
    global _FORM_CACHE
    if _FORM_CACHE is None:
        _FORM_CACHE = _compute_form_cache()
    return _FORM_CACHE.get(team_code, 1.0)


def reset_cache() -> None:
    """Force re-read of results file (useful for testing)."""
    global _FORM_CACHE
    _FORM_CACHE = None
