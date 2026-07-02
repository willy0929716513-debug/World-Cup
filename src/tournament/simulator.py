"""
2026 FIFA World Cup Tournament Simulator.

48 teams, 12 groups (A-L), 4 teams per group.
Top 2 from each group + best 8 third-placed teams = 32 for knockout.
Knockout: R32 -> R16 -> QF -> SF -> Final.
"""
from __future__ import annotations

import math
from collections import defaultdict
from itertools import combinations
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GROUP_LIST = list('ABCDEFGHIJKL')

GROUPS: dict[str, list[str]] = {
    'A': ['MEX', 'RSA', 'KOR', 'CZE'],
    'B': ['CAN', 'SUI', 'QAT', 'BIH'],
    'C': ['BRA', 'MAR', 'SCO', 'HAI'],
    'D': ['USA', 'PAR', 'AUS', 'TUR'],
    'E': ['GER', 'CUW', 'CIV', 'ECU'],
    'F': ['NED', 'JPN', 'SWE', 'TUN'],
    'G': ['BEL', 'EGY', 'IRN', 'NZL'],
    'H': ['ESP', 'CPV', 'KSA', 'URU'],
    'I': ['FRA', 'SEN', 'IRQ', 'NOR'],
    'J': ['ARG', 'ALG', 'AUT', 'JOR'],
    'K': ['POR', 'COD', 'UZB', 'COL'],
    'L': ['ENG', 'CRO', 'GHA', 'PAN'],
}

ALL_ELOS: dict[str, int] = {
    'ARG': 2411, 'BRA': 2233, 'FRA': 2421, 'ENG': 2134, 'ESP': 2034, 'GER': 1857,
    'POR': 1961, 'NED': 2126, 'URU': 1708, 'USA': 1928, 'MAR': 2186, 'BEL': 1904,
    'CRO': 1989, 'SUI': 2039, 'AUT': 1843, 'TUR': 1730, 'SCO': 1668, 'COL': 2092,
    'ECU': 1774, 'PAR': 1811, 'JPN': 1947, 'KOR': 1583, 'KSA': 1705, 'AUS': 1813,
    'IRN': 1813, 'QAT': 1567, 'IRQ': 1320, 'UZB': 1347, 'SEN': 1685, 'EGY': 1907,
    'CIV': 1829, 'ALG': 1847, 'RSA': 1653, 'TUN': 1326, 'MEX': 2299, 'CAN': 1864,
    'PAN': 1296, 'NZL': 1589,
    # New WC2026 teams
    'SWE': 1866, 'NOR': 2099, 'CZE': 1471, 'GHA': 1868, 'COD': 1814,
    'BIH': 1772, 'CPV': 1800, 'JOR': 1299, 'CUW': 1545, 'HAI': 1239,
}

TEAM_NAMES: dict[str, str] = {
    'ARG': '阿根廷',       'BRA': '巴西',          'FRA': '法國',
    'ENG': '英格蘭',       'ESP': '西班牙',         'GER': '德國',
    'POR': '葡萄牙',       'NED': '荷蘭',           'URU': '烏拉圭',
    'USA': '美國',         'MAR': '摩洛哥',         'BEL': '比利時',
    'CRO': '克羅埃西亞',   'SUI': '瑞士',           'AUT': '奧地利',
    'TUR': '土耳其',       'SCO': '蘇格蘭',         'COL': '哥倫比亞',
    'ECU': '厄瓜多',       'PAR': '巴拉圭',         'JPN': '日本',
    'KOR': '南韓',         'KSA': '沙烏地阿拉伯',   'AUS': '澳洲',
    'IRN': '伊朗',         'QAT': '卡達',           'IRQ': '伊拉克',
    'UZB': '烏茲別克',     'SEN': '塞內加爾',       'EGY': '埃及',
    'CIV': '象牙海岸',     'ALG': '阿爾及利亞',     'RSA': '南非',
    'TUN': '突尼西亞',     'MEX': '墨西哥',         'CAN': '加拿大',
    'PAN': '巴拿馬',       'NZL': '紐西蘭',
    # New WC2026 teams
    'SWE': '瑞典',         'NOR': '挪威',           'CZE': '捷克',
    'GHA': '迦納',         'COD': '剛果民主共和國', 'BIH': '波士尼亞',
    'CPV': '維德角',       'JOR': '約旦',           'CUW': '庫拉索',
    'HAI': '海地',
}

