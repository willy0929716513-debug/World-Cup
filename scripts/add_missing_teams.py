#!/usr/bin/env python3
"""
Generate realistic team data for all 48 WC2026 teams that are missing from data/teams.json.
Stats are calibrated to each team's ELO rating and FIFA ranking.
"""
from __future__ import annotations
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "teams.json"

random.seed(42)

# ── ELO ratings from simulator.py ─────────────────────────────────────────────
ALL_ELOS = {
    'ARG':2063,'BRA':2008,'FRA':2038,'ENG':1992,'ESP':2015,'GER':1981,
    'POR':1978,'NED':1965,'URU':1928,'USA':1905,'MAR':1892,'BEL':1938,
    'ITA':1942,'CRO':1925,'SUI':1895,'AUT':1905,'DEN':1910,'SRB':1860,
    'TUR':1870,'POL':1845,'SCO':1855,'COL':1932,'ECU':1855,'PAR':1820,
    'JPN':1870,'KOR':1840,'KSA':1800,'AUS':1820,'IRN':1820,'QAT':1765,
    'IRQ':1780,'UZB':1795,'SEN':1855,'NGA':1830,'EGY':1815,'CIV':1820,
    'ALG':1825,'CMR':1805,'RSA':1785,'TUN':1795,'MEX':1878,'CAN':1902,
    'PAN':1772,'HON':1755,'JAM':1758,'NZL':1748,'VEN':1750,'IDN':1710,
}

def s(elo):
    """Normalized strength 0.0 (IDN=1710) → 1.0 (ARG=2063)."""
    return max(0.0, min(1.0, (elo - 1700) / 363))

def jitter(val, pct=0.04):
    return round(val * (1 + random.uniform(-pct, pct)), 3)

def ri(lo, hi):
    return random.randint(lo, hi)

def rf(lo, hi, dec=2):
    return round(random.uniform(lo, hi), dec)

def gen_recent(elo, n=10):
    """Generate n synthetic recent match results based on ELO."""
    st = s(elo)
    matches = []
    comps = ['WCQ', 'WCQ', 'WCQ', 'Friendly', 'Friendly', 'NL']
    venues = ['H', 'A', 'N']
    opponents = ['Opponent A', 'Opponent B', 'Opponent C', 'Opponent D', 'Opponent E',
                 'Opponent F', 'Opponent G', 'Opponent H', 'Opponent I', 'Opponent J']
    for i in range(n):
        r = random.random()
        wp = 0.35 + st * 0.35  # win probability
        dp = 0.25 - st * 0.05  # draw probability
        if r < wp:
            gf, ga = ri(1, 3), ri(0, 1)
        elif r < wp + dp:
            g = ri(0, 2)
            gf, ga = g, g
        else:
            gf, ga = ri(0, 1), ri(1, 3)
        matches.append({
            "opponent": opponents[i % len(opponents)],
            "goals_for": gf, "goals_against": ga,
            "venue": venues[i % 3],
            "competition": comps[i % len(comps)],
        })
    return matches

def gen_market(elo):
    """Generate generic market data."""
    st = s(elo)
    # generic odds for a match vs average-ranked opponent
    ph = 0.35 + st * 0.30
    pd = 0.28 - st * 0.06
    pa = 1 - ph - pd
    def prob_to_odds(p, margin=1.07):
        return round(margin / max(p, 0.05), 2)
    return {
        "odds_home": prob_to_odds(ph),
        "odds_draw": prob_to_odds(pd),
        "odds_away": prob_to_odds(pa),
        "asian_handicap_line": round(-0.5 * st, 1),
        "asian_handicap_home_odds": 1.95,
        "asian_handicap_away_odds": 1.95,
        "ou_line": 2.5,
        "over_odds": round(1.7 + st * 0.2, 2),
        "under_odds": round(2.1 - st * 0.2, 2),
    }

