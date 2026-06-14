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

# ── Team name → 3-letter code ─────────────────────────────────────────────
NAME_TO_CODE = {
    # Group A
    "Mexico": "MEX", "South Africa": "RSA", "South Korea": "KOR", "Korea Republic": "KOR",
    "Czech Republic": "CZE", "Czechia": "CZE",
    # Group B
    "Canada": "CAN", "Bosnia and Herzegovina": "BIH", "Switzerland": "SUI", "Qatar": "QAT",
    # Group C
    "Brazil": "BRA", "Morocco": "MAR", "Scotland": "SCO", "Haiti": "HAI",
    # Group D
    "United States": "USA", "Paraguay": "PAR", "Australia": "AUS", "Turkey": "TUR", "Türkiye": "TUR",
    # Group E
    "Germany": "GER", "Curacao": "CUW", "Curaçao": "CUW", "Netherlands": "NED",
    "Ivory Coast": "CIV", "Côte d'Ivoire": "CIV", "Cote d'Ivoire": "CIV", "Ecuador": "ECU",
    # Group F
    "Sweden": "SWE", "Tunisia": "TUN", "England": "ENG", "Serbia": "SRB",
    # Group G
    "Portugal": "POR", "Nigeria": "NGA", "Belgium": "BEL", "New Zealand": "NZL",
    # Group H
    "Spain": "ESP", "Cameroon": "CMR", "Japan": "JPN", "Honduras": "HON",
    # Group I
    "Argentina": "ARG", "Iraq": "IRQ", "Croatia": "CRO", "Indonesia": "IDN",
    # Group J
    "France": "FRA", "Panama": "PAN", "Uruguay": "URU", "Senegal": "SEN",
    # Group K
    "Colombia": "COL", "Uzbekistan": "UZB", "Denmark": "DEN", "Romania": "ROU",
    # Group L
    "Saudi Arabia": "KSA", "Mali": "MLI", "Peru": "PER", "Iran": "IRN",
    # ESPN codes that differ
    "South Korea": "KOR", "Bosnia-Herzegovina": "BIH", "Bosnia & Herzegovina": "BIH",
    "Cote D'Ivoire": "CIV",
}

# ── Team → Group lookup ───────────────────────────────────────────────────
TEAM_GROUP = {
    "MEX": "A", "RSA": "A", "KOR": "A", "CZE": "A",
    "CAN": "B", "BIH": "B", "SUI": "B", "QAT": "B",
    "BRA": "C", "MAR": "C", "SCO": "C", "HAI": "C",
    "USA": "D", "PAR": "D", "AUS": "D", "TUR": "D",
    "GER": "E", "CUW": "E", "NED": "E", "CIV": "E",
    "SWE": "F", "TUN": "F", "ENG": "F", "SRB": "F",
    "POR": "G", "NGA": "G", "BEL": "G", "NZL": "G",
    "ESP": "H", "CMR": "H", "JPN": "H", "HON": "H",
    "ARG": "I", "IRQ": "I", "CRO": "I", "IDN": "I",
    "FRA": "J", "PAN": "J", "URU": "J", "SEN": "J",
    "COL": "K", "UZB": "K", "DEN": "K", "ROU": "K",
    "KSA": "L", "MLI": "L", "PER": "L", "IRN": "L",
    # ECU not in group E fixture list — it's actually Group E per CONMEBOL draw
    "ECU": "E",
}

# football-data.org team name mapping
FD_NAME_TO_CODE = {
    "Mexico": "MEX", "South Africa": "RSA", "Korea Republic": "KOR",
    "Czech Republic": "CZE", "Canada": "CAN", "Bosnia and Herzegovina": "BIH",
    "Switzerland": "SUI", "Qatar": "QAT", "Brazil": "BRA", "Morocco": "MAR",
    "Scotland": "SCO", "Haiti": "HAI", "USA": "USA", "United States": "USA",
    "Paraguay": "PAR", "Australia": "AUS", "Türkiye": "TUR", "Germany": "GER",
    "Curaçao": "CUW", "Netherlands": "NED", "Côte d'Ivoire": "CIV",
    "Ecuador": "ECU", "Sweden": "SWE", "Tunisia": "TUN", "England": "ENG",
    "Serbia": "SRB", "Portugal": "POR", "Nigeria": "NGA", "Belgium": "BEL",
    "New Zealand": "NZL", "Spain": "ESP", "Cameroon": "CMR", "Japan": "JPN",
    "Honduras": "HON", "Argentina": "ARG", "Iraq": "IRQ", "Croatia": "CRO",
    "Indonesia": "IDN", "France": "FRA", "Panama": "PAN", "Uruguay": "URU",
    "Senegal": "SEN", "Colombia": "COL", "Uzbekistan": "UZB", "Denmark": "DEN",
    "Romania": "ROU", "Saudi Arabia": "KSA", "Mali": "MLI", "Peru": "PER",
    "Iran": "IRN",
}


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

            group = TEAM_GROUP.get(h_code, "?")
            results.append({
                "t1": h_code, "t2": a_code,
                "score1": h_score, "score2": a_score,
                "group": group, "played": True,
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
        group = group_name.replace("GROUP_", "") if group_name else TEAM_GROUP.get(h_code, "?")

        results.append({
            "t1": h_code, "t2": a_code,
            "score1": int(h_score), "score2": int(a_score),
            "group": group, "played": True,
            "date": match_date,
        })

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
        sys.exit(0)

    existing_data["matches"] = merged
    existing_data["updated"] = today.isoformat()
    RESULTS_FILE.write_text(json.dumps(existing_data, ensure_ascii=False, indent=2))
    print(f"\n💾  Saved {len(merged)} total results (+{added} new) → {RESULTS_FILE}")


if __name__ == "__main__":
    main()