CONFEDERATIONS: dict[str, str] = {
    'ARG': 'CONMEBOL', 'BRA': 'CONMEBOL', 'URU': 'CONMEBOL', 'COL': 'CONMEBOL',
    'ECU': 'CONMEBOL', 'PAR': 'CONMEBOL', 'ESP': 'UEFA',     'FRA': 'UEFA',
    'GER': 'UEFA',     'ENG': 'UEFA',     'POR': 'UEFA',     'NED': 'UEFA',
    'BEL': 'UEFA',     'CRO': 'UEFA',     'SUI': 'UEFA',     'AUT': 'UEFA',
    'TUR': 'UEFA',     'SCO': 'UEFA',     'MAR': 'CAF',      'SEN': 'CAF',
    'EGY': 'CAF',      'CIV': 'CAF',      'ALG': 'CAF',      'RSA': 'CAF',
    'TUN': 'CAF',      'JPN': 'AFC',      'KOR': 'AFC',      'KSA': 'AFC',
    'AUS': 'AFC',      'IRN': 'AFC',      'QAT': 'AFC',      'IRQ': 'AFC',
    'UZB': 'AFC',      'USA': 'CONCACAF', 'MEX': 'CONCACAF', 'CAN': 'CONCACAF',
    'PAN': 'CONCACAF', 'NZL': 'OFC',
    # New WC2026 teams
    'SWE': 'UEFA',     'NOR': 'UEFA',     'CZE': 'UEFA',     'BIH': 'UEFA',
    'CPV': 'CAF',      'GHA': 'CAF',      'COD': 'CAF',
    'JOR': 'AFC',      'CUW': 'CONCACAF', 'HAI': 'CONCACAF',
}

# ---------------------------------------------------------------------------
# Core simulation helpers
# ---------------------------------------------------------------------------

def elo_to_lambdas(elo_home: float, elo_away: float) -> tuple[float, float]:
    """Convert ELO ratings to Poisson goal-rate lambdas."""
    diff = elo_home - elo_away
    lam_h = 1.30 * math.exp(diff / 1100)
    lam_a = 1.10 * math.exp(-diff / 1100)
    lam_h = max(0.35, min(4.0, lam_h))
    lam_a = max(0.35, min(4.0, lam_a))
    return lam_h, lam_a


def simulate_match_single(
    elo_a: float,
    elo_b: float,
    rng: np.random.Generator,
    allow_draw: bool = True,
) -> tuple[int, int]:
    """
    Simulate a single match between two teams.

    Returns (goals_a, goals_b). When allow_draw=False (knockout), draws
    lead to extra-time and then a coin-flip PK shootout if still tied.
    """
    lam_h, lam_a = elo_to_lambdas(elo_a, elo_b)
    g_h = int(rng.poisson(lam_h))
    g_a = int(rng.poisson(lam_a))

    if allow_draw or g_h != g_a:
        return g_h, g_a

    # Extra time: 40% of base lambda
    et_lam_h = lam_h * 0.35
    et_lam_a = lam_a * 0.35
    et_h = int(rng.poisson(et_lam_h))
    et_a = int(rng.poisson(et_lam_a))
    g_h += et_h
    g_a += et_a

    if g_h != g_a:
        return g_h, g_a

    # Penalty shootout: coin-flip with ELO bias
    diff = elo_a - elo_b
    p_win = 0.5 + diff / 3000.0
    p_win = max(0.3, min(0.7, p_win))
    if rng.random() < p_win:
        return g_h + 1, g_a   # team_a wins PKs (marker only)
    else:
        return g_h, g_a + 1   # team_b wins PKs


# ---------------------------------------------------------------------------
# Group-stage simulation
# ---------------------------------------------------------------------------

def _empty_team_record(team: str) -> dict[str, Any]:
    return {'team': team, 'pts': 0, 'gf': 0, 'ga': 0, 'gd': 0, 'w': 0, 'd': 0, 'l': 0}


def _update_record(record: dict, gf: int, ga: int) -> None:
    record['gf'] += gf
    record['ga'] += ga
    record['gd'] += gf - ga
    if gf > ga:
        record['pts'] += 3
        record['w'] += 1
    elif gf == ga:
        record['pts'] += 1
        record['d'] += 1
    else:
        record['l'] += 1