def gen_team(code, name, short_name, confederation, fifa_ranking, elo,
             spi, squad_value_m, avg_age, wc_titles, wc_best_result, wc_appearances,
             coach, coach_rating, primary_formation, secondary_formation,
             possession_style, high_press, defensive_line,
             key_players):
    st = s(elo)
    atk = {
        "goals_per_game": jitter(0.72 + st * 1.55),
        "xg_per_game": jitter(0.68 + st * 1.48),
        "npxg_per_game": jitter(0.60 + st * 1.32),
        "shots_per_game": jitter(7.5 + st * 8.5),
        "shots_on_target_per_game": jitter(2.6 + st * 3.2),
        "shots_in_box_per_game": jitter(4.5 + st * 5.5),
        "big_chances_per_game": jitter(0.8 + st * 2.2),
        "conversion_rate": jitter(0.085 + st * 0.075),
        "counter_goals_pct": rf(15, 35),
        "set_piece_goals_pct": rf(18, 38),
        "corners_per_game": jitter(3.8 + st * 3.2),
        "cross_accuracy_pct": jitter(24 + st * 12),
        "key_passes_per_game": jitter(2.2 + st * 2.6),
        "possession_pct": jitter(44 + st * 18),
        "pass_accuracy_pct": jitter(75 + st * 15),
    }
    dfn = {
        "goals_against_per_game": jitter(1.90 - st * 1.15),
        "xga_per_game": jitter(1.85 - st * 1.05),
        "clean_sheet_pct": jitter(12 + st * 42),
        "shots_against_per_game": jitter(15.5 - st * 7.0),
        "sot_against_per_game": jitter(6.0 - st * 3.0),
        "tackle_success_pct": jitter(60 + st * 16),
        "interceptions_per_game": jitter(5.5 + st * 3.5),
        "clearances_per_game": jitter(14 + st * 4),
        "set_piece_conceded_pct": rf(20, 38),
        "aerial_success_pct": jitter(50 + st * 15),
        "gk_save_pct": jitter(66 + st * 12),
        "gk_psxg_ga": jitter(-0.05 + st * 0.28),
    }
    adv = {
        "ppda": jitter(14 - st * 6.5),
        "field_tilt": jitter(38 + st * 22),
        "deep_completion_per_game": jitter(2.5 + st * 4.0),
        "progressive_passes": jitter(35 + st * 35),
        "progressive_carries": jitter(14 + st * 18),
        "shot_creating_actions": jitter(9 + st * 12),
        "goal_creating_actions": jitter(1.2 + st * 2.2),
        "xpts_per_game": jitter(0.9 + st * 1.5),
    }
    tactics = {
        "primary_formation": primary_formation,
        "secondary_formation": secondary_formation,
        "possession_style": possession_style,
        "high_press": high_press,
        "press_intensity": round(4.5 + st * 5.5, 1),
        "defensive_line": defensive_line,
        "wide_play_pct": rf(28, 58),
        "set_piece_quality": round(5.0 + st * 4.5, 1),
        "tactical_flexibility": round(5.0 + st * 4.5, 1),
    }
    return {
        "name": name, "short_name": short_name, "code": code,
        "confederation": confederation, "fifa_ranking": fifa_ranking,
        "elo_rating": elo, "spi_rating": spi,
        "squad_value_m": squad_value_m, "avg_age": avg_age,
        "squad_depth": round(4.0 + st * 5.5, 1),
        "bench_quality": round(3.5 + st * 5.8, 1),
        "wc_titles": wc_titles, "wc_best_result": wc_best_result,
        "wc_appearances": wc_appearances,
        "coach": coach, "coach_rating": coach_rating,
        "attack": atk, "defense": dfn, "advanced": adv, "tactics": tactics,
        "key_players": key_players,
        "injured_players": [], "suspended_players": [],
        "recent_matches": gen_recent(elo),
        "market_data": gen_market(elo),
    }

def p(name, pos, club, age, mv, goals=0, assists=0, rating=7.5):
    return {"name": name, "position": pos, "club": club, "age": age,
            "market_value_m": mv, "goals_season": goals, "assists_season": assists,
            "form_rating": rating, "is_injured": False, "is_suspended": False, "injury_detail": ""}

# ── Team definitions (37 missing teams) ───────────────────────────────────────

NEW_TEAMS = {}

# Belgium (BEL) — UEFA, ELO 1938
NEW_TEAMS['BEL'] = gen_team(
    'BEL','Belgium','Belgium','UEFA',5,1938,84.5,750,27.2,0,'Runner-Up',14,
    'Domenico Tedesco',7.5,'4-3-3','3-4-3',True,True,'medium',
    [p('Kevin De Bruyne','MID','Manchester City',33,100,8,14,9.2),
     p('Romelu Lukaku','FWD','AS Roma',31,45,22,5,8.0),
     p('Thibaut Courtois','GK','Real Madrid',32,60,0,0,9.0),
     p('Axel Witsel','MID','Atletico Madrid',35,8,2,3,7.4)])

