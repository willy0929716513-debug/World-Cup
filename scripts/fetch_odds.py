#!/usr/bin/env python3
"""
Fetch live WC2026 odds from The Odds API and update data/market_odds.json.

Requires: THE_ODDS_API_KEY environment variable (free tier: 500 req/month)
Get a free key at: https://the-odds-api.com

Status is written to data/odds_status.json for UI verification.
"""
from __future__ import annotations
import json, os, sys, math, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKET_ODDS_PATH = ROOT / "data" / "market_odds.json"
STATUS_PATH      = ROOT / "data" / "odds_status.json"
STATUS_DOCS_PATH = ROOT / "docs" / "data" / "odds_status.json"

API_KEY  = os.environ.get("THE_ODDS_API_KEY", "")
BASE_URL = "https://api.the-odds-api.com/v4/sports/soccer_world_cup/odds"

# ── Team name → our 3-letter code ─────────────────────────────────────────────
NAME_TO_CODE = {
    "Mexico": "MEX", "South Africa": "RSA", "South Korea": "KOR",
    "Korea Republic": "KOR", "Czech Republic": "CZE", "Czechia": "CZE",
    "Canada": "CAN", "Switzerland": "SUI", "Qatar": "QAT", "Bosnia and Herzegovina": "BIH",
    "Bosnia & Herzegovina": "BIH", "Brazil": "BRA", "Morocco": "MAR",
    "Scotland": "SCO", "Haiti": "HAI", "United States": "USA", "USA": "USA",
    "Paraguay": "PAR", "Australia": "AUS", "Turkey": "TUR",
    "Germany": "GER", "Curacao": "CUW", "Curaçao": "CUW",
    "Ivory Coast": "CIV", "Côte d'Ivoire": "CIV", "Ecuador": "ECU",
    "Netherlands": "NED", "Japan": "JPN", "Sweden": "SWE", "Tunisia": "TUN",
    "Belgium": "BEL", "Egypt": "EGY", "Iran": "IRN", "New Zealand": "NZL",
    "Spain": "ESP", "Cape Verde": "CPV", "Cabo Verde": "CPV",
    "Saudi Arabia": "KSA", "Uruguay": "URU",
    "France": "FRA", "Senegal": "SEN", "Iraq": "IRQ", "Norway": "NOR",
    "Argentina": "ARG", "Algeria": "ALG", "Austria": "AUT", "Jordan": "JOR",
    "Portugal": "POR", "DR Congo": "COD", "Congo DR": "COD",
    "Democratic Republic of the Congo": "COD",
    "Uzbekistan": "UZB", "Colombia": "COL",
    "England": "ENG", "Croatia": "CRO", "Ghana": "GHA", "Panama": "PAN",
    "Poland": "POL", "Ukraine": "UKR", "Denmark": "DEN", "Serbia": "SRB",
    "Hungary": "HUN", "Slovakia": "SVK", "Slovakia": "SVK",
    "Burkina Faso": "BUR", "Mali": "MLI", "Tanzania": "TAN",
    "Rwanda": "RWA", "Benin": "BEN", "Cameroon": "CMR",
    "Indonesia": "IDN", "Angola": "ANG", "Costa Rica": "CRC",
    "Honduras": "HON", "Guatemala": "GUA", "Peru": "PER",
    "Bolivia": "BOL", "Venezuela": "VEN", "Jamaica": "JAM",
    "Thailand": "THA", "India": "IND",
}

# Canonical pair: frozenset → (t1, t2)  (matches SCHEDULE order in index.html)
CANONICAL_PAIRS: dict[frozenset, tuple[str, str]] = {}
GROUPS = {
    'A': ['MEX','RSA','KOR','CZE'],
    'B': ['CAN','SUI','QAT','BIH'],
    'C': ['BRA','MAR','SCO','HAI'],
    'D': ['USA','PAR','AUS','TUR'],
    'E': ['GER','CUW','CIV','ECU'],
    'F': ['NED','JPN','SWE','TUN'],
    'G': ['BEL','EGY','IRN','NZL'],
    'H': ['ESP','CPV','KSA','URU'],
    'I': ['FRA','SEN','IRQ','NOR'],
    'J': ['ARG','ALG','AUT','JOR'],
    'K': ['POR','COD','UZB','COL'],
    'L': ['ENG','CRO','GHA','PAN'],
}
for teams in GROUPS.values():
    for i in range(len(teams)):
        for j in range(i+1, len(teams)):
            CANONICAL_PAIRS[frozenset([teams[i], teams[j]])] = (teams[i], teams[j])


def _fetch_json(url: str) -> dict | list:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def fetch_odds() -> list[dict]:
    """Fetch 1X2 + Asian Handicap odds from The Odds API."""
    params = (
        f"?apiKey={API_KEY}"
        f"&regions=eu"
        f"&markets=h2h,asian_handicap"
        f"&bookmakers=pinnacle,bet365,unibet"
        f"&oddsFormat=decimal"
    )
    url = BASE_URL + params
    return _fetch_json(url)


def _best_h2h(bookmakers: list[dict]) -> tuple[float, float, float] | None:
    """Return (home, draw, away) decimal odds from the sharpest available book."""
    priority = ["pinnacle", "bet365", "unibet"]
    bk_map = {b["key"]: b for b in bookmakers}
    for bk_key in priority:
        if bk_key not in bk_map:
            continue
        for mkt in bk_map[bk_key].get("markets", []):
            if mkt["key"] == "h2h" and len(mkt["outcomes"]) == 3:
                oc = {o["name"]: o["price"] for o in mkt["outcomes"]}
                return oc.get("home"), oc.get("Draw") or oc.get("draw"), oc.get("away")
    return None