def _h2h_pts(team: str, opponent: str, results: list[dict]) -> int:
    """Return H2H points for `team` vs `opponent` from match results list."""
    pts = 0
    for r in results:
        if r['t1'] == team and r['t2'] == opponent:
            if r['g1'] > r['g2']:
                pts += 3
            elif r['g1'] == r['g2']:
                pts += 1
        elif r['t1'] == opponent and r['t2'] == team:
            if r['g2'] > r['g1']:
                pts += 3
            elif r['g1'] == r['g2']:
                pts += 1
    return pts


def _h2h_gd(team: str, opponent: str, results: list[dict]) -> int:
    """Return H2H goal-difference for `team` vs `opponent`."""
    gd = 0
    for r in results:
        if r['t1'] == team and r['t2'] == opponent:
            gd += r['g1'] - r['g2']
        elif r['t1'] == opponent and r['t2'] == team:
            gd += r['g2'] - r['g1']
    return gd


def _sort_group(records: list[dict], match_results: list[dict], rng: np.random.Generator) -> list[dict]:
    """Sort group standings with full tiebreaker chain."""
    def sort_key(rec: dict) -> tuple:
        team = rec['team']
        # Primary: pts, GD, GF — these handle most cases
        return (-rec['pts'], -rec['gd'], -rec['gf'])

    # First pass: sort by pts/GD/GF
    records_sorted = sorted(records, key=sort_key)

    # Apply H2H tiebreakers within tied groups
    # Group teams by (pts, gd, gf) clusters
    result: list[dict] = []
    i = 0
    while i < len(records_sorted):
        j = i + 1
        while j < len(records_sorted) and (
            records_sorted[j]['pts'] == records_sorted[i]['pts'] and
            records_sorted[j]['gd'] == records_sorted[i]['gd'] and
            records_sorted[j]['gf'] == records_sorted[i]['gf']
        ):
            j += 1
        cluster = records_sorted[i:j]
        if len(cluster) > 1:
            # Apply H2H sorting within cluster
            teams_in_cluster = [r['team'] for r in cluster]
            cluster = _sort_cluster_h2h(cluster, teams_in_cluster, match_results, rng)
        result.extend(cluster)
        i = j

    return result


def _sort_cluster_h2h(
    cluster: list[dict],
    teams: list[str],
    match_results: list[dict],
    rng: np.random.Generator,
) -> list[dict]:
    """Sort a tied cluster by H2H points then H2H GD then random."""
    def h2h_sort_key(rec: dict) -> tuple:
        team = rec['team']
        h2h_pts_total = sum(_h2h_pts(team, opp, match_results) for opp in teams if opp != team)
        h2h_gd_total = sum(_h2h_gd(team, opp, match_results) for opp in teams if opp != team)
        random_tiebreak = rng.random()
        return (-h2h_pts_total, -h2h_gd_total, -random_tiebreak)

    return sorted(cluster, key=h2h_sort_key)


def simulate_group_stage(rng: np.random.Generator) -> dict[str, Any]:
    """
    Simulate all 72 group matches.

    Returns dict keyed by group letter with 'standings' and 'results'.
    """
    group_results: dict[str, Any] = {}

    for grp, teams in GROUPS.items():
        records = {t: _empty_team_record(t) for t in teams}
        match_list: list[dict] = []

        # Round-robin: 6 matches per group
        for t1, t2 in combinations(teams, 2):
            e1 = ALL_ELOS[t1]
            e2 = ALL_ELOS[t2]
            g1, g2 = simulate_match_single(e1, e2, rng, allow_draw=True)
            match_list.append({'t1': t1, 'g1': g1, 't2': t2, 'g2': g2})
            _update_record(records[t1], g1, g2)
            _update_record(records[t2], g2, g1)

        standings = _sort_group(list(records.values()), match_list, rng)
        group_results[grp] = {'standings': standings, 'results': match_list}

    return group_results


# ---------------------------------------------------------------------------
# Best-thirds selection
# ---------------------------------------------------------------------------