# Italy (ITA) — UEFA, ELO 1942
NEW_TEAMS['ITA'] = gen_team(
    'ITA','Italy','Italy','UEFA',9,1942,85.1,620,26.8,4,'Champion',18,
    'Luciano Spalletti',7.8,'4-3-3','3-5-2',True,True,'medium',
    [p('Gianluigi Donnarumma','GK','PSG',25,80,0,0,9.1),
     p('Federico Chiesa','FWD','Liverpool',26,60,14,8,8.5),
     p('Sandro Tonali','MID','Newcastle',24,70,5,7,8.3),
     p('Giacomo Raspadori','FWD','Napoli',24,45,11,4,7.8)])

# Croatia (CRO) — UEFA, ELO 1925
NEW_TEAMS['CRO'] = gen_team(
    'CRO','Croatia','Croatia','UEFA',13,1925,82.0,310,29.5,0,'Runner-Up',6,
    'Zlatko Dalic',8.0,'4-3-3','4-2-3-1',True,False,'medium',
    [p('Luka Modric','MID','Real Madrid',39,20,4,9,8.9),
     p('Ivan Gvardiol','DEF','Manchester City',22,80,3,4,8.4),
     p('Mateo Kovacic','MID','Manchester City',30,55,5,8,8.2),
     p('Andrej Kramaric','FWD','Hoffenheim',33,18,18,9,8.0)])

# Switzerland (SUI) — UEFA, ELO 1895
NEW_TEAMS['SUI'] = gen_team(
    'SUI','Switzerland','Switzerland','UEFA',19,1895,78.5,280,27.8,0,'Quarter-Final',12,
    'Murat Yakin',7.2,'3-4-3','4-2-3-1',True,True,'medium',
    [p('Granit Xhaka','MID','Bayer Leverkusen',31,35,8,12,8.5),
     p('Xherdan Shaqiri','FWD','Chicago Fire',32,12,7,5,7.5),
     p('Yann Sommer','GK','Internazionale',35,22,0,0,8.4),
     p('Manuel Akanji','DEF','Manchester City',28,60,2,3,8.2)])

# Austria (AUT) — UEFA, ELO 1905
NEW_TEAMS['AUT'] = gen_team(
    'AUT','Austria','Austria','UEFA',26,1905,79.5,260,27.0,0,'Runner-Up',7,
    'Ralf Rangnick',8.5,'4-2-3-1','3-5-2',True,True,'high',
    [p('David Alaba','DEF','Real Madrid',32,55,3,5,8.8),
     p('Marcel Sabitzer','MID','Dortmund',30,30,7,8,8.0),
     p('Marko Arnautovic','FWD','Internazionale',35,12,10,4,7.6),
     p('Florian Grillitsch','MID','Nice',29,18,3,5,7.5)])

# Denmark (DEN) — UEFA, ELO 1910
NEW_TEAMS['DEN'] = gen_team(
    'DEN','Denmark','Denmark','UEFA',17,1910,80.2,290,26.5,0,'Semi-Final',5,
    'Kasper Hjulmand',7.6,'3-4-3','4-3-3',True,True,'medium',
    [p('Christian Eriksen','MID','Manchester United',32,35,6,11,8.6),
     p('Rasmus Hojlund','FWD','Manchester United',21,80,16,5,8.5),
     p('Pierre-Emile Hojbjerg','MID','Marseille',28,30,4,6,8.0),
     p('Andreas Christensen','DEF','Barcelona',28,45,1,2,8.3)])

# Serbia (SRB) — UEFA, ELO 1860
NEW_TEAMS['SRB'] = gen_team(
    'SRB','Serbia','Serbia','UEFA',33,1860,72.0,220,27.2,0,'Group Stage',14,
    'Dragan Stojkovic',7.4,'3-4-3','4-2-3-1',False,False,'medium',
    [p('Dusan Vlahovic','FWD','Juventus',24,90,22,5,8.5),
     p('Sergej Milinkovic-Savic','MID','Al-Hilal',29,45,7,8,8.0),
     p('Aleksandar Mitrovic','FWD','Al-Hilal',30,40,30,6,8.2),
     p('Filip Kostic','MID','Juventus',31,22,4,9,7.8)])

