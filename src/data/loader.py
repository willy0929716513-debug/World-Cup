"""Load team data from JSON and construct TeamData objects."""
from __future__ import annotations
import json
import os
from typing import Optional
from .structures import (
    TeamData, AttackStats, DefenseStats, AdvancedStats,
    TacticalProfile, MarketData, PlayerInfo, MatchResult
)

_DATA_PATH = os.path.join(os.path.dirname(__file__), "../../data/teams.json")


def _load_raw() -> dict:
    path = os.path.abspath(_DATA_PATH)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_team(raw: dict) -> TeamData:
    atk = raw["attack"]
    dfn = raw["defense"]
    adv = raw["advanced"]
    tac = raw["tactics"]

    attack = AttackStats(
        goals_per_game=atk["goals_per_game"],
        xg_per_game=atk["xg_per_game"],
        npxg_per_game=atk["npxg_per_game"],
        shots_per_game=atk["shots_per_game"],
        shots_on_target_per_game=atk["shots_on_target_per_game"],
        shots_in_box_per_game=atk["shots_in_box_per_game"],
        big_chances_per_game=atk["big_chances_per_game"],
        conversion_rate=atk["conversion_rate"],
        counter_goals_pct=atk["counter_goals_pct"],
        set_piece_goals_pct=atk["set_piece_goals_pct"],
        corners_per_game=atk["corners_per_game"],
        cross_accuracy_pct=atk["cross_accuracy_pct"],
        key_passes_per_game=atk["key_passes_per_game"],
        possession_pct=atk["possession_pct"],
        pass_accuracy_pct=atk["pass_accuracy_pct"],
    )

    defense = DefenseStats(
        goals_against_per_game=dfn["goals_against_per_game"],
        xga_per_game=dfn["xga_per_game"],
        clean_sheet_pct=dfn["clean_sheet_pct"],
        shots_against_per_game=dfn["shots_against_per_game"],
        sot_against_per_game=dfn["sot_against_per_game"],
        tackle_success_pct=dfn["tackle_success_pct"],
        interceptions_per_game=dfn["interceptions_per_game"],
        clearances_per_game=dfn["clearances_per_game"],
        set_piece_conceded_pct=dfn["set_piece_conceded_pct"],
        aerial_success_pct=dfn["aerial_success_pct"],
        gk_save_pct=dfn["gk_save_pct"],
        gk_psxg_ga=dfn["gk_psxg_ga"],
    )

    advanced = AdvancedStats(
        ppda=adv["ppda"],
        field_tilt=adv["field_tilt"],
        deep_completion_per_game=adv["deep_completion_per_game"],
        progressive_passes=adv["progressive_passes"],
        progressive_carries=adv["progressive_carries"],
        shot_creating_actions=adv["shot_creating_actions"],
        goal_creating_actions=adv["goal_creating_actions"],
        xpts_per_game=adv["xpts_per_game"],
    )

    tactics = TacticalProfile(
        primary_formation=tac["primary_formation"],
        secondary_formation=tac["secondary_formation"],
        possession_style=tac["possession_style"],
        high_press=tac["high_press"],
        press_intensity=tac["press_intensity"],
        defensive_line=tac["defensive_line"],
        wide_play_pct=tac["wide_play_pct"],
        set_piece_quality=tac["set_piece_quality"],
        tactical_flexibility=tac["tactical_flexibility"],
    )

    def build_player(p: dict) -> PlayerInfo:
        return PlayerInfo(
            name=p["name"], position=p["position"], club=p["club"],
            age=p["age"], market_value_m=p["market_value_m"],
            goals_season=p.get("goals_season", 0),
            assists_season=p.get("assists_season", 0),
            form_rating=p.get("form_rating", 7.0),
            is_injured=p.get("is_injured", False),
            is_suspended=p.get("is_suspended", False),
            injury_detail=p.get("injury_detail", ""),
        )

    def build_match(m: dict) -> MatchResult:
        return MatchResult(
            opponent=m["opponent"],
            goals_for=m["goals_for"],
            goals_against=m["goals_against"],
            venue=m["venue"],
            competition=m["competition"],
        )

    return TeamData(
        name=raw["name"],
        short_name=raw["short_name"],
        code=raw["code"],
        confederation=raw["confederation"],
        fifa_ranking=raw["fifa_ranking"],
        elo_rating=raw["elo_rating"],
        spi_rating=raw["spi_rating"],
        squad_value_m=raw["squad_value_m"],
        avg_age=raw["avg_age"],
        squad_depth=raw["squad_depth"],
        bench_quality=raw["bench_quality"],
        wc_titles=raw["wc_titles"],
        wc_best_result=raw["wc_best_result"],
        wc_appearances=raw["wc_appearances"],
        coach=raw.get("coach", ""),
        coach_rating=raw.get("coach_rating", 7.0),
        attack=attack,
        defense=defense,
        advanced=advanced,
        tactics=tactics,
        key_players=[build_player(p) for p in raw.get("key_players", [])],
        injured_players=[build_player(p) for p in raw.get("injured_players", [])],
        suspended_players=[build_player(p) for p in raw.get("suspended_players", [])],
        recent_matches=[build_match(m) for m in raw.get("recent_matches", [])],
    )


def get_team(code: str) -> TeamData:
    """Return TeamData for the given 3-letter FIFA code (case-insensitive)."""
    raw_db = _load_raw()
    code_upper = code.upper()
    if code_upper not in raw_db:
        available = ", ".join(sorted(raw_db.keys()))
        raise ValueError(f"Team '{code}' not found. Available: {available}")
    return _build_team(raw_db[code_upper])


def get_market_data(code: str) -> Optional[MarketData]:
    """Return MarketData for a team or None if not present."""
    raw_db = _load_raw()
    code_upper = code.upper()
    if code_upper not in raw_db:
        return None
    raw = raw_db[code_upper]
    md = raw.get("market_data")
    if not md:
        return None
    return MarketData(
        odds_home=md["odds_home"],
        odds_draw=md["odds_draw"],
        odds_away=md["odds_away"],
        asian_handicap_line=md["asian_handicap_line"],
        asian_handicap_home_odds=md["asian_handicap_home_odds"],
        asian_handicap_away_odds=md["asian_handicap_away_odds"],
        ou_line=md["ou_line"],
        over_odds=md["over_odds"],
        under_odds=md["under_odds"],
    )


def list_teams() -> list[str]:
    return sorted(_load_raw().keys())
