#!/usr/bin/env python3
"""
Train ML model (LogisticRegression) and probability calibration.

Data sources:
  1. WC2022 + WC2018 historical results (hardcoded, with estimated pre-match ELOs)
  2. WC2026 actual results from docs/data/results.json
     - Features derived from current data/teams.json

Outputs:
  data/ml_coefficients.json   — LogisticRegression coefficients
  data/calibration.json       — per-class linear calibration parameters

Run order in CI:
  1. update_elo_from_results.py
  2. train_models.py          ← this script
  3. generate_static_data.py
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np

# ── Historical training data ───────────────────────────────────────────────────
# Format: (home_code, away_code, home_elo, away_elo, result)
# result: 1=home_win, 0=draw, -1=away_win

WC2022_DATA = [
    # Group Stage
    ("QAT", "ECU", 1630, 1750, -1),
    ("ENG", "IRN", 1950, 1720, 1),
    ("SEN", "NED", 1780, 1900, -1),
    ("USA", "WAL", 1830, 1760, 0),
    ("ARG", "KSA", 2000, 1690, -1),
    ("DEN", "TUN", 1850, 1680, 0),
    ("MEX", "POL", 1820, 1780, 0),
    ("FRA", "AUS", 1980, 1740, 1),
    ("MAR", "CRO", 1770, 1890, 0),
    ("GER", "JPN", 1960, 1790, -1),
    ("ESP", "CRC", 1960, 1720, 1),
    ("BEL", "CAN", 1950, 1800, 1),
    ("SUI", "CMR", 1820, 1680, 1),
    ("URU", "KOR", 1860, 1770, 0),
    ("POR", "GHA", 1930, 1720, 1),
    ("BRA", "SRB", 1990, 1780, 1),
    ("WAL", "IRN", 1760, 1720, 0),
    ("QAT", "SEN", 1630, 1780, -1),
    ("NED", "ECU", 1900, 1750, 0),
    ("ENG", "USA", 1950, 1830, 0),
    ("TUN", "AUS", 1680, 1740, -1),
    ("POL", "KSA", 1780, 1690, 1),
    ("FRA", "DEN", 1980, 1850, 1),
    ("ARG", "MEX", 2000, 1820, 1),
    ("JPN", "CRC", 1790, 1720, -1),
    ("BEL", "MAR", 1950, 1770, -1),
    ("CRO", "CAN", 1890, 1800, 1),
    ("ESP", "GER", 1960, 1960, 0),
    ("CMR", "SRB", 1680, 1780, 0),
    ("KOR", "GHA", 1770, 1720, -1),
    ("BRA", "SUI", 1990, 1820, 1),
    ("POR", "URU", 1930, 1860, 1),
    ("NED", "QAT", 1900, 1630, 1),
    ("ECU", "SEN", 1750, 1780, -1),
    ("WAL", "ENG", 1760, 1950, -1),
    ("IRN", "USA", 1720, 1830, -1),
    ("AUS", "DEN", 1740, 1850, 1),
    ("TUN", "FRA", 1680, 1980, 1),
    ("POL", "ARG", 1780, 2000, -1),
    ("KSA", "MEX", 1690, 1820, -1),
    ("CRC", "GER", 1720, 1960, -1),
    ("JPN", "ESP", 1790, 1960, 1),
    ("BEL", "CRO", 1950, 1890, 0),
    ("CAN", "MAR", 1800, 1770, -1),
    ("GHA", "URU", 1720, 1860, -1),
    ("KOR", "POR", 1770, 1930, 1),
    ("CMR", "BRA", 1680, 1990, 1),
    ("SRB", "SUI", 1780, 1820, -1),
]

WC2018_DATA = [
    ("RUS", "KSA", 1700, 1660, 1),
    ("EGY", "URU", 1750, 1880, -1),
    ("MAR", "IRN", 1760, 1700, -1),
    ("POR", "ESP", 1900, 1920, 0),
    ("FRA", "AUS", 1960, 1740, 1),
    ("ARG", "ISL", 1980, 1760, 0),
    ("PER", "DEN", 1780, 1830, -1),
    ("CRO", "NGA", 1840, 1770, 1),
    ("ESP", "IRN", 1920, 1700, 1),
    ("GER", "MEX", 1980, 1830, -1),
    ("BRA", "SUI", 1960, 1820, 0),
    ("SWE", "KOR", 1820, 1770, 1),
    ("BEL", "PAN", 1900, 1640, 1),
    ("TUN", "ENG", 1650, 1880, -1),
    ("COL", "JPN", 1860, 1780, -1),
    ("POL", "SEN", 1780, 1760, -1),
    ("RUS", "EGY", 1700, 1750, 1),
    ("POR", "MAR", 1900, 1760, 1),
    ("URU", "KSA", 1880, 1660, 1),
    ("IRN", "ESP", 1700, 1920, -1),
    ("DEN", "AUS", 1830, 1740, 0),
    ("FRA", "PER", 1960, 1780, 1),
    ("ARG", "CRO", 1980, 1840, -1),
    ("NGA", "ISL", 1770, 1760, 1),
    ("BRA", "CRC", 1960, 1720, 1),
    ("GER", "SWE", 1980, 1820, 1),
    ("KOR", "MEX", 1770, 1830, -1),
    ("ENG", "PAN", 1880, 1640, 1),
    ("JPN", "SEN", 1780, 1760, 0),
    ("POL", "COL", 1780, 1860, -1),
    ("URU", "RUS", 1880, 1700, 1),
    ("KSA", "EGY", 1660, 1750, 1),
    ("IRN", "POR", 1700, 1900, 0),
    ("ESP", "MAR", 1920, 1760, 0),
    ("DEN", "FRA", 1830, 1960, 0),
    ("AUS", "PER", 1740, 1780, -1),
    ("ARG", "NGA", 1980, 1770, 1),
    ("ISL", "CRO", 1760, 1840, -1),
    ("NGA", "ARG", 1770, 1980, -1),
    ("SEN", "COL", 1760, 1860, -1),
    ("JPN", "POL", 1780, 1780, 0),
    ("MEX", "SWE", 1830, 1820, -1),
    ("GER", "KOR", 1980, 1770, -1),
    ("ENG", "BEL", 1880, 1900, -1),
    ("TUN", "PAN", 1650, 1640, 1),
]


def _build_historical_features(
    records: list[tuple[str, str, float, float, int]],
    teams_data: dict | None = None,
) -> tuple[list[list[float]], list[int]]:
    """
    Build feature rows from historical records.

    If teams_data is provided (current teams.json), use actual stats for teams
    that also appear in WC2026. For other teams, estimate from ELO.

    Feature scale targets (to match real data distribution):
      elo_diff:                  [-600, +600]
      spi_diff:                  [-60, +60]
      xg_diff:                   [-2, +2]
      xga_diff:                  [-2, +2]
      ppda_ratio:                [0.5, 2.0] (ratio of away/home PPDA, ~1.0 neutral)
      field_tilt_diff:           [-25, +25] (real field_tilt is 38-65%, diff is ±20)
      coach_rating_diff:         [-3, +3]
      squad_depth_diff:          [-5, +5]
      gk_quality_diff:           [-0.3, +0.3]
      set_piece_diff:            [-5, +5]
      shots_in_box_diff:         [-5, +5]
      goal_creating_actions_diff:[-2, +2]
    """
    X = []
    y = []
    for home_code, away_code, home_elo, away_elo, result in records:
        elo_diff = home_elo - away_elo
        # Estimate SPI from ELO (rough linear: ELO ~1700=SPI~75, ELO~2000=SPI~90)
        spi_diff = elo_diff * (15.0 / 300.0)

        # Try to get real stats for teams that exist in current teams.json
        if teams_data and home_code in teams_data and away_code in teams_data:
            home = teams_data[home_code]
            away = teams_data[away_code]
            h_atk = home.get("attack", {})
            a_atk = away.get("attack", {})
            h_def = home.get("defense", {})
            a_def = away.get("defense", {})
            h_adv = home.get("advanced", {})
            a_adv = away.get("advanced", {})
            h_tac = home.get("tactics", {})
            a_tac = away.get("tactics", {})
            xg_diff = h_atk.get("xg_per_game", 1.3) - a_atk.get("xg_per_game", 1.3)
            xga_diff = h_def.get("xga_per_game", 1.1) - a_def.get("xga_per_game", 1.1)
            home_ppda = max(h_adv.get("ppda", 11.0), 0.1)
            away_ppda = max(a_adv.get("ppda", 11.0), 0.1)
            ppda_ratio = away_ppda / home_ppda
            field_tilt_diff = h_adv.get("field_tilt", 48.0) - a_adv.get("field_tilt", 48.0)
            coach_rating_diff = home.get("coach_rating", 7.0) - away.get("coach_rating", 7.0)
            squad_depth_diff = home.get("squad_depth", 5.0) - away.get("squad_depth", 5.0)
            gk_quality_diff = h_def.get("gk_psxg_ga", 0.0) - a_def.get("gk_psxg_ga", 0.0)
            set_piece_diff = h_tac.get("set_piece_quality", 5.0) - a_tac.get("set_piece_quality", 5.0)
            shots_in_box_diff = h_atk.get("shots_in_box_per_game", 5.0) - a_atk.get("shots_in_box_per_game", 5.0)
            goal_creating_actions_diff = h_adv.get("goal_creating_actions", 2.0) - a_adv.get("goal_creating_actions", 2.0)
        else:
            # Estimate from ELO — use realistic scales matching actual data
            # xg_diff: +300 ELO → ~+0.5 xG, scaled to match real data range
            xg_diff = elo_diff / 700.0
            xga_diff = -elo_diff / 1000.0  # better ELO = lower xGA allowed
            # ppda_ratio: neutral 1.0, ±0.2 based on ELO (stronger team presses more)
            ppda_ratio = max(0.5, min(2.0, 1.0 - elo_diff / 3000.0))
            # field_tilt_diff: stronger team dominates territory (~+5 per 300 ELO)
            field_tilt_diff = elo_diff / 60.0
            # New features estimated from ELO for historical data
            coach_rating_diff = elo_diff / 600.0    # rough proxy
            squad_depth_diff = elo_diff / 300.0     # rough proxy
            gk_quality_diff = elo_diff / 6000.0     # small signal
            set_piece_diff = elo_diff / 300.0        # rough proxy
            shots_in_box_diff = elo_diff / 150.0     # rough proxy
            goal_creating_actions_diff = elo_diff / 300.0  # rough proxy

        X.append([
            elo_diff, spi_diff, xg_diff, xga_diff, ppda_ratio, field_tilt_diff,
            coach_rating_diff, squad_depth_diff, gk_quality_diff, set_piece_diff,
            shots_in_box_diff, goal_creating_actions_diff,
        ])
        y.append(result)
    return X, y


def _build_wc2026_features(
    results_path: str,
    teams_path: str,
) -> tuple[list[list[float]], list[int]]:
    """
    Build feature rows from WC2026 actual results using current team stats.
    """
    if not os.path.exists(results_path) or not os.path.exists(teams_path):
        return [], []

    with open(results_path, "r", encoding="utf-8") as f:
        results_data = json.load(f)
    with open(teams_path, "r", encoding="utf-8") as f:
        teams_data = json.load(f)

    matches = results_data.get("matches", [])
    X = []
    y = []

    for m in matches:
        if not m.get("played", True):
            continue
        t1 = m.get("t1", "")
        t2 = m.get("t2", "")
        s1 = m.get("score1", 0)
        s2 = m.get("score2", 0)

        if t1 not in teams_data or t2 not in teams_data:
            continue

        home = teams_data[t1]
        away = teams_data[t2]

        elo_diff = home.get("elo_rating", 1800) - away.get("elo_rating", 1800)
        spi_diff = home.get("spi_rating", 80.0) - away.get("spi_rating", 80.0)

        h_atk = home.get("attack", {})
        a_atk = away.get("attack", {})
        h_def = home.get("defense", {})
        a_def = away.get("defense", {})
        h_adv = home.get("advanced", {})
        a_adv = away.get("advanced", {})

        xg_diff = h_atk.get("xg_per_game", 1.3) - a_atk.get("xg_per_game", 1.3)
        xga_diff = h_def.get("xga_per_game", 1.1) - a_def.get("xga_per_game", 1.1)
        home_ppda = max(h_adv.get("ppda", 10.0), 0.1)
        away_ppda = max(a_adv.get("ppda", 10.0), 0.1)
        ppda_ratio = away_ppda / home_ppda
        field_tilt_diff = h_adv.get("field_tilt", 0.5) - a_adv.get("field_tilt", 0.5)
        h_tac = home.get("tactics", {})
        a_tac = away.get("tactics", {})
        coach_rating_diff = home.get("coach_rating", 7.0) - away.get("coach_rating", 7.0)
        squad_depth_diff = home.get("squad_depth", 5.0) - away.get("squad_depth", 5.0)
        gk_quality_diff = h_def.get("gk_psxg_ga", 0.0) - a_def.get("gk_psxg_ga", 0.0)
        set_piece_diff = h_tac.get("set_piece_quality", 5.0) - a_tac.get("set_piece_quality", 5.0)
        shots_in_box_diff = h_atk.get("shots_in_box_per_game", 5.0) - a_atk.get("shots_in_box_per_game", 5.0)
        goal_creating_actions_diff = h_adv.get("goal_creating_actions", 2.0) - a_adv.get("goal_creating_actions", 2.0)

        X.append([
            elo_diff, spi_diff, xg_diff, xga_diff, ppda_ratio, field_tilt_diff,
            coach_rating_diff, squad_depth_diff, gk_quality_diff, set_piece_diff,
            shots_in_box_diff, goal_creating_actions_diff,
        ])

        if s1 > s2:
            y.append(1)
        elif s1 < s2:
            y.append(-1)
        else:
            y.append(0)

    return X, y


def train_ml_model(X: np.ndarray, y: np.ndarray, out_path: str) -> None:
    """Train LogisticRegression and save coefficients to JSON."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    print(f"  Training LogisticRegression on {len(X)} samples…")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    clf = LogisticRegression(C=0.5, solver="lbfgs", max_iter=1000, random_state=42)
    clf.fit(X_scaled, y)

    # Accuracy
    preds = clf.predict(X_scaled)
    acc = (preds == y).mean()
    print(f"  Training accuracy: {acc:.3f} (expected ~0.50–0.60 for football)")

    # Classes should be [-1, 0, 1]
    classes = clf.classes_.tolist()
    print(f"  Classes: {classes}")

    model_data = {
        "mean": scaler.mean_.tolist(),
        "std": scaler.scale_.tolist(),
        "coef": clf.coef_.tolist(),        # shape (n_classes, n_features)
        "intercept": clf.intercept_.tolist(),
        "classes": classes,
        "feature_names": [
            "elo_diff", "spi_diff", "xg_diff", "xga_diff", "ppda_ratio", "field_tilt_diff",
            "coach_rating_diff", "squad_depth_diff", "gk_quality_diff", "set_piece_diff",
            "shots_in_box_diff", "goal_creating_actions_diff",
        ],
        "n_samples": int(len(X)),
        "training_accuracy": float(acc),
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(model_data, f, indent=2)
    print(f"  Saved → {out_path}")


def train_calibration(
    results_path: str,
    teams_path: str,
    ml_coeff_path: str,
    out_path: str,
) -> None:
    """
    Train simple linear calibration on WC2026 ensemble predictions.
    Uses only the ML model predictions for calibration (avoids circular dependency
    with ensemble.py at training time).
    """
    if not os.path.exists(results_path) or not os.path.exists(teams_path):
        print("  Calibration skipped — missing results or teams data")
        return

    if not os.path.exists(ml_coeff_path):
        print("  Calibration skipped — ML model not trained yet")
        return

    with open(results_path, "r", encoding="utf-8") as f:
        results_data = json.load(f)
    matches = results_data.get("matches", [])

    # Collect predictions and actuals
    pred_home, pred_draw, pred_away = [], [], []
    actual_home, actual_draw, actual_away = [], [], []

    # We need ensemble predictions for each match — import after model is saved
    # to avoid circular issues. Do a lightweight version here.
    with open(ml_coeff_path, "r", encoding="utf-8") as f:
        coeff_data = json.load(f)
    with open(teams_path, "r", encoding="utf-8") as f:
        teams_data = json.load(f)

    mean = np.array(coeff_data["mean"])
    std = np.array(coeff_data["std"])
    coef = np.array(coeff_data["coef"])
    intercept = np.array(coeff_data["intercept"])

    def _softmax_local(x):
        e = np.exp(x - x.max())
        return e / e.sum()

    for m in matches:
        if not m.get("played", True):
            continue
        t1 = m.get("t1", "")
        t2 = m.get("t2", "")
        s1 = m.get("score1", 0)
        s2 = m.get("score2", 0)

        if t1 not in teams_data or t2 not in teams_data:
            continue

        home = teams_data[t1]
        away = teams_data[t2]

        elo_diff = home.get("elo_rating", 1800) - away.get("elo_rating", 1800)
        spi_diff = home.get("spi_rating", 80.0) - away.get("spi_rating", 80.0)
        h_atk = home.get("attack", {})
        a_atk = away.get("attack", {})
        h_def = home.get("defense", {})
        a_def = away.get("defense", {})
        h_adv = home.get("advanced", {})
        a_adv = away.get("advanced", {})
        h_tac = home.get("tactics", {})
        a_tac = away.get("tactics", {})
        xg_diff = h_atk.get("xg_per_game", 1.3) - a_atk.get("xg_per_game", 1.3)
        xga_diff = h_def.get("xga_per_game", 1.1) - a_def.get("xga_per_game", 1.1)
        home_ppda = max(h_adv.get("ppda", 10.0), 0.1)
        away_ppda = max(a_adv.get("ppda", 10.0), 0.1)
        ppda_ratio = away_ppda / home_ppda
        field_tilt_diff = h_adv.get("field_tilt", 0.5) - a_adv.get("field_tilt", 0.5)
        coach_rating_diff = home.get("coach_rating", 7.0) - away.get("coach_rating", 7.0)
        squad_depth_diff = home.get("squad_depth", 5.0) - away.get("squad_depth", 5.0)
        gk_quality_diff = h_def.get("gk_psxg_ga", 0.0) - a_def.get("gk_psxg_ga", 0.0)
        set_piece_diff = h_tac.get("set_piece_quality", 5.0) - a_tac.get("set_piece_quality", 5.0)
        shots_in_box_diff = h_atk.get("shots_in_box_per_game", 5.0) - a_atk.get("shots_in_box_per_game", 5.0)
        goal_creating_actions_diff = h_adv.get("goal_creating_actions", 2.0) - a_adv.get("goal_creating_actions", 2.0)

        feat = np.array([
            elo_diff, spi_diff, xg_diff, xga_diff, ppda_ratio, field_tilt_diff,
            coach_rating_diff, squad_depth_diff, gk_quality_diff, set_piece_diff,
            shots_in_box_diff, goal_creating_actions_diff,
        ])
        std_safe = np.where(std < 1e-9, 1.0, std)
        x = (feat - mean) / std_safe
        scores = coef @ x + intercept
        probs = _softmax_local(scores)
        # classes: [-1, 0, 1] → [away, draw, home]
        ph, pd, pa = float(probs[2]), float(probs[1]), float(probs[0])

        pred_home.append(ph)
        pred_draw.append(pd)
        pred_away.append(pa)

        actual_home.append(1 if s1 > s2 else 0)
        actual_draw.append(1 if s1 == s2 else 0)
        actual_away.append(1 if s2 > s1 else 0)

    n = len(pred_home)
    if n < 5:
        print(f"  Calibration skipped — only {n} matches with team data")
        # Save identity calibration
        calib_data = {"alpha_home": 1.0, "beta_home": 0.0,
                      "alpha_draw": 1.0, "beta_draw": 0.0,
                      "alpha_away": 1.0, "beta_away": 0.0,
                      "n_samples": n}
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(calib_data, f, indent=2)
        return

    print(f"  Calibrating on {n} WC2026 matches…")

    from sklearn.linear_model import LinearRegression

    def _fit_calibration(pred: list[float], actual: list[float]) -> tuple[float, float]:
        X_cal = np.array(pred).reshape(-1, 1)
        y_cal = np.array(actual)
        lr = LinearRegression()
        lr.fit(X_cal, y_cal)
        return float(lr.coef_[0]), float(lr.intercept_)

    alpha_h, beta_h = _fit_calibration(pred_home, actual_home)
    alpha_d, beta_d = _fit_calibration(pred_draw, actual_draw)
    alpha_a, beta_a = _fit_calibration(pred_away, actual_away)

    # Constrain to reasonable range to avoid degenerate calibrations
    alpha_h = max(0.5, min(2.0, alpha_h))
    alpha_d = max(0.5, min(2.0, alpha_d))
    alpha_a = max(0.5, min(2.0, alpha_a))

    calib_data = {
        "alpha_home": alpha_h, "beta_home": beta_h,
        "alpha_draw": alpha_d, "beta_draw": beta_d,
        "alpha_away": alpha_a, "beta_away": beta_a,
        "n_samples": n,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(calib_data, f, indent=2)
    print(f"  Saved → {out_path}")
    print(f"    Home:  alpha={alpha_h:.3f}, beta={beta_h:.3f}")
    print(f"    Draw:  alpha={alpha_d:.3f}, beta={beta_d:.3f}")
    print(f"    Away:  alpha={alpha_a:.3f}, beta={beta_a:.3f}")


def main() -> None:
    print("=== Training ML model and calibration ===")

    results_path = str(ROOT / "docs" / "data" / "results.json")
    teams_path = str(ROOT / "data" / "teams.json")
    ml_coeff_path = str(ROOT / "data" / "ml_coefficients.json")
    calib_path = str(ROOT / "data" / "calibration.json")

    # ── Build training dataset ────────────────────────────────────────────────
    print("\n1. Building training dataset…")

    # Load teams for use in both historical feature extraction and WC2026
    teams_data: dict = {}
    if os.path.exists(teams_path):
        with open(teams_path, "r", encoding="utf-8") as f:
            teams_data = json.load(f)

    X_hist, y_hist = _build_historical_features(WC2022_DATA + WC2018_DATA, teams_data)
    X_wc26, y_wc26 = _build_wc2026_features(results_path, teams_path)

    print(f"   Historical samples (WC2018+2022): {len(X_hist)}")
    print(f"   WC2026 samples: {len(X_wc26)}")

    X_all = X_hist + X_wc26
    y_all = y_hist + y_wc26

    if len(X_all) < 10:
        print("ERROR: Not enough training data")
        sys.exit(1)

    X_np = np.array(X_all, dtype=float)
    y_np = np.array(y_all, dtype=int)

    # ── Train ML model ────────────────────────────────────────────────────────
    print("\n2. Training LogisticRegression…")
    train_ml_model(X_np, y_np, ml_coeff_path)

    # ── Train calibration ─────────────────────────────────────────────────────
    print("\n3. Training calibration…")
    train_calibration(results_path, teams_path, ml_coeff_path, calib_path)

    print("\n=== Training complete ===")


if __name__ == "__main__":
    main()