# Turkey (TUR) — UEFA, ELO 1870
NEW_TEAMS['TUR'] = gen_team(
    'TUR','Turkey','Turkey','UEFA',29,1870,73.5,310,25.8,0,'Third Place',2,
    'Vincenzo Montella',7.2,'4-2-3-1','4-3-3',False,True,'medium',
    [p('Hakan Calhanoglu','MID','Internazionale',30,55,8,14,9.0),
     p('Arda Guler','MID','Real Madrid',19,80,6,5,8.8),
     p('Merih Demiral','DEF','Al-Qadsiah',26,28,2,1,8.0),
     p('Kerem Akturkoglu','FWD','Galatasaray',26,30,14,8,8.2)])

# Poland (POL) — UEFA, ELO 1845
NEW_TEAMS['POL'] = gen_team(
    'POL','Poland','Poland','UEFA',25,1845,70.8,220,29.0,0,'Third Place',9,
    'Michal Probierz',6.8,'4-3-1-2','4-2-3-1',False,False,'low',
    [p('Robert Lewandowski','FWD','Barcelona',36,45,25,8,9.0),
     p('Wojciech Szczesny','GK','Barcelona',34,20,0,0,8.2),
     p('Piotr Zielinski','MID','Internazionale',30,40,7,10,8.4),
     p('Kamil Glik','DEF','Benevento',36,3,1,0,7.0)])

# Scotland (SCO) — UEFA, ELO 1855
NEW_TEAMS['SCO'] = gen_team(
    'SCO','Scotland','Scotland','UEFA',34,1855,71.5,180,27.5,0,'Group Stage',10,
    'Steve Clarke',7.0,'3-5-2','4-2-3-1',False,True,'medium',
    [p('Andrew Robertson','DEF','Liverpool',30,55,2,8,8.8),
     p('Scott McTominay','MID','Napoli',27,45,8,4,8.2),
     p('Kieran Tierney','DEF','Arsenal',27,30,2,4,8.0),
     p('John McGinn','MID','Aston Villa',30,28,6,7,8.1)])

# Colombia (COL) — CONMEBOL, ELO 1932
NEW_TEAMS['COL'] = gen_team(
    'COL','Colombia','Colombia','CONMEBOL',11,1932,83.0,550,26.8,0,'Fourth Place',6,
    'Nestor Lorenzo',7.5,'4-2-3-1','4-3-3',True,True,'medium',
    [p('Luis Diaz','FWD','Liverpool',27,90,18,8,8.8),
     p('James Rodriguez','MID','Rayo Vallecano',33,18,7,14,8.2),
     p('Jhon Duran','FWD','Aston Villa',21,55,12,5,8.4),
     p('Davinson Sanchez','DEF','Galatasaray',28,22,2,2,7.8)])

# Ecuador (ECU) — CONMEBOL, ELO 1855
NEW_TEAMS['ECU'] = gen_team(
    'ECU','Ecuador','Ecuador','CONMEBOL',41,1855,71.0,280,25.2,0,'Second Round',3,
    'Sebastian Beccacece',7.0,'4-4-2','3-5-2',False,True,'medium',
    [p('Moises Caicedo','MID','Chelsea',22,100,4,7,8.8),
     p('Enner Valencia','FWD','Independiente',34,8,12,5,7.8),
     p('Jeremy Sarmiento','MID','Brighton',23,22,5,7,8.0),
     p('Piero Hincapie','DEF','Bayer Leverkusen',22,55,2,3,8.2)])

# Paraguay (PAR) — CONMEBOL, ELO 1820
NEW_TEAMS['PAR'] = gen_team(
    'PAR','Paraguay','Paraguay','CONMEBOL',60,1820,66.5,120,27.5,2,'Runner-Up',9,
    'Gustavo Alfaro',6.8,'4-4-2','5-3-2',False,False,'low',
    [p('Miguel Almiron','MID','Newcastle',30,22,6,8,8.2),
     p('Gustavo Gomez','DEF','Palmeiras',31,15,3,2,7.8),
     p('Antonio Sanabria','FWD','Torino',28,18,10,4,7.5),
     p('Junior Alonso','DEF','Atletico Mineiro',30,12,2,1,7.4)])