def get_best_thirds(group_results: dict[str, Any], rng: np.random.Generator | None = None) -> list[str]:
    """
    Return the 8 best third-placed teams from 12 groups.

    Ranking: pts -> GD -> GF -> random.
    """
    thirds = []
    for grp in GROUP_LIST:
        standing = group_results[grp]['standings']
        if len(standing) >= 3:
            thirds.append(standing[2])  # 3rd-place record

    def third_sort_key(rec: dict) -> tuple:
        rand_val = rng.random() if rng is not None else 0.0
        return (-rec['pts'], -rec['gd'], -rec['gf'], -rand_val)

    thirds_sorted = sorted(thirds, key=third_sort_key)
    return [r['team'] for r in thirds_sorted[:8]]


# ---------------------------------------------------------------------------
# Knockout stage
# ---------------------------------------------------------------------------

def _ko_round(teams: list[str], rng: np.random.Generator) -> list[str]:
    """
    Play one knockout round. teams must have even length; paired sequentially.
    Returns list of winners.
    """
    winners = []
    for i in range(0, len(teams), 2):
        t1 = teams[i]
        t2 = teams[i + 1]
        g1, g2 = simulate_match_single(ALL_ELOS[t1], ALL_ELOS[t2], rng, allow_draw=False)
        if g1 > g2:
            winners.append(t1)
        else:
            winners.append(t2)
    return winners