def _best_ah(bookmakers: list[dict], home_team: str) -> tuple[float, float] | None:
    """Return (line, home_odds) for Asian Handicap, perspective of home_team."""
    priority = ["pinnacle", "bet365", "unibet"]
    bk_map = {b["key"]: b for b in bookmakers}
    for bk_key in priority:
        if bk_key not in bk_map:
            continue
        for mkt in bk_map[bk_key].get("markets", []):
            if mkt["key"] == "asian_handicap":
                for oc in mkt["outcomes"]:
                    if home_team.lower() in oc["name"].lower():
                        return oc.get("point", 0.0), oc["price"]
    return None


def update_market_odds(events: list[dict]) -> dict:
    """Process API response and update market_odds.json. Returns summary."""
    # Load existing data
    existing = {}
    if MARKET_ODDS_PATH.exists():
        existing = json.loads(MARKET_ODDS_PATH.read_text())

    updated = 0
    skipped = 0
    errors  = []

    for ev in events:
        home_name = ev.get("home_team", "")
        away_name = ev.get("away_team", "")
        h_code = NAME_TO_CODE.get(home_name)
        a_code = NAME_TO_CODE.get(away_name)

        if not h_code or not a_code:
            errors.append(f"Unknown team: {home_name!r} or {away_name!r}")
            continue

        pair_key = frozenset([h_code, a_code])
        canonical = CANONICAL_PAIRS.get(pair_key)
        if not canonical:
            skipped += 1
            continue

        t1, t2 = canonical
        match_key = f"{t1}_{t2}"

        bks = ev.get("bookmakers", [])
        h2h = _best_h2h(bks)
        if h2h is None:
            errors.append(f"No H2H odds for {match_key}")
            continue

        home_odds, draw_odds, away_odds = h2h
        # Swap if canonical order differs from API home/away
        if t1 != h_code:
            home_odds, away_odds = away_odds, home_odds

        ah_info = _best_ah(bks, home_name)
        ah_line = ah_info[0] if ah_info else None

        prev = existing.get(match_key, {})

        # Preserve opening odds if we have them and new data is closing
        open_home = prev.get("open_home") or round(home_odds * 1.07, 2)
        open_draw = prev.get("open_draw") or round(draw_odds * 0.96, 2)
        open_away = prev.get("open_away") or round(away_odds * 1.07, 2)
        ah_open   = prev.get("ah_open", ah_line if ah_line is not None else 999.0)

        # Compute drift to infer sharp movement
        if open_home and open_home > 1.01:
            def fair(oh, od, oa):
                r = 1/oh + 1/od + 1/oa
                return (1/oh)/r, (1/oa)/r
            fh_o, fa_o = fair(open_home, open_draw, open_away)
            fh_c, fa_c = fair(home_odds, draw_odds, away_odds)
            dh = fh_c - fh_o   # positive = home shortened (backed)
            da = fa_c - fa_o
            # Map drift to sharp_index: each 2% implied prob drift → 0.1 index unit
            raw_si = 0.5 + (dh - da) * 2.5
            sharp_idx = round(max(0.15, min(0.85, raw_si)), 2)
        else:
            sharp_idx = prev.get("sharp_index", 0.5)

        # Steam: any side moved >5% implied prob
        steam = False
        if open_home and open_home > 1.01:
            steam = abs(dh) > 0.05 or abs(da) > 0.05

        ah_close = ah_line if ah_line is not None else (prev.get("ah_close") or 0.0)

        existing[match_key] = {
            "open_home":   open_home,
            "open_draw":   open_draw,
            "open_away":   open_away,
            "close_home":  round(home_odds, 2),
            "close_draw":  round(draw_odds, 2),
            "close_away":  round(away_odds, 2),
            "ah_open":     ah_open,
            "ah_close":    ah_close,
            "sharp_index": sharp_idx,
            "steam":       steam,
            "source":      "the-odds-api",
            "fetched_at":  datetime.now(timezone.utc).isoformat(),
        }
        updated += 1

    MARKET_ODDS_PATH.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
    return {"updated": updated, "skipped": skipped, "errors": errors, "total": len(events)}


def write_status(ok: bool, summary: dict, error_msg: str = "") -> None:
    status = {
        "ok":         ok,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source":     "the-odds-api" if API_KEY else "manual-estimates",
        "matches_updated": summary.get("updated", 0),
        "total_events":    summary.get("total", 0),
        "errors":          summary.get("errors", []),
        "error_msg":       error_msg,
    }
    STATUS_PATH.write_text(json.dumps(status, indent=2, ensure_ascii=False))
    if STATUS_DOCS_PATH.parent.exists():
        STATUS_DOCS_PATH.write_text(json.dumps(status, indent=2, ensure_ascii=False))
    print(json.dumps(status, indent=2, ensure_ascii=False))


def main():
    if not API_KEY:
        print("⚠ THE_ODDS_API_KEY not set — skipping live odds fetch")
        print("  Get a free key at https://the-odds-api.com (500 req/month free)")
        write_status(False, {}, "No API key — using manual estimates")
        sys.exit(0)   # not a failure; just skip

    print(f"Fetching WC2026 odds from The Odds API…")
    try:
        events = fetch_odds()
        summary = update_market_odds(events)
        print(f"✅ Updated {summary['updated']} matches ({summary['skipped']} skipped, {len(summary['errors'])} errors)")
        if summary["errors"]:
            for e in summary["errors"]:
                print(f"  ⚠ {e}")
        write_status(True, summary)
    except urllib.error.HTTPError as e:
        msg = f"HTTP {e.code}: {e.reason}"
        print(f"❌ {msg}")
        write_status(False, {}, msg)
        sys.exit(1)
    except Exception as e:
        print(f"❌ {e}")
        write_status(False, {}, str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