# Japan (JPN) — AFC, ELO 1870
NEW_TEAMS['JPN'] = gen_team(
    'JPN','Japan','Japan','AFC',16,1870,74.2,360,26.2,0,'Quarter-Final',7,
    'Hajime Moriyasu',7.5,'4-2-3-1','3-4-3',True,True,'high',
    [p('Takumi Minamino','FWD','Monaco',30,22,10,8,8.0),
     p('Ritsu Doan','FWD','Freiburg',26,30,12,7,8.3),
     p('Daichi Kamada','MID','Crystal Palace',28,22,7,8,8.2),
     p('Ko Itakura','DEF','Borussia M\'gladbach',27,18,1,2,8.0)])

# South Korea (KOR) — AFC, ELO 1840
NEW_TEAMS['KOR'] = gen_team(
    'KOR','South Korea','Korea Republic','AFC',22,1840,69.5,280,27.0,0,'Fourth Place',11,
    'Hong Myung-bo',7.2,'4-2-3-1','3-4-3',True,True,'high',
    [p('Heung-min Son','FWD','Tottenham',32,70,18,10,9.2),
     p('Lee Kang-in','MID','PSG',23,60,8,11,8.5),
     p('Kim Min-jae','DEF','Bayern Munich',27,65,2,2,9.0),
     p('Cho Gue-sung','FWD','Jeonbuk',26,8,12,4,7.6)])

# Saudi Arabia (KSA) — AFC, ELO 1800
NEW_TEAMS['KSA'] = gen_team(
    'KSA','Saudi Arabia','Saudi Arabia','AFC',56,1800,64.0,90,28.5,0,'Second Round',6,
    'Roberto Mancini',7.0,'4-3-3','4-2-3-1',True,False,'medium',
    [p('Saleh Al-Shehri','FWD','Al-Hilal',31,5,14,4,7.8),
     p('Salem Al-Dawsari','FWD','Al-Hilal',32,4,10,9,7.6),
     p('Mohammed Al-Owais','GK','Al-Hilal',31,4,0,0,7.8),
     p('Ali Al-Bulaihi','DEF','Al-Hilal',33,3,2,1,7.4)])

# Australia (AUS) — AFC, ELO 1820
NEW_TEAMS['AUS'] = gen_team(
    'AUS','Australia','Australia','AFC',23,1820,67.0,180,27.8,0,'Quarter-Final',5,
    'Tony Popovic',7.0,'4-3-3','4-4-2',False,True,'medium',
    [p('Mathew Leckie','FWD','Melbourne City',34,5,8,5,7.8),
     p('Mat Ryan','GK','Copenhagen',32,8,0,0,7.8),
     p('Cameron Devlin','MID','Hearts',26,6,3,5,7.5),
     p('Harry Souttar','DEF','Leicester',26,12,2,2,7.6)])

# Iran (IRN) — AFC, ELO 1820
NEW_TEAMS['IRN'] = gen_team(
    'IRN','Iran','IR Iran','AFC',20,1820,67.5,120,29.5,0,'Group Stage',6,
    'Amir Ghalenoei',6.8,'4-1-4-1','4-2-3-1',False,False,'low',
    [p('Mehdi Taremi','FWD','Internazionale',32,30,15,8,8.5),
     p('Sardar Azmoun','FWD','Bayer Leverkusen',29,25,12,7,8.0),
     p('Ali Beiranvand','GK','Antwerp',32,5,0,0,7.5),
     p('Saman Ghoddos','MID','Brentford',30,8,4,6,7.6)])

# Qatar (QAT) — AFC, ELO 1765
NEW_TEAMS['QAT'] = gen_team(
    'QAT','Qatar','Qatar','AFC',35,1765,61.0,45,27.0,0,'Group Stage',2,
    'Marquez Lopez',6.5,'4-3-3','4-2-3-1',True,False,'medium',
    [p('Akram Afif','FWD','Al-Sadd',28,6,12,8,8.2),
     p('Almoez Ali','FWD','Al-Duhail',28,5,10,5,7.8),
     p('Hassan Al-Haydos','MID','Al-Sadd',33,3,5,6,7.5),
     p('Bassam Al-Rawi','DEF','Al-Rayyan',29,3,1,2,7.2)])

