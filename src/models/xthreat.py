"""xThreat proxy using shots_in_box, goal_creating_actions, big_chances."""
from __future__ import annotations
from src.data.structures import TeamData


def xt_multiplier(team: TeamData) -> float:
    """0.85–1.15 lambda multiplier based on chance quality proxy."""
    # Normalize each metric (typical WC team values as reference)
    gca_norm = min(1.0, team.advanced.goal_creating_actions / 3.5)   # 3.5 GCA/game = strong
    sib_norm = min(1.0, team.attack.shots_in_box_per_game / 9.0)      # 9 shots in box = strong
    bch_norm = min(1.0, team.attack.big_chances_per_game / 2.5)       # 2.5 big chances = strong
    raw = 0.40 * gca_norm + 0.35 * sib_norm + 0.25 * bch_norm
    return max(0.85, min(1.15, 0.85 + 0.30 * raw))
