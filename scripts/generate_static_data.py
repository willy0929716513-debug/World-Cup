#!/usr/bin/env python3
"""
Generate all static JSON data for GitHub Pages deployment.

Output:
  docs/data/tournament.json   - group probs, bracket, champion probs, team names
  docs/data/teams.json        - team list for dropdowns
  docs/data/matches/*.json    - per-pair match predictions
"""
from __future__ import annotations
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from itertools import combinations

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DOCS_DATA   = ROOT / 'docs' / 'data'
MATCHES_DIR = DOCS_DATA / 'matches'
DOCS_DATA.mkdir(parents=True, exist_ok=True)
MATCHES_DIR.mkdir(exist_ok=True)

from src.tournament.simulator import (
    simulate_tournament, GROUPS, GROUP_LIST, TEAM_NAMES,
    CONFEDERATIONS, ALL_ELOS, elo_to_lambdas,
)
from src.data.loader import get_team, get_market_data, list_teams
from src.models import ensemble

NOW = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


# ── Serialisation helpers (mirrors web/app.py) ─────────────────────────────────

def _team_to_dict(team) -> dict:
    return {
        "name":           team.name,
        "short_name":     team.short_name,
        "code":           team.code,
        "confederation":  team.confederation,
        "fifa_ranking":   team.fifa_ranking,
        "elo_rating":     team.elo_rating,
        "spi_rating":     team.spi_rating,
        "squad_value_m":  team.squad_value_m,
        "avg_age":        team.avg_age,
        "squad_depth":    team.squad_depth,
        "bench_quality":  team.bench_quality,
        "wc_titles":      team.wc_titles,
        "wc_best_result": team.wc_best_result,
        "wc_appearances": team.wc_appearances,
        "coach":          team.coach,
        "coach_rating":   team.coach_rating,
        "attack": {
            "goals_per_game":              team.attack.goals_per_game,
            "xg_per_game":                 team.attack.xg_per_game,
            "npxg_per_game":               team.attack.npxg_per_game,
            "shots_per_game":              team.attack.shots_per_game,
            "shots_on_target_per_game":    team.attack.shots_on_target_per_game,
            "shots_in_box_per_game":       team.attack.shots_in_box_per_game,
            "big_chances_per_game":        team.attack.big_chances_per_game,
            "conversion_rate":             round(team.attack.conversion_rate * 100, 1),
            "counter_goals_pct":           team.attack.counter_goals_pct,
            "set_piece_goals_pct":         team.attack.set_piece_goals_pct,
            "corners_per_game":            team.attack.corners_per_game,
            "cross_accuracy_pct":          team.attack.cross_accuracy_pct,
            "key_passes_per_game":         team.attack.key_passes_per_game,
            "possession_pct":              team.attack.possession_pct,
            "pass_accuracy_pct":           team.attack.pass_accuracy_pct,
        },
        "defense": {
            "goals_against_per_game":      team.defense.goals_against_per_game,
            "xga_per_game":                team.defense.xga_per_game,
            "clean_sheet_pct":             team.defense.clean_sheet_pct,
            "shots_against_per_game":      team.defense.shots_against_per_game,
            "sot_against_per_game":        team.defense.sot_against_per_game,
            "tackle_success_pct":          team.defense.tackle_success_pct,
            "interceptions_per_game":      team.defense.interceptions_per_game,
            "clearances_per_game":         team.defense.clearances_per_game,
            "aerial_success_pct":          team.defense.aerial_success_pct,
            "gk_save_pct":                 team.defense.gk_save_pct,
            "gk_psxg_ga":                  team.defense.gk_psxg_ga,
        },
        "advanced": {
            "ppda":                        team.advanced.ppda,
            "field_tilt":                  team.advanced.field_tilt,
            "deep_completion_per_game":    team.advanced.deep_completion_per_game,
            "progressive_passes":          team.advanced.progressive_passes,
            "progressive_carries":         team.advanced.progressive_carries,
            "shot_creating_actions":       team.advanced.shot_creating_actions,
            "goal_creating_actions":       team.advanced.goal_creating_actions,
            "xpts_per_game":               team.advanced.xpts_per_game,
        },
        "tactics": {
            "primary_formation":   team.tactics.primary_formation,
            "secondary_formation": team.tactics.secondary_formation,
            "possession_style":    team.tactics.possession_style,
            "high_press":          team.tactics.high_press,
            "press_intensity":     team.tactics.press_intensity,
            "defensive_line":      team.tactics.defensive_line,
            "wide_play_pct":       team.tactics.wide_play_pct,
            "set_piece_quality":   team.tactics.set_piece_quality,
            "tactical_flexibility":team.tactics.tactical_flexibility,
        },
        "key_players": [
            {
                "name":           p.name,
                "position":       p.position,
                "club":           p.club,
                "age":            p.age,
                "market_value_m": p.market_value_m,
                "goals_season":   p.goals_season,
                "assists_season": p.assists_season,
                "form_rating":    p.form_rating,
                "is_injured":     p.is_injured,
                "is_suspended":   p.is_suspended,
                "injury_detail":  p.injury_detail,
            }
            for p in team.key_players
        ],
        "injured_players": [
            {"name": p.name, "position": p.position, "detail": p.injury_detail}
            for p in team.injured_players
        ],
        "suspended_players": [
            {"name": p.name, "position": p.position}
            for p in team.suspended_players
        ],
        "recent_form":        [m.outcome for m in team.recent_matches[-10:]],
        "form_pts_5":         round(team.form_pts(5), 2),
        "form_pts_10":        round(team.form_pts(10), 2),
        "win_rate_10":        round(team.win_rate(10) * 100, 1),
        "goals_scored_10":    round(team.goals_scored_avg(10), 2),
        "goals_conceded_10":  round(team.goals_conceded_avg(10), 2),
    }