# Iraq (IRQ) — AFC, ELO 1780
NEW_TEAMS['IRQ'] = gen_team(
    'IRQ','Iraq','Iraq','AFC',58,1780,62.5,35,27.8,0,'Second Round',4,
    'Jesus Casas',6.5,'4-2-3-1','4-4-2',False,False,'medium',
    [p('Aymen Hussein','FWD','Al-Quwa Al-Jawiya',29,4,12,5,7.8),
     p('Amjad Attwan','MID','Al-Zawra',28,3,5,8,7.5),
     p('Ali Adnan','DEF','Lecce',30,8,2,4,7.6),
     p('Mohanad Ali','FWD','Al-Shorta',25,3,8,4,7.4)])

# Uzbekistan (UZB) — AFC, ELO 1795
NEW_TEAMS['UZB'] = gen_team(
    'UZB','Uzbekistan','Uzbekistan','AFC',65,1795,63.0,40,26.2,0,'First Round',2,
    'Timur Kapadze',6.8,'4-3-3','4-4-2',False,False,'medium',
    [p('Eldor Shomurodov','FWD','Roma',27,15,8,5,7.8),
     p('Jaloliddin Masharipov','MID','Pakhtakor',30,4,5,8,7.6),
     p('Odil Ahmedov','MID','Shanghai SIPG',35,3,2,4,7.2),
     p('Otabek Shukurov','DEF','Pakhtakor',27,3,1,2,7.3)])

# Senegal (SEN) — CAF, ELO 1855
NEW_TEAMS['SEN'] = gen_team(
    'SEN','Senegal','Senegal','CAF',15,1855,72.5,380,27.5,0,'Quarter-Final',4,
    'Aliou Cisse',7.5,'4-3-3','4-2-3-1',True,True,'medium',
    [p('Sadio Mane','FWD','Al-Nassr',32,30,14,8,8.8),
     p('Kalidou Koulibaly','DEF','Al-Hilal',33,22,2,2,8.5),
     p('Edouard Mendy','GK','Chelsea',32,28,0,0,8.0),
     p('Idrissa Gueye','MID','Everton',35,8,2,5,7.8)])

# Nigeria (NGA) — CAF, ELO 1830
NEW_TEAMS['NGA'] = gen_team(
    'NGA','Nigeria','Nigeria','CAF',40,1830,68.5,320,25.8,0,'Second Round',6,
    'Augustine Eguavoen',6.8,'4-3-3','4-2-3-1',True,True,'high',
    [p('Victor Osimhen','FWD','Galatasaray',25,120,25,8,9.2),
     p('Samuel Chukwueze','FWD','AC Milan',25,45,8,9,8.0),
     p('Wilfred Ndidi','MID','Leicester',27,28,3,4,8.2),
     p('Calvin Bassey','DEF','Fulham',24,30,2,3,7.8)])

# Egypt (EGY) — CAF, ELO 1815
NEW_TEAMS['EGY'] = gen_team(
    'EGY','Egypt','Egypt','CAF',37,1815,67.0,180,28.5,0,'Runner-Up',3,
    'Hossam Hassan',6.8,'4-2-3-1','4-4-2',False,False,'medium',
    [p('Mohamed Salah','FWD','Liverpool',32,100,22,12,9.5),
     p('Mohamed El-Shenawy','GK','Al-Ahly',36,4,0,0,7.8),
     p('Omar Marmoush','FWD','Manchester City',26,60,18,10,8.6),
     p('Mostafa Mohamed','FWD','Galatasaray',26,25,12,4,7.8)])

# Ivory Coast (CIV) — CAF, ELO 1820
NEW_TEAMS['CIV'] = gen_team(
    'CIV','Ivory Coast','Ivory Coast','CAF',43,1820,67.5,280,27.8,0,'Quarter-Final',9,
    'Emerse Fae',7.0,'4-3-3','4-2-3-1',True,True,'medium',
    [p('Sebastien Haller','FWD','Dortmund',30,22,10,4,7.8),
     p('Franck Kessie','MID','Al-Ahli',27,18,5,7,7.8),
     p('Simon Adingra','FWD','Brighton',22,30,8,6,8.2),
     p('Serge Aurier','DEF','Nottm Forest',32,8,2,4,7.4)])

# Algeria (ALG) — CAF, ELO 1825
NEW_TEAMS['ALG'] = gen_team(
    'ALG','Algeria','Algeria','CAF',38,1825,68.0,180,28.2,0,'Champion',4,
    'Vladimir Petkovic',7.0,'4-3-3','4-4-2',True,False,'medium',
    [p('Riyad Mahrez','FWD','Al-Ahli',33,20,10,10,8.5),
     p('Ismael Bennacer','MID','AC Milan',26,50,4,8,8.4),
     p('Youcef Atal','DEF','Nice',28,22,4,5,8.0),
     p('Said Benrahma','MID','Lyon',29,18,7,8,7.8)])

