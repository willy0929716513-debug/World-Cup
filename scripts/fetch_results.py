#!/usr/bin/env python3
"""
Fetch 2026 World Cup match results and update docs/data/results.json.

Primary source: ESPN public scoreboard API (no key required)
Fallback:       football-data.org (requires FOOTBALL_API_KEY env var)
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import date, timedelta
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent
RESULTS_FILE = REPO_ROOT / "docs" / "data" / "results.json"

# ── Team display name → our 3-letter code ────────────────────────────────
# Covers ESPN displayName, football-data.org name, and common variants
NAME_TO_CODE = {
    # Group A
    "Mexico": "MEX", "South Africa": "RSA",
    "South Korea": "KOR", "Korea Republic": "KOR", "Korea DPR": "KOR",
    "Czech Republic": "CZE", "Czechia": "CZE",
    # Group B
    "Canada": "CAN",
    "Bosnia and Herzegovina": "BIH", "Bosnia-Herzegovina": "BIH", "Bosnia & Herzegovina": "BIH",
    "Switzerland": "SUI", "Qatar": "QAT",
    # Group C
    "Brazil": "BRA", "Morocco": "MAR", "Scotland": "SCO", "Haiti": "HAI",
    # Group D
    "United States": "USA", "USA": "USA",
    "Paraguay": "PAR", "Australia": "AUS", "Turkey": "TUR", "Türkiye": "TUR",
    # Group E
    "Germany": "GER",
    "Curacao": "CUW", "Curaçao": "CUW", "Curaçao": "CUW",
    "Ivory Coast": "CIV", "Côte d'Ivoire": "CIV", "Cote d'Ivoire": "CIV",
    "Cote D'Ivoire": "CIV", "Côte D'Ivoire": "CIV",
    "Ecuador": "ECU",
    # Group F
    "Netherlands": "NED", "Japan": "JPN", "Sweden": "SWE", "Tunisia": "TUN",
    # Group G
    "Belgium": "BEL", "Egypt": "EGY", "Iran": "IRN", "New Zealand": "NZL",
    # Group H
    "Spain": "ESP",
    "Cape Verde": "CPV", "Cabo Verde": "CPV", "Cape Verde Islands": "CPV",
    "Saudi Arabia": "KSA", "Uruguay": "URU",
    # Group I
    "France": "FRA", "Senegal": "SEN", "Iraq": "IRQ", "Norway": "NOR",
    # Group J
    "Argentina": "ARG", "Algeria": "ALG", "Austria": "AUT", "Jordan": "JOR",
    # Group K
    "Portugal": "POR",
    "DR Congo": "COD", "Congo DR": "COD", "Congo, DR": "COD",
    "Democratic Republic of Congo": "COD", "Democratic Republic of the Congo": "COD",
    "Uzbekistan": "UZB", "Colombia": "COL",
    # Group L
    "England": "ENG", "Croatia": "CRO", "Ghana": "GHA", "Panama": "PAN",
}

# ── Actual WC2026 group assignments ───────────────────────────────────────
TEAM_GROUP = {
    "MEX": "A", "RSA": "A", "KOR": "A", "CZE": "A",
    "CAN": "B", "BIH": "B", "SUI": "B", "QAT": "B",
    "BRA": "C", "MAR": "C", "SCO": "C", "HAI": "C",
    "USA": "D", "PAR": "D", "AUS": "D", "TUR": "D",
    "GER": "E", "CUW": "E", "CIV": "E", "ECU": "E",
    "NED": "F", "JPN": "F", "SWE": "F", "TUN": "F",
    "BEL": "G", "EGY": "G", "IRN": "G", "NZL": "G",
    "ESP": "H", "CPV": "H", "KSA": "H", "URU": "H",
    "FRA": "I", "SEN": "I", "IRQ": "I", "NOR": "I",
    "ARG": "J", "ALG": "J", "AUT": "J", "JOR": "J",
    "POR": "K", "COD": "K", "UZB": "K", "COL": "K",
    "ENG": "L", "CRO": "L", "GHA": "L", "PAN": "L",
}

# ── Canonical schedule pairs (t1=first-listed, t2=second) ─────────────────
# Used to ensure consistent home/away ordering in results.json
CANONICAL_PAIRS = {
    frozenset(["MEX","RSA"]): ("MEX","RSA"), frozenset(["KOR","CZE"]): ("KOR","CZE"),
    frozenset(["USA","PAR"]): ("USA","PAR"), frozenset(["CAN","BIH"]): ("CAN","BIH"),
    frozenset(["SUI","QAT"]): ("SUI","QAT"), frozenset(["BRA","MAR"]): ("BRA","MAR"),
    frozenset(["SCO","HAI"]): ("SCO","HAI"), frozenset(["AUS","TUR"]): ("AUS","TUR"),
    frozenset(["GER","CUW"]): ("GER","CUW"), frozenset(["NED","JPN"]): ("NED","JPN"),
    frozenset(["CIV","ECU"]): ("CIV","ECU"), frozenset(["SWE","TUN"]): ("SWE","TUN"),
    frozenset(["ESP","CPV"]): ("ESP","CPV"), frozenset(["BEL","EGY"]): ("BEL","EGY"),
    frozenset(["KSA","URU"]): ("KSA","URU"), frozenset(["IRN","NZL"]): ("IRN","NZL"),
    frozenset(["FRA","SEN"]): ("FRA","SEN"), frozenset(["IRQ","NOR"]): ("IRQ","NOR"),
    frozenset(["ARG","ALG"]): ("ARG","ALG"), frozenset(["AUT","JOR"]): ("AUT","JOR"),
    frozenset(["POR","COD"]): ("POR","COD"), frozenset(["ENG","CRO"]): ("ENG","CRO"),
    frozenset(["GHA","PAN"]): ("GHA","PAN"), frozenset(["UZB","COL"]): ("UZB","COL"),
    frozenset(["CZE","RSA"]): ("CZE","RSA"), frozenset(["SUI","BIH"]): ("SUI","BIH"),
    frozenset(["CAN","QAT"]): ("CAN","QAT"), frozenset(["MEX","KOR"]): ("MEX","KOR"),
    frozenset(["USA","AUS"]): ("USA","AUS"), frozenset(["SCO","MAR"]): ("SCO","MAR"),
    frozenset(["BRA","HAI"]): ("BRA","HAI"), frozenset(["TUR","PAR"]): ("TUR","PAR"),
    frozenset(["NED","SWE"]): ("NED","SWE"), frozenset(["GER","CIV"]): ("GER","CIV"),
    frozenset(["ECU","CUW"]): ("ECU","CUW"), frozenset(["TUN","JPN"]): ("TUN","JPN"),
    frozenset(["ESP","KSA"]): ("ESP","KSA"), frozenset(["BEL","IRN"]): ("BEL","IRN"),
    frozenset(["URU","CPV"]): ("URU","CPV"), frozenset(["NZL","EGY"]): ("NZL","EGY"),
    frozenset(["ARG","AUT"]): ("ARG","AUT"), frozenset(["FRA","IRQ"]): ("FRA","IRQ"),
    frozenset(["NOR","SEN"]): ("NOR","SEN"), frozenset(["JOR","ALG"]): ("JOR","ALG"),
    frozenset(["POR","UZB"]): ("POR","UZB"), frozenset(["ENG","GHA"]): ("ENG","GHA"),
    frozenset(["PAN","CRO"]): ("PAN","CRO"), frozenset(["COL","COD"]): ("COL","COD"),
    frozenset(["SUI","CAN"]): ("SUI","CAN"), frozenset(["BIH","QAT"]): ("BIH","QAT"),
    frozenset(["SCO","BRA"]): ("SCO","BRA"), frozenset(["MAR","HAI"]): ("MAR","HAI"),
    frozenset(["CZE","MEX"]): ("CZE","MEX"), frozenset(["RSA","KOR"]): ("RSA","KOR"),
    frozenset(["ECU","GER"]): ("ECU","GER"), frozenset(["CUW","CIV"]): ("CUW","CIV"),
    frozenset(["JPN","SWE"]): ("JPN","SWE"), frozenset(["TUN","NED"]): ("TUN","NED"),
    frozenset(["TUR","USA"]): ("TUR","USA"), frozenset(["PAR","AUS"]): ("PAR","AUS"),
    frozenset(["NOR","FRA"]): ("NOR","FRA"), frozenset(["SEN","IRQ"]): ("SEN","IRQ"),
    frozenset(["CPV","KSA"]): ("CPV","KSA"), frozenset(["URU","ESP"]): ("URU","ESP"),
    frozenset(["EGY","IRN"]): ("EGY","IRN"), frozenset(["NZL","BEL"]): ("NZL","BEL"),
    frozenset(["PAN","ENG"]): ("PAN","ENG"), frozenset(["CRO","GHA"]): ("CRO","GHA"),
    frozenset(["COL","POR"]): ("COL","POR"), frozenset(["COD","UZB"]): ("COD","UZB"),
    frozenset(["JOR","ARG"]): ("JOR","ARG"), frozenset(["ALG","AUT"]): ("ALG","AUT"),
}

# WC2026 knockout stage date ranges (inclusive) → round code
_KO_RANGES = [
    (date(2026, 6, 28), date(2026, 7,  3), "r32"),
    (date(2026, 7,  4), date(2026, 7,  8), "r16"),
    (date(2026, 7,  9), date(2026, 7, 12), "qf"),
    (date(2026, 7, 13), date(2026, 7, 16), "sf"),
    (date(2026, 7, 17), date(2026, 7, 19), "final"),
]

def round_for_date(d: date) -> str | None:
    for start, end, rnd in _KO_RANGES:
        if start <= d <= end:
            return rnd
    return None

# football-data.org — same as NAME_TO_CODE (reuse)
FD_NAME_TO_CODE = NAME_TO_CODE


def fetch_url(url, headers=None):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; WC2026-bot/1.0)",
        **(headers or {}),
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        print(f"  ⚠  GET {url[:60]}... failed: {e}")
        return None


def resolve_code(name):
    return NAME_TO_CODE.get(name) or FD_NAME_TO_CODE.get(name)


def fetch_espn(start_date: date, end_date: date) -> list[dict]:
    """Fetch completed matches from ESPN scoreboard API."""
    results = []
    d = start_date
    while d <= end_date:
        ds = d.strftime("%Y%m%d")
        url = (
            "https://site.api.espn.com/apis/site/v2/sports/soccer/"
            f"fifa.world/scoreboard?dates={ds}"
        )
        data = fetch_url(url)
        if not data:
            d += timedelta(days=1)
            continue

        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            status = comp.get("status", {}).get("type", {}).get("name", "")
            if status not in ("STATUS_FINAL", "STATUS_FULL_TIME"):
                continue

            competitors = comp.get("competitors", [])
            if len(competitors) != 2:
                continue

            # ESPN puts home first
            home = competitors[0]
            away = competitors[1]
            h_name = home.get("team", {}).get("displayName", "")
            a_name = away.get("team", {}).get("displayName", "")
            h_code = resolve_code(h_name)
            a_code = resolve_code(a_name)
            if not h_code or not a_code:
                print(f"  ⚠  Unknown team names: {h_name!r} vs {a_name!r}")
                continue

            try:
                h_score = int(home.get("score", -1))
                a_score = int(away.get("score", -1))
            except (ValueError, TypeError):
                continue
            if h_score < 0 or a_score < 0:
                continue

            pair_key = frozenset([h_code, a_code])
            canonical = CANONICAL_PAIRS.get(pair_key)
            if canonical:
                # Group stage: use canonical team ordering
                t1, t2 = canonical
                s1 = h_score if t1 == h_code else a_score
                s2 = a_score if t1 == h_code else h_score
                group = TEAM_GROUP.get(t1, "?")
                results.append({
                    "t1": t1, "t2": t2,
                    "score1": s1, "score2": s2,
                    "group": group, "played": True,
                    "date": d.isoformat(),
                })
            else:
                # Not a group-stage pair — check if it's a knockout match by date
                rnd = round_for_date(d)
                if not rnd:
                    print(f"  ⚠  Unknown match (not in schedule or knockout dates): {h_code} vs {a_code}")
                    continue
                print(f"  🏆  {rnd.upper()}: {h_code} {h_score}–{a_score} {a_code}")
                results.append({
                    "t1": h_code, "t2": a_code,
                    "score1": h_score, "score2": a_score,
                    "round": rnd, "played": True,
                    "date": d.isoformat(),
                })

        d += timedelta(days=1)

    return results


def fetch_football_data(api_key: str) -> list[dict]:
    """Fetch completed matches from football-data.org."""
    url = "https://api.football-data.org/v4/competitions/WC/matches?status=FINISHED"
    data = fetch_url(url, headers={"X-Auth-Token": api_key})
    if not data:
        return []

    results = []
    for m in data.get("matches", []):
        ht = m.get("homeTeam", {}).get("name", "")
        at = m.get("awayTeam", {}).get("name", "")
        h_code = resolve_code(ht)
        a_code = resolve_code(at)
        if not h_code or not a_code:
            print(f"  ⚠  Unknown team: {ht!r} vs {at!r}")
            continue

        score = m.get("score", {}).get("fullTime", {})
        h_score = score.get("home")
        a_score = score.get("away")
        if h_score is None or a_score is None:
            continue

        match_date = (m.get("utcDate", "") or "")[:10]
        group_name = m.get("group", "") or ""
        group = group_name.replace("GROUP_", "") if group_name else None

        _FD_STAGE_MAP = {
            "ROUND_OF_32": "r32", "ROUND_OF_16": "r16",
            "QUARTER_FINALS": "qf", "SEMI_FINALS": "sf",
            "THIRD_PLACE": "final", "FINAL": "final",
        }
        stage_name = m.get("stage", "") or ""
        rnd = _FD_STAGE_MAP.get(stage_name)

        if group:
            results.append({
                "t1": h_code, "t2": a_code,
                "score1": int(h_score), "score2": int(a_score),
                "group": group, "played": True,
                "date": match_date,
            })
        elif rnd:
            results.append({
                "t1": h_code, "t2": a_code,
                "score1": int(h_score), "score2": int(a_score),
                "round": rnd, "played": True,
                "date": match_date,
            })
        else:
            print(f"  ⚠  Skipping {h_code} vs {a_code}: no group or known stage ({stage_name!r})")

    return results


def load_existing() -> dict:
    if RESULTS_FILE.exists():
        return json.loads(RESULTS_FILE.read_text())
    return {"note": "實際比賽結果 — 手動更新", "matches": []}


def merge(existing: list[dict], fetched: list[dict]) -> tuple[list[dict], int]:
    """Merge fetched results into existing list, deduplicating by team pair."""
    seen = set()
    for m in existing:
        seen.add((m["t1"], m["t2"]))
        seen.add((m["t2"], m["t1"]))

    added = 0
    merged = list(existing)
    for m in fetched:
        key = (m["t1"], m["t2"])
        if key not in seen:
            merged.append(m)
            seen.add(key)
            seen.add((m["t2"], m["t1"]))
            added += 1
            print(f"  ✅  NEW: {m['t1']} {m['score1']}–{m['score2']} {m['t2']}  ({m['date']})")

    merged.sort(key=lambda x: (x["date"], x.get("group", "")))
    return merged, added


def main():
    print("⚽  WC2026 result fetcher")
    existing_data = load_existing()
    existing = existing_data.get("matches", [])
    print(f"   Existing results: {len(existing)}")

    # Date range: tournament start → today
    start = date(2026, 6, 11)
    today = date.today()

    fetched: list[dict] = []

    # ── Primary: ESPN (no key) ────────────────────────────────────────────
    print(f"\n📡  ESPN: scanning {start} → {today}")
    espn_results = fetch_espn(start, today)
    print(f"   ESPN returned {len(espn_results)} completed match(es)")
    fetched.extend(espn_results)

    # ── Fallback: football-data.org ───────────────────────────────────────
    api_key = os.environ.get("FOOTBALL_API_KEY", "")
    if api_key:
        print("\n📡  football-data.org fallback...")
        fd_results = fetch_football_data(api_key)
        print(f"   football-data.org returned {len(fd_results)} completed match(es)")
        fetched.extend(fd_results)

    # ── Merge ─────────────────────────────────────────────────────────────
    print("\n🔀  Merging...")
    merged, added = merge(existing, fetched)

    if added == 0:
        print("\n✅  No new results — results.json unchanged.")
        _write_gha_output("new_results", "false")
        sys.exit(0)

    existing_data["matches"] = merged
    existing_data["updated"] = today.isoformat()
    RESULTS_FILE.write_text(json.dumps(existing_data, ensure_ascii=False, indent=2))
    print(f"\n💾  Saved {len(merged)} total results (+{added} new) → {RESULTS_FILE}")
    _write_gha_output("new_results", "true")


def _write_gha_output(key: str, value: str) -> None:
    """Write a key=value pair to GITHUB_OUTPUT (no-op outside Actions)."""
    gha = os.environ.get("GITHUB_OUTPUT", "")
    if gha:
        with open(gha, "a") as f:
            f.write(f"{key}={value}\n")


if __name__ == "__main__":
    main()
