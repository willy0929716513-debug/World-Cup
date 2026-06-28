#!/usr/bin/env python3
"""
Patch current_stage in docs/data/tournament.json based on docs/data/results.json.
Lightweight — no Monte Carlo, no external dependencies.
Run after fetch_results.py so stage is always current within 20 minutes.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
RESULTS_FILE = REPO_ROOT / "docs" / "data" / "results.json"
TOURNAMENT_FILE = REPO_ROOT / "docs" / "data" / "tournament.json"


def compute_stage(matches: list) -> dict:
    GROUP_TOTAL = 72
    group_played = sum(1 for m in matches if m.get("played") and m.get("group"))
    if group_played < GROUP_TOTAL:
        return {"stage": "group", "played": group_played, "total": GROUP_TOTAL}
    for rnd, total in [("r32", 16), ("r16", 8), ("qf", 4), ("sf", 2), ("final", 1)]:
        played = sum(1 for m in matches if m.get("played") and m.get("round") == rnd)
        if played < total:
            return {"stage": rnd, "played": played, "total": total}
    return {"stage": "champion", "played": 31, "total": 31}


def main():
    if not RESULTS_FILE.exists():
        print("results.json missing, skipping.")
        return
    if not TOURNAMENT_FILE.exists():
        print("tournament.json missing, skipping.")
        return

    matches = json.loads(RESULTS_FILE.read_text()).get("matches", [])
    stage = compute_stage(matches)

    tournament = json.loads(TOURNAMENT_FILE.read_text())
    old = tournament.get("current_stage", {})
    tournament["current_stage"] = stage
    TOURNAMENT_FILE.write_text(json.dumps(tournament, ensure_ascii=False, indent=2))
    print(f"✅  stage: {old.get('stage','?')} → {stage['stage']} ({stage['played']}/{stage['total']})")


if __name__ == "__main__":
    main()