# Cameroon (CMR) — CAF, ELO 1805
NEW_TEAMS['CMR'] = gen_team(
    'CMR','Cameroon','Cameroon','CAF',48,1805,65.0,140,28.0,0,'Quarter-Final',8,
    'Marc Brys',6.8,'4-3-3','4-2-3-1',False,False,'medium',
    [p('Andre Onana','GK','Manchester United',28,45,0,0,8.5),
     p('Vincent Aboubakar','FWD','Al-Nassr',32,10,12,4,7.8),
     p('Bryan Mbeumo','FWD','Brentford',24,50,14,8,8.5),
     p('Michael Ngadeu','DEF','Gent',33,4,2,1,7.4)])

# South Africa (RSA) — CAF, ELO 1785
NEW_TEAMS['RSA'] = gen_team(
    'RSA','South Africa','South Africa','CAF',62,1785,62.0,70,28.5,0,'First Round',3,
    'Hugo Broos',6.5,'4-1-4-1','4-4-2',False,False,'low',
    [p('Percy Tau','FWD','Al-Ahly',30,8,8,5,8.0),
     p('Ronwen Williams','GK','Mamelodi Sundowns',31,4,0,0,7.8),
     p('Themba Zwane','MID','Mamelodi Sundowns',33,3,6,9,7.8),
     p('Bongani Zungu','MID','Rangers',31,5,3,4,7.4)])

# Tunisia (TUN) — CAF, ELO 1795
NEW_TEAMS['TUN'] = gen_team(
    'TUN','Tunisia','Tunisia','CAF',30,1795,63.5,90,28.8,0,'Second Round',6,
    'Jalel Kadri',6.8,'4-3-3','4-2-3-1',False,False,'medium',
    [p('Wahbi Khazri','FWD','Montpellier',33,6,8,6,7.8),
     p('Ellyes Skhiri','MID','Eintracht Frankfurt',28,18,4,5,8.0),
     p('Youssef Msakni','FWD','Al-Qadsiah',34,4,7,6,7.6),
     p('Montassar Talbi','DEF','Lorient',25,8,2,1,7.5)])

# Mexico (MEX) — CONCACAF, ELO 1878
NEW_TEAMS['MEX'] = gen_team(
    'MEX','Mexico','Mexico','CONCACAF',13,1878,75.5,280,28.5,0,'Quarter-Final',17,
    'Javier Aguirre',7.2,'4-3-3','4-2-3-1',True,False,'medium',
    [p('Hirving Lozano','FWD','PSV',28,35,10,10,8.5),
     p('Raul Jimenez','FWD','Fulham',33,22,12,6,8.0),
     p('Edson Alvarez','MID','West Ham',26,40,3,5,8.3),
     p('Guillermo Ochoa','GK','Salernitana',38,4,0,0,7.8)])

# Canada (CAN) — CONCACAF, ELO 1902
NEW_TEAMS['CAN'] = gen_team(
    'CAN','Canada','Canada','CONCACAF',49,1902,78.5,380,26.5,0,'Group Stage',3,
    'Jesse Marsch',7.8,'4-3-3','4-4-2',True,True,'high',
    [p('Alphonso Davies','DEF','Bayern Munich',23,90,4,12,9.2),
     p('Jonathan David','FWD','Lille',24,80,25,8,9.0),
     p('Tajon Buchanan','FWD','Internazionale',25,35,8,8,8.2),
     p('Cyle Larin','FWD','Mallorca',29,15,12,5,7.8)])

# Panama (PAN) — CONCACAF, ELO 1772
NEW_TEAMS['PAN'] = gen_team(
    'PAN','Panama','Panama','CONCACAF',81,1772,62.0,35,29.5,0,'Group Stage',2,
    'Thomas Christiansen',6.5,'4-4-2','5-4-1',False,False,'low',
    [p('Rolando Blackburn','FWD','Club Atletico Independiente',27,3,6,3,7.5),
     p('Jose Fajardo','FWD','Al-Qadsiah',24,8,5,4,7.6),
     p('Ricardo Avila','MID','New York City FC',28,4,2,5,7.4),
     p('Eric Davis','DEF','New York Red Bulls',34,2,1,1,7.2)])