def _result_to_dict(result, market=None) -> dict:
    score_matrix = [
        [round(result.score_probs.get((h, a), 0.0) * 100, 2) for a in range(6)]
        for h in range(6)
    ]
    top10 = [
        {
            "home": h, "away": a,
            "prob": round(p * 100, 2),
            "type": "home" if h > a else "away" if a > h else "draw",
        }
        for (h, a), p in result.most_likely_scores[:10]
    ]
    tg = result.total_goal_probs()
    goal_dist = [
        {
            "label": f"{g}+" if g == 6 else str(g),
            "prob": round((sum(v for k, v in tg.items() if k >= g) if g == 6
                           else tg.get(g, 0.0)) * 100, 2),
        }
        for g in range(7)
    ]
    cold = [
        {"home": h, "away": a, "prob": round(p * 100, 2), "odds": round(1.0 / p, 1)}
        for (h, a), p in sorted(
            [(k, v) for k, v in result.score_probs.items() if v >= 0.01 and sum(k) >= 4],
            key=lambda x: -x[1],
        )[:3]
    ]
    models = [
        {
            "name":     r.model_name,
            "p_home":   round(r.p_home * 100, 1),
            "p_draw":   round(r.p_draw * 100, 1),
            "p_away":   round(r.p_away * 100, 1),
            "lam_home": round(r.lambda_home, 2),
            "lam_away": round(r.lambda_away, 2),
        }
        for r in result.model_results
    ]
    betting = None
    if market:
        p_over  = sum(v for k, v in tg.items() if k > market.ou_line)
        p_under = 1.0 - p_over
        def edge(tp, odds):
            return round((tp - 1.0 / odds) * 100, 1)
        betting = {
            "home":  {"odds": market.odds_home,  "implied": round(100/market.odds_home, 1),
                      "model": round(result.p_home*100, 1),  "edge": edge(result.p_home, market.odds_home)},
            "draw":  {"odds": market.odds_draw,  "implied": round(100/market.odds_draw, 1),
                      "model": round(result.p_draw*100, 1),  "edge": edge(result.p_draw, market.odds_draw)},
            "away":  {"odds": market.odds_away,  "implied": round(100/market.odds_away, 1),
                      "model": round(result.p_away*100, 1),  "edge": edge(result.p_away, market.odds_away)},
            "over":  {"line": market.ou_line, "odds": market.over_odds,
                      "implied": round(100/market.over_odds, 1),
                      "model": round(p_over*100, 1),  "edge": edge(p_over, market.over_odds)},
            "under": {"line": market.ou_line, "odds": market.under_odds,
                      "implied": round(100/market.under_odds, 1),
                      "model": round(p_under*100, 1), "edge": edge(p_under, market.under_odds)},
            "ah_line":      market.asian_handicap_line,
            "ah_home_odds": market.asian_handicap_home_odds,
            "ah_away_odds": market.asian_handicap_away_odds,
        }
    return {
        "p_home":       round(result.p_home * 100, 1),
        "p_draw":       round(result.p_draw * 100, 1),
        "p_away":       round(result.p_away * 100, 1),
        "lambda_home":  round(result.lambda_home, 2),
        "lambda_away":  round(result.lambda_away, 2),
        "btts_yes":     round(result.btts_prob() * 100, 1),
        "btts_no":      round((1 - result.btts_prob()) * 100, 1),
        "score_matrix": score_matrix,
        "top10":        top10,
        "goal_dist":    goal_dist,
        "cold":         cold,
        "models":       models,
        "betting":      betting,
    }


