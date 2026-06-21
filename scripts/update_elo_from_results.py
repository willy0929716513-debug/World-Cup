#!/usr/bin/env python3
"""
Update team ELO ratings and strength metrics based on actual WC2026 results.

Reads docs/data/results.json → updates data/teams.json + ALL_ELOS in
src/tournament/simulator.py.

ELO formula: K=40 (FIFA standard for major tournaments)
Strength update: Bayesian blend of pre-WC baseline with observed goals.
The pre_wc_attack / pre_wc_defense fields in teams.json are the FIXED priors
— they never change. This makes each CI run fully idempotent.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT      = Path(__file__).parent.parent
RESULTS_FILE   = REPO_ROOT / "docs" / "data" / "results.json"
TEAMS_FILE     = REPO_ROOT / "data" / "teams.json"
SIMULATOR_FILE = REPO_ROOT / "src" / "tournament" / "simulator.py"

K = 40          # FIFA K-factor for major international tournaments
PRIOR_WEIGHT = 10  # virtual games' worth of confidence in pre-tournament prior


def _expected(elo_a: float, elo_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))


def _actual(g_a: int, g_b: int) -> float:
    if g_a > g_b:  return 1.0
    if g_a == g_b: return 0.5
    return 0.0


def _elo_update(elo_a: float, elo_b: float, g_a: int, g_b: int) -> tuple[float, float]:
    e = _expected(elo_a, elo_b)
    w = _actual(g_a, g_b)
    return elo_a + K * (w - e), elo_b + K * (1 - w - (1 - e))


def main() -> None:
    print("⚡  WC2026 ELO & strength updater")

    if not RESULTS_FILE.exists():
        print("   No results.json found — nothing to update.")
        return

    results_data = json.loads(RESULTS_FILE.read_text())
    matches = results_data.get("matches", [])
    if not matches:
        print("   No completed matches — nothing to update.")
        return

    print(f"   {len(matches)} completed match(es) found\n")

    # ── Load current ELOs from teams.json ────────────────────────────────────
    teams_raw = json.loads(TEAMS_FILE.read_text())
    elos: dict[str, float] = {
        code: float(team.get("elo_rating", 1800))
        for code, team in teams_raw.items()
    }

    # ── Also collect baseline ELOs from simulator.py ALL_ELOS (for teams
    #    not in data/teams.json) ────────────────────────────────────────────
    sim_content = SIMULATOR_FILE.read_text()
    for m in re.finditer(r"'([A-Z]{2,3})':\s*(\d+)", sim_content):
        code, elo = m.group(1), int(m.group(2))
        if code not in elos:
            elos[code] = float(elo)

    # ── Accumulate actual goals per team ─────────────────────────────────────
    goals_scored:    dict[str, list[int]] = {}
    goals_conceded:  dict[str, list[int]] = {}

    sorted_matches = sorted(matches, key=lambda m: m["date"])

    for m in sorted_matches:
        t1, t2 = m["t1"], m["t2"]
        s1, s2 = int(m["score1"]), int(m["score2"])

        if t1 not in elos or t2 not in elos:
            print(f"  ⚠  Unknown team: {t1} or {t2} — skipped")
            continue

        old1, old2 = elos[t1], elos[t2]
        new1, new2 = _elo_update(old1, old2, s1, s2)
        elos[t1], elos[t2] = new1, new2

        goals_scored.setdefault(t1, []).append(s1)
        goals_conceded.setdefault(t1, []).append(s2)
        goals_scored.setdefault(t2, []).append(s2)
        goals_conceded.setdefault(t2, []).append(s1)

        print(
            f"  {t1} {s1}–{s2} {t2}  →  "
            f"{t1}: {round(old1)}→{round(new1)}  "
            f"{t2}: {round(old2)}→{round(new2)}"
        )

    # ── Write updated ELOs + blended attack/defense to data/teams.json ───────
    updated = 0
    for code, team in teams_raw.items():
        new_elo = round(elos.get(code, team.get("elo_rating", 1800)))
        old_elo = team.get("elo_rating")
        if old_elo != new_elo:
            team["elo_rating"] = new_elo
            updated += 1

        if code in goals_scored:
            n      = len(goals_scored[code])
            gf_act = sum(goals_scored[code]) / n
            ga_act = sum(goals_conceded[code]) / n

            # ALWAYS use pre-WC baseline as prior (not current, which may be
            # compounded from prior CI runs). This makes each run idempotent.
            attack  = team["attack"]
            defense = team["defense"]
            pre_atk = team.get("pre_wc_attack", attack)
            pre_def = team.get("pre_wc_defense", defense)

            prior_gf = pre_atk.get("goals_per_game", gf_act)
            prior_ga = pre_def.get("goals_against_per_game", ga_act)

            blend_gf = (prior_gf * PRIOR_WEIGHT + gf_act * n) / (PRIOR_WEIGHT + n)
            blend_ga = (prior_ga * PRIOR_WEIGHT + ga_act * n) / (PRIOR_WEIGHT + n)

            team["attack"]["goals_per_game"]          = round(blend_gf, 2)
            team["attack"]["xg_per_game"]             = round(blend_gf * 0.96, 2)
            team["defense"]["goals_against_per_game"] = round(blend_ga, 2)
            team["defense"]["xga_per_game"]           = round(blend_ga * 1.03, 2)

    TEAMS_FILE.write_text(json.dumps(teams_raw, ensure_ascii=False, indent=2))
    print(f"\n💾  data/teams.json: {updated} ELO rating(s) updated")

    # ── Patch ALL_ELOS in src/tournament/simulator.py ────────────────────────
    patched = 0
    new_sim = sim_content
    for code, new_elo in elos.items():
        pattern = rf"('{re.escape(code)}':\s*)\d+"
        replacement = rf"\g<1>{round(new_elo)}"
        result, n = re.subn(pattern, replacement, new_sim)
        if n:
            new_sim = result
            patched += 1

    SIMULATOR_FILE.write_text(new_sim)
    print(f"💾  simulator.py: {patched} ALL_ELOS entry/entries updated")


if __name__ == "__main__":
    main()