# Honduras (HON) — CONCACAF, ELO 1755
NEW_TEAMS['HON'] = gen_team(
    'HON','Honduras','Honduras','CONCACAF',89,1755,60.5,25,28.0,0,'Second Round',8,
    'Reinaldo Rueda',6.5,'4-4-2','4-5-1',False,False,'low',
    [p('Alberth Elis','FWD','Bournemouth',28,15,8,5,8.0),
     p('Romell Quiotto','FWD','CF Montreal',30,6,5,7,7.6),
     p('Antony Lozano','FWD','Getafe',28,8,6,4,7.5),
     p('Denil Maldonado','DEF','Marathon',26,3,1,2,7.3)])

# Jamaica (JAM) — CONCACAF, ELO 1758
NEW_TEAMS['JAM'] = gen_team(
    'JAM','Jamaica','Jamaica','CONCACAF',47,1758,61.0,80,27.5,0,'Second Round',5,
    'Heimir Hallgrimsson',6.8,'4-2-3-1','4-3-3',False,False,'medium',
    [p('Leon Bailey','FWD','Aston Villa',27,40,8,9,8.2),
     p('Michail Antonio','FWD','Nottm Forest',34,10,6,4,7.5),
     p('Bobby Reid','MID','Fulham',31,8,4,5,7.4),
     p('Damion Lowe','DEF','Hibernian',31,4,2,1,7.2)])

# New Zealand (NZL) — OFC, ELO 1748
NEW_TEAMS['NZL'] = gen_team(
    'NZL','New Zealand','New Zealand','OFC',96,1748,59.5,30,27.2,0,'Second Round',4,
    'Darren Bazeley',6.2,'4-4-2','4-5-1',False,False,'low',
    [p('Clayton Lewis','MID','Go Ahead Eagles',27,3,3,4,7.5),
     p('Chris Wood','FWD','Nottm Forest',32,12,12,4,8.0),
     p('Stefan Marinovic','GK','Millwall',33,3,0,0,7.4),
     p('Dane Ingham','DEF','Wollongong Wolves',29,1,1,1,7.2)])

# Venezuela (VEN) — CONMEBOL (marked INT in simulator), ELO 1750
NEW_TEAMS['VEN'] = gen_team(
    'VEN','Venezuela','Venezuela','CONMEBOL',50,1750,60.0,90,26.8,0,'First Round',3,
    'Fernando Batista',6.5,'4-3-3','4-4-2',False,False,'medium',
    [p('Yangel Herrera','MID','Barcelona',26,35,6,7,8.2),
     p('Josef Martinez','FWD','Inter Miami',31,8,8,4,7.8),
     p('Tomas Rincon','MID','Sampdoria',36,4,2,3,7.2),
     p('Jhon Chancellor','DEF','Elche',31,6,2,1,7.4)])

# Indonesia (IDN) — AFC (marked INT in simulator), ELO 1710
NEW_TEAMS['IDN'] = gen_team(
    'IDN','Indonesia','Indonesia','AFC',130,1710,55.0,18,26.0,0,'Never qualified',0,
    'Patrick Kluivert',6.8,'4-2-3-1','4-3-3',True,False,'medium',
    [p('Egy Maulana Vikri','FWD','Lechia Gdansk',24,3,5,4,7.5),
     p('Witan Sulaeman','MID','Persib Bandung',23,2,3,5,7.4),
     p('Marselino Ferdinan','MID','Persebaya',20,2,4,5,7.8),
     p('Pratama Arhan','DEF','Suwon FC',22,2,1,3,7.3)])


# ── Load existing teams.json and merge ─────────────────────────────────────────
with open(DATA_FILE, 'r', encoding='utf-8') as f:
    existing = json.load(f)

added = 0
for code, data in NEW_TEAMS.items():
    if code not in existing:
        existing[code] = data
        print(f"  + Added {code} ({data['name']})")
        added += 1
    else:
        print(f"  . Skipped {code} (already exists)")

with open(DATA_FILE, 'w', encoding='utf-8') as f:
    json.dump(existing, f, ensure_ascii=False, indent=2)

print(f"\n✅ Done — added {added} new teams ({len(existing)} total in teams.json)")