def _seed_and_pair(qualifiers: list[str]) -> list[str]:
    """
    Seed 32 qualifiers by ELO descending, pair 1v32, 2v31, ..., 16v17.
    Returns list of 32 teams in match order: [s1, s32, s2, s31, ...].
    """
    seeded = sorted(qualifiers, key=lambda t: ALL_ELOS[t], reverse=True)
    paired: list[str] = []
    n = len(seeded)
    for i in range(n // 2):
        paired.append(seeded[i])
        paired.append(seeded[n - 1 - i])
    return paired


# ---------------------------------------------------------------------------
# Full tournament simulation
# ---------------------------------------------------------------------------

def simulate_tournament(n: int = 10000, seed: int = 42) -> dict[str, Any]:
    """
    Run full World Cup tournament n times.

    Returns probability distributions for group positions, advancement,
    and knockout-round participation, plus the expected bracket.
    """
    rng = np.random.default_rng(seed)

    # Accumulators
    # group_pos_counts[grp][team][pos_1_indexed] = count
    group_pos_counts: dict[str, dict[str, dict[int, int]]] = {
        grp: {t: defaultdict(int) for t in teams}
        for grp, teams in GROUPS.items()
    }
    best_third_counts: dict[str, int] = defaultdict(int)

    # tournament_counts[team][round] = count
    # rounds: 'qual'=qualified to R32, 'r16','qf','sf','final','champ'
    tournament_counts: dict[str, dict[str, int]] = {
        t: defaultdict(int) for t in ALL_ELOS
    }

    for _ in range(n):
        # --- Group stage ---
        group_results = simulate_group_stage(rng)

        qualifiers: list[str] = []  # 32 teams for R32
        for grp in GROUP_LIST:
            standings = group_results[grp]['standings']
            # Positions 1 and 2 qualify automatically
            for pos_idx in range(4):
                team = standings[pos_idx]['team']
                group_pos_counts[grp][team][pos_idx + 1] += 1
            qualifiers.append(standings[0]['team'])
            qualifiers.append(standings[1]['team'])

        # Best 8 thirds
        best_thirds = get_best_thirds(group_results, rng)
        qualifiers.extend(best_thirds)
        for t in best_thirds:
            best_third_counts[t] += 1

        # Mark all 32 as qualified
        for t in qualifiers:
            tournament_counts[t]['qual'] += 1

        # --- Knockout stage ---
        # ELO-seeded pairing for R32
        r32_order = _seed_and_pair(qualifiers)

        r16_teams = _ko_round(r32_order, rng)
        for t in r16_teams:
            tournament_counts[t]['r16'] += 1

        qf_teams = _ko_round(r16_teams, rng)
        for t in qf_teams:
            tournament_counts[t]['qf'] += 1

        sf_teams = _ko_round(qf_teams, rng)
        for t in sf_teams:
            tournament_counts[t]['sf'] += 1

        final_teams = _ko_round(sf_teams, rng)
        for t in final_teams:
            tournament_counts[t]['final'] += 1

        champion = _ko_round(final_teams, rng)
        for t in champion:
            tournament_counts[t]['champ'] += 1

    # ---------------------------------------------------------------------------
    # Build output probabilities
    # ---------------------------------------------------------------------------

    # Group probs
    group_probs: dict[str, dict[str, dict[str, float]]] = {}
    for grp in GROUP_LIST:
        group_probs[grp] = {}
        for team in GROUPS[grp]:
            pos_counts = group_pos_counts[grp][team]
            p1 = pos_counts[1] / n * 100
            p2 = pos_counts[2] / n * 100
            p3 = pos_counts[3] / n * 100
            p4 = pos_counts[4] / n * 100
            qualified = p1 + p2
            bt = best_third_counts.get(team, 0) / n * 100
            group_probs[grp][team] = {
                'pos1': round(p1, 1),
                'pos2': round(p2, 1),
                'pos3': round(p3, 1),
                'pos4': round(p4, 1),
                'qualified': round(qualified, 1),
                'best_third': round(bt, 1),
            }

    # Tournament probs
    tournament_probs: dict[str, dict[str, float]] = {}
    for team in ALL_ELOS:
        tc = tournament_counts[team]
        tournament_probs[team] = {
            'qual':  round(tc['qual'] / n * 100, 1),
            'r16':   round(tc['r16'] / n * 100, 1),
            'qf':    round(tc['qf'] / n * 100, 1),
            'sf':    round(tc['sf'] / n * 100, 1),
            'final': round(tc['final'] / n * 100, 1),
            'champ': round(tc['champ'] / n * 100, 1),
        }

    # ---------------------------------------------------------------------------
    # Build expected bracket (deterministic, ELO-based)
    # ---------------------------------------------------------------------------

    expected_bracket = _build_expected_bracket()

    # Predicted group standings (deterministic, ELO-sorted)
    predicted_group_standings: dict[str, list[str]] = {}
    for grp, teams in GROUPS.items():
        predicted_group_standings[grp] = sorted(teams, key=lambda t: ALL_ELOS[t], reverse=True)

    return {
        'group_probs': group_probs,
        'tournament_probs': tournament_probs,
        'expected_bracket': expected_bracket,
        'predicted_group_standings': predicted_group_standings,
    }


# ---------------------------------------------------------------------------
# Expected bracket construction
# ---------------------------------------------------------------------------

def _win_prob_from_elo(elo1: float, elo2: float) -> float:
    """
    Derive P(team1 wins) from ELO-based Poisson score matrix.

    Uses a simplified closed-form approximation via the Skellam distribution
    characteristic: P(X > Y) where X ~ Poisson(lam_h), Y ~ Poisson(lam_a).
    We approximate by computing the score-matrix up to a reasonable max.
    """
    lam_h, lam_a = elo_to_lambdas(elo1, elo2)
    max_goals = 10
    p_win = 0.0
    p_draw = 0.0
    # Pre-compute Poisson PMFs
    pmf_h = [math.exp(-lam_h) * lam_h**k / math.factorial(k) for k in range(max_goals + 1)]
    pmf_a = [math.exp(-lam_a) * lam_a**k / math.factorial(k) for k in range(max_goals + 1)]
    for g_h in range(max_goals + 1):
        for g_a in range(max_goals + 1):
            p = pmf_h[g_h] * pmf_a[g_a]
            if g_h > g_a:
                p_win += p
            elif g_h == g_a:
                p_draw += p
    # In knockout, draw -> ET -> PKs. Rough approx: half the draw prob goes to each team.
    return p_win + p_draw * 0.5


def _expected_score_str(elo1: float, elo2: float) -> str:
    """Return expected score string like '2-1'."""
    lam_h, lam_a = elo_to_lambdas(elo1, elo2)
    return f"{round(lam_h)}-{round(lam_a)}"


def _build_expected_bracket() -> dict[str, Any]:
    """
    Build a deterministic expected bracket using ELO.

    - Predict group winners by ELO rank.
    - Collect 32 qualifiers (top 2 from each group + best 8 thirds by ELO).
    - Seed 1–32 by ELO desc, pair 1v32 ... 16v17.
    - Advance the higher-ELO team each round.
    """
    # Predicted group finishers by ELO
    pred_standings: dict[str, list[str]] = {}
    for grp, teams in GROUPS.items():
        pred_standings[grp] = sorted(teams, key=lambda t: ALL_ELOS[t], reverse=True)

    # Qualifiers: top-2 from each group
    qualifiers: list[str] = []
    for grp in GROUP_LIST:
        qualifiers.append(pred_standings[grp][0])
        qualifiers.append(pred_standings[grp][1])

    # Best 8 thirds by ELO from predicted 3rd-place teams
    thirds = [pred_standings[grp][2] for grp in GROUP_LIST]
    thirds_sorted = sorted(thirds, key=lambda t: ALL_ELOS[t], reverse=True)
    qualifiers.extend(thirds_sorted[:8])

    # Seed and pair
    seeded = sorted(qualifiers, key=lambda t: ALL_ELOS[t], reverse=True)
    n = len(seeded)  # 32

    def build_round_matches(teams_ordered: list[str], round_name: str, slot_offset: int = 0) -> list[dict]:
        matches = []
        for i in range(0, len(teams_ordered), 2):
            t1 = teams_ordered[i]
            t2 = teams_ordered[i + 1]
            e1 = ALL_ELOS[t1]
            e2 = ALL_ELOS[t2]
            p1 = _win_prob_from_elo(e1, e2)
            score = _expected_score_str(e1, e2)
            slot = i // 2 + 1 + slot_offset
            matches.append({
                'slot': f"M{slot}",
                'team1': t1,
                'team2': t2,
                'p1': round(p1 * 100, 1),
                'score': score,
            })
        return matches

    # R32 matches
    r32_order: list[str] = []
    for i in range(n // 2):
        r32_order.append(seeded[i])
        r32_order.append(seeded[n - 1 - i])

    r32_matches = build_round_matches(r32_order, 'r32')

    # Advance expected winners (higher ELO)
    def advance(teams_ordered: list[str]) -> list[str]:
        winners = []
        for i in range(0, len(teams_ordered), 2):
            t1 = teams_ordered[i]
            t2 = teams_ordered[i + 1]
            winner = t1 if ALL_ELOS[t1] >= ALL_ELOS[t2] else t2
            winners.append(winner)
        return winners

    r16_order = advance(r32_order)
    r16_matches = build_round_matches(r16_order, 'r16')

    qf_order = advance(r16_order)
    qf_matches = build_round_matches(qf_order, 'qf')

    sf_order = advance(qf_order)
    sf_matches = build_round_matches(sf_order, 'sf')

    final_order = advance(sf_order)
    t1, t2 = final_order[0], final_order[1]
    e1, e2 = ALL_ELOS[t1], ALL_ELOS[t2]
    p1 = _win_prob_from_elo(e1, e2)
    final_match = {
        'slot': 'M1',
        'team1': t1,
        'team2': t2,
        'p1': round(p1 * 100, 1),
        'score': _expected_score_str(e1, e2),
    }

    return {
        'r32': r32_matches,
        'r16': r16_matches,
        'qf': qf_matches,
        'sf': sf_matches,
        'final': final_match,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import json
    import time

    print("Running 2026 FIFA World Cup simulation (n=10000)...")
    t0 = time.time()
    results = simulate_tournament(n=10000, seed=42)
    elapsed = time.time() - t0
    print(f"Completed in {elapsed:.2f}s\n")

    print("=== PREDICTED GROUP STANDINGS ===")
    for grp in GROUP_LIST:
        teams = results['predicted_group_standings'][grp]
        print(f"  Group {grp}: {' | '.join(teams)}")

    print("\n=== TOP CHAMPIONSHIP PROBABILITIES ===")
    champ_probs = sorted(
        results['tournament_probs'].items(),
        key=lambda x: x[1]['champ'],
        reverse=True
    )
    for team, probs in champ_probs[:10]:
        name = TEAM_NAMES.get(team, team)
        print(f"  {name:20s} qual={probs['qual']:5.1f}%  r16={probs['r16']:5.1f}%  "
              f"qf={probs['qf']:5.1f}%  sf={probs['sf']:5.1f}%  "
              f"final={probs['final']:5.1f}%  champ={probs['champ']:5.1f}%")

    print("\n=== EXPECTED FINAL ===")
    final = results['expected_bracket']['final']
    t1 = TEAM_NAMES.get(final['team1'], final['team1'])
    t2 = TEAM_NAMES.get(final['team2'], final['team2'])
    print(f"  {t1} vs {t2}  ({final['score']})  P({t1} wins)={final['p1']:.1f}%")
