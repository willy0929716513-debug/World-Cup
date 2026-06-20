"""Core data structures for the football prediction system."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class MatchResult:
    opponent: str
    goals_for: int
    goals_against: int
    venue: str          # 'H' | 'A' | 'N'
    competition: str

    @property
    def outcome(self) -> str:
        if self.goals_for > self.goals_against:
            return "W"
        if self.goals_for < self.goals_against:
            return "L"
        return "D"


@dataclass
class PlayerInfo:
    name: str
    position: str           # GK | DEF | MID | FWD
    club: str
    age: int
    market_value_m: float   # millions EUR
    goals_season: int = 0
    assists_season: int = 0
    form_rating: float = 7.0
    is_injured: bool = False
    is_suspended: bool = False
    injury_detail: str = ""


@dataclass
class AttackStats:
    goals_per_game: float
    xg_per_game: float
    npxg_per_game: float
    shots_per_game: float
    shots_on_target_per_game: float
    shots_in_box_per_game: float
    big_chances_per_game: float
    conversion_rate: float
    counter_goals_pct: float        # % of goals from counter-attack
    set_piece_goals_pct: float      # % of goals from set pieces
    corners_per_game: float
    cross_accuracy_pct: float
    key_passes_per_game: float
    possession_pct: float
    pass_accuracy_pct: float


@dataclass
class DefenseStats:
    goals_against_per_game: float
    xga_per_game: float
    clean_sheet_pct: float
    shots_against_per_game: float
    sot_against_per_game: float
    tackle_success_pct: float
    interceptions_per_game: float
    clearances_per_game: float
    set_piece_conceded_pct: float
    aerial_success_pct: float
    gk_save_pct: float
    gk_psxg_ga: float               # PSxG-GA: positive = better than expected


@dataclass
class AdvancedStats:
    ppda: float                     # Passes Per Defensive Action (lower = more intense press)
    field_tilt: float               # % time ball in opponent's final third
    deep_completion_per_game: float # progressive passes into 18-yard box
    progressive_passes: float
    progressive_carries: float
    shot_creating_actions: float
    goal_creating_actions: float
    xpts_per_game: float


@dataclass
class TacticalProfile:
    primary_formation: str
    secondary_formation: str
    possession_style: bool          # True = possession, False = counter/direct
    high_press: bool
    press_intensity: float          # 0–10
    defensive_line: str             # 'high' | 'medium' | 'low'
    wide_play_pct: float            # % attacks via wings
    set_piece_quality: float        # 0–10
    tactical_flexibility: float     # 0–10


@dataclass
class MarketData:
    odds_home: float                # 1X2 decimal odds (closing)
    odds_draw: float
    odds_away: float
    asian_handicap_line: float      # e.g. -0.5, +1.5 (closing)
    asian_handicap_home_odds: float
    asian_handicap_away_odds: float
    ou_line: float                  # Over/Under line, e.g. 2.5
    over_odds: float
    under_odds: float
    # Market movement signals (optional; 0.0/999 = not available)
    odds_open_home: float = 0.0     # Opening 1X2 odds
    odds_open_draw: float = 0.0
    odds_open_away: float = 0.0
    ah_open_line: float = 999.0     # Opening AH line (999 = unavailable)
    sharp_index: float = 0.5        # 0-1: >0.5 = sharp money on home, <0.5 = on away
    steam: bool = False             # True if sudden large line move detected


@dataclass
class MatchEnvironment:
    venue: str
    city: str
    country: str
    capacity: int
    altitude_m: int
    temperature_c: float
    humidity_pct: float
    wind_speed_kmh: float
    pitch_condition: str            # 'excellent' | 'good' | 'poor'
    neutral_venue: bool
    crowd_factor: float             # 0–10 home support intensity


@dataclass
class RefereeProfile:
    name: str
    nationality: str
    avg_yellow_per_game: float = 3.5
    avg_red_per_game: float = 0.3
    avg_penalty_per_game: float = 0.4
    strict_style: bool = False


@dataclass
class TeamData:
    # Identity
    name: str
    short_name: str
    code: str                       # 3-letter FIFA code
    confederation: str

    # Section 1 – Overall Strength
    fifa_ranking: int
    elo_rating: float
    spi_rating: float
    squad_value_m: float            # total market value
    avg_age: float
    squad_depth: float              # 0–10
    bench_quality: float            # 0–10

    # World Cup history
    wc_titles: int
    wc_best_result: str
    wc_appearances: int

    # Sections 3–4 – Stats
    attack: AttackStats
    defense: DefenseStats
    advanced: AdvancedStats

    # Section 6 – Tactics
    tactics: TacticalProfile

    # Section 5 – Players
    key_players: List[PlayerInfo] = field(default_factory=list)
    injured_players: List[PlayerInfo] = field(default_factory=list)
    suspended_players: List[PlayerInfo] = field(default_factory=list)

    # Section 2 – Form (last 20 matches, oldest first)
    recent_matches: List[MatchResult] = field(default_factory=list)

    # Coach
    coach: str = ""
    coach_rating: float = 7.0      # 0–10

    # ── Derived helpers ───────────────────────────────────────────────────────
    def form_string(self, n: int = 5) -> str:
        outcomes = [m.outcome for m in self.recent_matches[-n:]]
        return " ".join(outcomes) if outcomes else "N/A"

    def form_pts(self, n: int = 5) -> float:
        matches = self.recent_matches[-n:]
        if not matches:
            return 1.5
        pts = sum(3 if m.outcome == "W" else 1 if m.outcome == "D" else 0
                  for m in matches)
        return pts / len(matches)

    def win_rate(self, n: int = 10) -> float:
        matches = self.recent_matches[-n:]
        if not matches:
            return 0.33
        return sum(1 for m in matches if m.outcome == "W") / len(matches)

    def goals_scored_avg(self, n: int = 10) -> float:
        matches = self.recent_matches[-n:]
        if not matches:
            return self.attack.goals_per_game
        return sum(m.goals_for for m in matches) / len(matches)

    def goals_conceded_avg(self, n: int = 10) -> float:
        matches = self.recent_matches[-n:]
        if not matches:
            return self.defense.goals_against_per_game
        return sum(m.goals_against for m in matches) / len(matches)


@dataclass
class ModelResult:
    """Output from a single prediction model."""
    model_name: str
    p_home: float
    p_draw: float
    p_away: float
    lambda_home: float
    lambda_away: float
    score_matrix: Optional[object] = None   # np.ndarray


@dataclass
class EnsembleResult:
    """Final combined prediction."""
    p_home: float
    p_draw: float
    p_away: float
    lambda_home: float
    lambda_away: float
    score_probs: dict           # (h_goals, a_goals) -> probability
    model_results: List[ModelResult] = field(default_factory=list)

    @property
    def most_likely_scores(self) -> List[tuple]:
        return sorted(self.score_probs.items(), key=lambda x: -x[1])[:10]

    def total_goal_probs(self) -> dict:
        totals: dict[int, float] = {}
        for (h, a), p in self.score_probs.items():
            t = h + a
            totals[t] = totals.get(t, 0.0) + p
        return totals

    def btts_prob(self) -> float:
        return sum(p for (h, a), p in self.score_probs.items() if h > 0 and a > 0)