def _confidence(p_home, p_draw, p_away):
    dom = max(p_home, p_draw, p_away)
    if dom >= 0.62: return 9, "極高信心"
    if dom >= 0.55: return 8, "高信心"
    if dom >= 0.48: return 7, "中高信心"
    if dom >= 0.42: return 6, "中等信心"
    if dom >= 0.36: return 5, "中低信心"
    return 4, "低信心"


# ── 1. Tournament simulation ───────────────────────────────────────────────────

print("▶ Running tournament simulation (n=10000)…")
sim = simulate_tournament(n=10_000)

# Build group match predicted scores using ensemble model for accurate results
group_matches: dict[str, list[dict]] = {}
print("▶ Computing group stage match predictions…")
for grp in GROUP_LIST:
    grp_teams = GROUPS[grp]
    ms = []
    for t1, t2 in combinations(grp_teams, 2):
        try:
            ht = get_team(t1)
            at = get_team(t2)
            res = ensemble.run(ht, at, market_data=None, neutral=True)
            # Most likely score from top-10
            best = res.most_likely_scores[0][0] if res.most_likely_scores else (1, 1)
            score_str = f"{best[0]}-{best[1]}"
            ms.append({
                "t1": t1, "score": score_str, "t2": t2,
                "p_home": round(res.p_home * 100, 1),
                "p_draw": round(res.p_draw * 100, 1),
                "p_away": round(res.p_away * 100, 1),
            })
        except Exception:
            lh, la = elo_to_lambdas(ALL_ELOS[t1], ALL_ELOS[t2])
            ms.append({"t1": t1, "score": f"{int(lh)}-{int(la)}", "t2": t2,
                       "p_home": 0, "p_draw": 0, "p_away": 0})
    group_matches[grp] = ms

tournament_doc = {
    "generated_at":             NOW,
    "n_sim":                    10_000,
    "group_probs":              sim["group_probs"],
    "predicted_group_standings":sim["predicted_group_standings"],
    "group_matches":            group_matches,
    "expected_bracket":         sim["expected_bracket"],
    "tournament_probs":         sim["tournament_probs"],
    "team_names":               TEAM_NAMES,
    "confederations":           CONFEDERATIONS,
    "groups":                   GROUPS,
}

with open(DOCS_DATA / "tournament.json", "w", encoding="utf-8") as f:
    json.dump(tournament_doc, f, ensure_ascii=False)
print("  ✅ docs/data/tournament.json")


# ── 2. Teams list (detailed teams from data/teams.json) ────────────────────────

print("▶ Building teams list…")
teams_list = []
for code in list_teams():
    try:
        t = get_team(code)
        teams_list.append({"code": code, "name": t.name,
                            "rank": t.fifa_ranking, "conf": t.confederation})
    except Exception:
        pass
teams_list.sort(key=lambda x: x["rank"])

with open(DOCS_DATA / "teams.json", "w", encoding="utf-8") as f:
    json.dump({"generated_at": NOW, "teams": teams_list}, f, ensure_ascii=False)
print(f"  ✅ docs/data/teams.json ({len(teams_list)} teams)")


# ── 3. Match predictions ───────────────────────────────────────────────────────

team_codes = [t["code"] for t in teams_list]
pairs = [(h, a) for h in team_codes for a in team_codes if h != a]
print(f"▶ Generating {len(pairs)} match predictions…")

ok = 0
for home_code, away_code in pairs:
    out_path = MATCHES_DIR / f"{home_code}_vs_{away_code}.json"
    try:
        home_team = get_team(home_code)
        away_team = get_team(away_code)
        market    = get_market_data(home_code)
        res       = ensemble.run(home_team, away_team, market_data=market, neutral=True)

        home_d   = _team_to_dict(home_team)
        away_d   = _team_to_dict(away_team)
        result_d = _result_to_dict(res, market)
        conf_level, conf_label = _confidence(res.p_home, res.p_draw, res.p_away)

        doc = {
            "generated_at": NOW,
            "home":         home_d,
            "away":         away_d,
            "result":       result_d,
            "conf_level":   conf_level,
            "conf_label":   conf_label,
            "match": {
                "date":  "2026-06-14",
                "venue": "MetLife Stadium, East Rutherford, NJ",
                "comp":  "FIFA World Cup 2026",
                "stage": "Group Stage",
            },
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False)
        ok += 1
        print(f"  ✅ {home_code} vs {away_code}")
    except Exception as e:
        print(f"  ⚠  {home_code} vs {away_code}: {e}")

print(f"\n✅ Done — {ok}/{len(pairs)} matches generated")
print(f"   docs/data/ → {sum(1 for _ in DOCS_DATA.rglob('*.json'))} JSON files total")
