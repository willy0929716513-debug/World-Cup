"""Rich-powered terminal report generator."""
from __future__ import annotations
import math
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text
from rich.columns import Columns
from rich.rule import Rule

from src.data.structures import TeamData, EnsembleResult, MarketData, MatchEnvironment


console = Console(width=110)

# ── Colour palette ─────────────────────────────────────────────────────────────
C_HOME   = "bold cyan"
C_AWAY   = "bold magenta"
C_WIN    = "bold green"
C_DRAW   = "bold yellow"
C_LOSS   = "bold red"
C_HEADER = "bold white on dark_blue"
C_GOLD   = "bold yellow"
C_DIM    = "dim"
C_ACCENT = "bold bright_white"


def _prob_bar(p: float, width: int = 28) -> str:
    """Unicode progress bar for a probability."""
    filled = round(p * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{C_WIN if p >= 0.45 else C_DRAW if p >= 0.28 else C_LOSS}]{bar}[/] {p*100:.1f}%"


def _outcome_char(outcome: str) -> str:
    colours = {"W": f"[{C_WIN}]W[/]", "D": f"[{C_DRAW}]D[/]", "L": f"[{C_LOSS}]L[/]"}
    return colours.get(outcome, outcome)


def _form_string_rich(team: TeamData, n: int = 10) -> str:
    outcomes = [m.outcome for m in team.recent_matches[-n:]]
    return " ".join(_outcome_char(o) for o in outcomes)


def _stars(rating: float, total: int = 10) -> str:
    filled = round(rating)
    return "★" * filled + "☆" * (total - filled)


def _confidence_from_probs(p_home: float, p_draw: float, p_away: float) -> tuple[int, str]:
    """Derive confidence score 1–10 from probability spread."""
    dominant = max(p_home, p_draw, p_away)
    if dominant >= 0.65:
        level, label = 9, "極高"
    elif dominant >= 0.55:
        level, label = 8, "高"
    elif dominant >= 0.48:
        level, label = 7, "中高"
    elif dominant >= 0.42:
        level, label = 6, "中"
    elif dominant >= 0.36:
        level, label = 5, "中低"
    else:
        level, label = 4, "低"
    return level, label


def _value_assessment(true_p: float, mkt_odds: float) -> str:
    if mkt_odds <= 1.0:
        return "[dim]N/A[/]"
    implied = 1.0 / mkt_odds
    edge = true_p - implied
    if edge >= 0.06:
        return f"[bold green]價值佳 +{edge*100:.1f}%[/]"
    if edge >= 0.02:
        return f"[green]輕微價值 +{edge*100:.1f}%[/]"
    if edge >= -0.02:
        return f"[yellow]公道 ({edge*100:+.1f}%)[/]"
    return f"[red]無價值 {edge*100:.1f}%[/]"


# ── Section printers ──────────────────────────────────────────────────────────

def _print_header(
    home: TeamData, away: TeamData,
    match_date: str, venue: str, competition: str, stage: str,
) -> None:
    console.print()
    console.rule(f"[bold bright_yellow]⚽  FIFA WORLD CUP 2026 — MATCH PREDICTION SYSTEM  ⚽[/]",
                 style="bright_yellow")
    console.print()

    info = Table(box=box.SIMPLE_HEAVY, show_header=False, padding=(0, 2))
    info.add_column(justify="right", style="dim")
    info.add_column(justify="left", style="bright_white")
    info.add_row("比賽", f"[{C_HOME}]{home.name}[/]  vs  [{C_AWAY}]{away.name}[/]")
    info.add_row("賽事", f"{competition} — {stage}")
    info.add_row("時間", match_date)
    info.add_row("場地", venue)
    console.print(Panel(info, title="【比賽資訊】", border_style="bright_yellow", expand=False))
    console.print()


def _print_team_overview(home: TeamData, away: TeamData) -> None:
    t = Table(title="【球隊整體實力比較】", box=box.ROUNDED, border_style="bright_yellow",
              header_style=C_HEADER, show_lines=True)
    t.add_column("指標", style="bold", justify="left", min_width=22)
    t.add_column(home.name, justify="center", style=C_HOME, min_width=22)
    t.add_column(away.name, justify="center", style=C_AWAY, min_width=22)

    def row(label: str, h_val, a_val, fmt: str = "{}",
            better: str = "low") -> None:
        hv = fmt.format(h_val)
        av = fmt.format(a_val)
        if better == "low":
            h_mark = "[green]◀[/]" if h_val < a_val else ""
            a_mark = "[green]◀[/]" if a_val < h_val else ""
        else:
            h_mark = "[green]◀[/]" if h_val > a_val else ""
            a_mark = "[green]◀[/]" if a_val > h_val else ""
        t.add_row(label, f"{hv} {h_mark}", f"{av} {a_mark}")

    row("FIFA 世界排名",    home.fifa_ranking,    away.fifa_ranking,    "# {}", better="low")
    row("ELO Rating",      home.elo_rating,      away.elo_rating,      "{:.0f}", better="high")
    row("SPI Rating",      home.spi_rating,      away.spi_rating,      "{:.1f}", better="high")
    row("陣容市值 (億€)",   home.squad_value_m/100, away.squad_value_m/100, "{:.1f}", better="high")
    row("平均年齡",         home.avg_age,         away.avg_age,         "{:.1f}",  better="low")
    row("陣容深度",         home.squad_depth,     away.squad_depth,     "{:.1f}",  better="high")
    row("替補實力",         home.bench_quality,   away.bench_quality,   "{:.1f}",  better="high")
    row("世界盃冠軍次數",   home.wc_titles,       away.wc_titles,       "{}",      better="high")
    row("歷屆最佳成績",     home.wc_best_result,  away.wc_best_result,  "{}",      better="high")
    row("主教練評分",       home.coach_rating,    away.coach_rating,    "{:.1f}",  better="high")

    console.print(t)
    console.print()


def _print_form(home: TeamData, away: TeamData) -> None:
    t = Table(title="【近期狀態】", box=box.ROUNDED, border_style="cyan",
              header_style=C_HEADER, show_lines=True)
    t.add_column("指標", style="bold", min_width=20)
    t.add_column(home.name, justify="center", style=C_HOME, min_width=28)
    t.add_column(away.name, justify="center", style=C_AWAY, min_width=28)

    t.add_row("近10場結果 (→新)", _form_string_rich(home, 10), _form_string_rich(away, 10))
    t.add_row("近5場積分/場",
              f"{home.form_pts(5):.2f} pts",
              f"{away.form_pts(5):.2f} pts")
    t.add_row("近10場勝率",
              f"{home.win_rate(10)*100:.0f}%",
              f"{away.win_rate(10)*100:.0f}%")
    t.add_row("近10場場均進球",
              f"{home.goals_scored_avg(10):.2f}",
              f"{away.goals_scored_avg(10):.2f}")
    t.add_row("近10場場均失球",
              f"{home.goals_conceded_avg(10):.2f}",
              f"{away.goals_conceded_avg(10):.2f}")

    console.print(t)
    console.print()


def _print_attack_defense(home: TeamData, away: TeamData) -> None:
    t = Table(title="【進攻 / 防守數據比較】", box=box.ROUNDED, border_style="green",
              header_style=C_HEADER, show_lines=True)
    t.add_column("指標", style="bold", min_width=24)
    t.add_column(home.name, justify="center", style=C_HOME, min_width=20)
    t.add_column(away.name, justify="center", style=C_AWAY, min_width=20)

    ha, aa = home.attack, away.attack
    hd, ad = home.defense, away.defense

    def ar(label, hv, av, fmt="{:.2f}", better="high"):
        h_mark = "[green]▲[/]" if (hv > av if better == "high" else hv < av) else ""
        a_mark = "[green]▲[/]" if (av > hv if better == "high" else av < hv) else ""
        t.add_row(label, f"{fmt.format(hv)} {h_mark}", f"{fmt.format(av)} {a_mark}")

    console.print("[bold green]  ─── 進攻 ───[/]")
    t.add_section()
    ar("場均進球",          ha.goals_per_game,              aa.goals_per_game)
    ar("場均 xG",           ha.xg_per_game,                 aa.xg_per_game)
    ar("場均 npxG",         ha.npxg_per_game,               aa.npxg_per_game)
    ar("場均射門",          ha.shots_per_game,              aa.shots_per_game)
    ar("場均射正",          ha.shots_on_target_per_game,    aa.shots_on_target_per_game)
    ar("禁區內射門",        ha.shots_in_box_per_game,       aa.shots_in_box_per_game)
    ar("大好機會/場",       ha.big_chances_per_game,        aa.big_chances_per_game)
    ar("射門轉化率",        ha.conversion_rate,             aa.conversion_rate, "{:.1%}")
    ar("控球率",            ha.possession_pct,              aa.possession_pct,  "{:.1f}%")
    ar("傳球成功率",        ha.pass_accuracy_pct,           aa.pass_accuracy_pct, "{:.1f}%")
    ar("定位球得分 %",      ha.set_piece_goals_pct,         aa.set_piece_goals_pct, "{:.0f}%")
    ar("關鍵傳球/場",       ha.key_passes_per_game,         aa.key_passes_per_game)

    t.add_section()
    ar("場均失球",          hd.goals_against_per_game,      ad.goals_against_per_game, better="low")
    ar("場均 xGA",          hd.xga_per_game,                ad.xga_per_game,           better="low")
    ar("零封率",            hd.clean_sheet_pct,             ad.clean_sheet_pct, "{:.0f}%")
    ar("搶截成功率",        hd.tackle_success_pct,          ad.tackle_success_pct, "{:.0f}%")
    ar("攔截/場",           hd.interceptions_per_game,      ad.interceptions_per_game)
    ar("解圍/場",           hd.clearances_per_game,         ad.clearances_per_game)
    ar("空中對抗成功率",    hd.aerial_success_pct,          ad.aerial_success_pct, "{:.0f}%")
    ar("門將撲救率",        hd.gk_save_pct,                 ad.gk_save_pct, "{:.1f}%")
    ar("門將 PSxG-GA",      hd.gk_psxg_ga,                 ad.gk_psxg_ga)

    console.print(t)
    console.print()


def _print_advanced(home: TeamData, away: TeamData) -> None:
    t = Table(title="【進階數據 (Advanced Stats)】", box=box.ROUNDED,
              border_style="blue", header_style=C_HEADER, show_lines=True)
    t.add_column("指標", style="bold", min_width=28)
    t.add_column(home.name, justify="center", style=C_HOME, min_width=20)
    t.add_column(away.name, justify="center", style=C_AWAY, min_width=20)

    ha, aa = home.advanced, away.advanced

    def ar(label, hv, av, fmt="{:.1f}", better="high"):
        h_mark = "[green]▲[/]" if (hv > av if better == "high" else hv < av) else ""
        a_mark = "[green]▲[/]" if (av > hv if better == "high" else av < hv) else ""
        t.add_row(label, f"{fmt.format(hv)} {h_mark}", f"{fmt.format(av)} {a_mark}")

    ar("PPDA (逼搶強度, 低=強)",   ha.ppda,                     aa.ppda, better="low")
    ar("Field Tilt (佔位傾斜)",    ha.field_tilt,               aa.field_tilt, "{:.1f}%")
    ar("Deep Completion/場",       ha.deep_completion_per_game, aa.deep_completion_per_game)
    ar("Progressive Passes/場",    ha.progressive_passes,       aa.progressive_passes)
    ar("Progressive Carries/場",   ha.progressive_carries,      aa.progressive_carries)
    ar("Shot Creating Actions/場", ha.shot_creating_actions,    aa.shot_creating_actions)
    ar("Goal Creating Actions/場", ha.goal_creating_actions,    aa.goal_creating_actions)
    ar("xPTS/場",                  ha.xpts_per_game,            aa.xpts_per_game)

    console.print(t)
    console.print()


def _print_tactics(home: TeamData, away: TeamData) -> None:
    t = Table(title="【戰術分析】", box=box.ROUNDED, border_style="magenta",
              header_style=C_HEADER, show_lines=True)
    t.add_column("指標", style="bold", min_width=22)
    t.add_column(home.name, justify="center", style=C_HOME, min_width=22)
    t.add_column(away.name, justify="center", style=C_AWAY, min_width=22)

    ht, at = home.tactics, away.tactics
    t.add_row("主要陣型",     ht.primary_formation,   at.primary_formation)
    t.add_row("備用陣型",     ht.secondary_formation, at.secondary_formation)
    t.add_row("打法風格",
              "控球" if ht.possession_style else "反擊",
              "控球" if at.possession_style else "反擊")
    t.add_row("高位逼搶",
              "[green]是[/]" if ht.high_press else "[red]否[/]",
              "[green]是[/]" if at.high_press else "[red]否[/]")
    t.add_row("逼搶強度",     f"{ht.press_intensity:.1f}/10", f"{at.press_intensity:.1f}/10")
    t.add_row("防線高度",     ht.defensive_line,       at.defensive_line)
    t.add_row("邊路進攻比例", f"{ht.wide_play_pct:.0f}%",   f"{at.wide_play_pct:.0f}%")
    t.add_row("定位球品質",   f"{ht.set_piece_quality:.1f}/10", f"{at.set_piece_quality:.1f}/10")
    t.add_row("臨場調整能力", f"{ht.tactical_flexibility:.1f}/10", f"{at.tactical_flexibility:.1f}/10")

    console.print(t)
    console.print()


def _print_players(home: TeamData, away: TeamData) -> None:
    console.print(Panel(
        f"[{C_HOME}]【{home.name} 關鍵球員】[/]",
        border_style="cyan", expand=False
    ))
    pt = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    pt.add_column("姓名", min_width=22)
    pt.add_column("位置", justify="center", width=6)
    pt.add_column("俱樂部", min_width=18)
    pt.add_column("年齡", justify="center", width=5)
    pt.add_column("本賽季", justify="center", width=10)
    pt.add_column("狀態", justify="center", width=10)
    pt.add_column("傷停", width=18)
    for p in home.key_players:
        status = "[red]傷[/]" if p.is_injured else "[yellow]停賽[/]" if p.is_suspended else "[green]可用[/]"
        detail = f"[dim]{p.injury_detail}[/]" if p.injury_detail else ""
        pt.add_row(
            p.name, p.position, p.club, str(p.age),
            f"{p.goals_season}G {p.assists_season}A",
            status, detail
        )
    console.print(pt)

    if home.injured_players:
        inj_names = ", ".join(p.name + (f" ({p.injury_detail})" if p.injury_detail else "")
                               for p in home.injured_players)
        console.print(f"  [{C_LOSS}]⚠ 傷病名單:[/] {inj_names}")
    if home.suspended_players:
        sus_names = ", ".join(p.name for p in home.suspended_players)
        console.print(f"  [yellow]⚠ 停賽名單:[/] {sus_names}")
    console.print()

    console.print(Panel(
        f"[{C_AWAY}]【{away.name} 關鍵球員】[/]",
        border_style="magenta", expand=False
    ))
    pt2 = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    pt2.add_column("姓名", min_width=22)
    pt2.add_column("位置", justify="center", width=6)
    pt2.add_column("俱樂部", min_width=18)
    pt2.add_column("年齡", justify="center", width=5)
    pt2.add_column("本賽季", justify="center", width=10)
    pt2.add_column("狀態", justify="center", width=10)
    pt2.add_column("傷停", width=18)
    for p in away.key_players:
        status = "[red]傷[/]" if p.is_injured else "[yellow]停賽[/]" if p.is_suspended else "[green]可用[/]"
        detail = f"[dim]{p.injury_detail}[/]" if p.injury_detail else ""
        pt2.add_row(
            p.name, p.position, p.club, str(p.age),
            f"{p.goals_season}G {p.assists_season}A",
            status, detail
        )
    console.print(pt2)

    if away.injured_players:
        inj_names = ", ".join(p.name + (f" ({p.injury_detail})" if p.injury_detail else "")
                               for p in away.injured_players)
        console.print(f"  [{C_LOSS}]⚠ 傷病名單:[/] {inj_names}")
    if away.suspended_players:
        sus_names = ", ".join(p.name for p in away.suspended_players)
        console.print(f"  [yellow]⚠ 停賽名單:[/] {sus_names}")
    console.print()


def _print_model_results(result: EnsembleResult, home: TeamData, away: TeamData) -> None:
    t = Table(title="【各模型預測結果】", box=box.ROUNDED, border_style="bright_yellow",
              header_style=C_HEADER, show_lines=True)
    t.add_column("模型", style="bold", min_width=18)
    t.add_column(f"{home.name} 勝", justify="center", min_width=14, style=C_HOME)
    t.add_column("平局", justify="center", min_width=14, style=C_DRAW)
    t.add_column(f"{away.name} 勝", justify="center", min_width=14, style=C_AWAY)
    t.add_column("λ主 / λ客", justify="center", min_width=16)

    for r in result.model_results:
        t.add_row(
            r.model_name,
            f"{r.p_home*100:.1f}%",
            f"{r.p_draw*100:.1f}%",
            f"{r.p_away*100:.1f}%",
            f"{r.lambda_home:.2f} / {r.lambda_away:.2f}",
        )

    t.add_section()
    t.add_row(
        "[bold bright_yellow]★ 綜合 Ensemble[/]",
        f"[bold]{result.p_home*100:.1f}%[/]",
        f"[bold]{result.p_draw*100:.1f}%[/]",
        f"[bold]{result.p_away*100:.1f}%[/]",
        f"[bold]{result.lambda_home:.2f} / {result.lambda_away:.2f}[/]",
    )
    console.print(t)
    console.print()

    # Probability bars
    console.print(Panel(
        "\n".join([
            f"  [{C_HOME}]{home.name:>18} 勝[/]  {_prob_bar(result.p_home)}",
            f"  [{C_DRAW}]{'平局':>18}[/]     {_prob_bar(result.p_draw)}",
            f"  [{C_AWAY}]{away.name:>18} 勝[/]  {_prob_bar(result.p_away)}",
        ]),
        title="【主勝 / 平局 / 客勝機率】",
        border_style="bright_yellow",
    ))
    console.print()


def _print_score_predictions(result: EnsembleResult, home: TeamData, away: TeamData) -> None:
    # ── Total goals ─────────────────────────────────────────────────────────
    tg = result.total_goal_probs()
    tgt = Table(title="【總進球數機率分佈】", box=box.ROUNDED, border_style="green",
                header_style=C_HEADER, show_lines=False)
    tgt.add_column("總進球", justify="center", style="bold", width=10)
    tgt.add_column("機率", justify="left", min_width=40)
    for g in range(7):
        label = f"{g}+" if g == 6 else str(g)
        p = sum(v for k, v in tg.items() if (k >= g if g == 6 else k == g))
        tgt.add_row(label, _prob_bar(p))
    console.print(tgt)
    console.print()

    # ── BTTS ────────────────────────────────────────────────────────────────
    btts_yes = result.btts_prob()
    btts_no  = 1.0 - btts_yes
    btts_t = Table(title="【BTTS — 雙方均進球】", box=box.SIMPLE, header_style=C_HEADER)
    btts_t.add_column("", justify="center", width=12)
    btts_t.add_column("機率", justify="left", min_width=40)
    btts_t.add_row("[green]YES[/]", _prob_bar(btts_yes))
    btts_t.add_row("[red]NO[/]",  _prob_bar(btts_no))
    console.print(btts_t)
    console.print()

    # ── Top 10 scores ────────────────────────────────────────────────────────
    top10 = result.most_likely_scores[:10]
    st = Table(title="【最可能比分 Top 10】", box=box.ROUNDED, border_style="bright_yellow",
               header_style=C_HEADER, show_lines=False)
    st.add_column("排名", justify="center", width=6)
    st.add_column("比分", justify="center", style="bold bright_white", width=12)
    st.add_column("說明", justify="center", width=12)
    st.add_column("機率", justify="left", min_width=36)
    for i, ((h, a), p) in enumerate(top10, 1):
        if h > a:
            desc = f"[{C_HOME}]{home.short_name} 勝[/]"
        elif h < a:
            desc = f"[{C_AWAY}]{away.short_name} 勝[/]"
        else:
            desc = f"[{C_DRAW}]平局[/]"
        st.add_row(f"#{i}", f"{h} - {a}", desc, _prob_bar(p, 24))
    console.print(st)
    console.print()

    # ── Cold scores (longshots with reasonable probability) ───────────────────
    cold_candidates = [
        (score, p) for score, p in result.score_probs.items()
        if p >= 0.010 and sum(score) >= 4
    ]
    cold_candidates.sort(key=lambda x: -x[1])
    cold3 = cold_candidates[:3] if cold_candidates else []

    if cold3:
        ct = Table(title="【冷門比分（高賠率但具合理機率）】", box=box.SIMPLE,
                   header_style=C_HEADER)
        ct.add_column("比分", justify="center", style="bold", width=12)
        ct.add_column("發生機率", justify="center", width=14)
        ct.add_column("隱含賠率", justify="center", width=14)
        ct.add_column("說明", justify="left")
        for (h, a), p in cold3:
            implied_odds = 1.0 / p
            ct.add_row(
                f"{h} - {a}",
                f"{p*100:.1f}%",
                f"{implied_odds:.1f}",
                "進球多的比賽，適合攻強隊" if h + a >= 5 else "冷門大比分"
            )
        console.print(ct)
        console.print()


def _print_betting(result: EnsembleResult, home: TeamData, away: TeamData,
                   market: Optional[MarketData]) -> None:
    if market is None:
        return
    t = Table(title="【投注價值分析】", box=box.ROUNDED, border_style="gold1",
              header_style=C_HEADER, show_lines=True)
    t.add_column("項目", style="bold", min_width=22)
    t.add_column("市場賠率", justify="center", min_width=14)
    t.add_column("市場隱含機率", justify="center", min_width=16)
    t.add_column("模型機率", justify="center", min_width=14)
    t.add_column("價值評估", justify="center", min_width=24)

    t.add_row(
        f"{home.name} 勝 (1)",
        f"{market.odds_home:.2f}",
        f"{1/market.odds_home*100:.1f}%",
        f"{result.p_home*100:.1f}%",
        _value_assessment(result.p_home, market.odds_home),
    )
    t.add_row(
        "平局 (X)",
        f"{market.odds_draw:.2f}",
        f"{1/market.odds_draw*100:.1f}%",
        f"{result.p_draw*100:.1f}%",
        _value_assessment(result.p_draw, market.odds_draw),
    )
    t.add_row(
        f"{away.name} 勝 (2)",
        f"{market.odds_away:.2f}",
        f"{1/market.odds_away*100:.1f}%",
        f"{result.p_away*100:.1f}%",
        _value_assessment(result.p_away, market.odds_away),
    )

    tg = result.total_goal_probs()
    p_over = sum(v for k, v in tg.items() if k > market.ou_line)
    p_under = 1.0 - p_over
    t.add_section()
    t.add_row(
        f"大球 Over {market.ou_line:.1f}",
        f"{market.over_odds:.2f}",
        f"{1/market.over_odds*100:.1f}%",
        f"{p_over*100:.1f}%",
        _value_assessment(p_over, market.over_odds),
    )
    t.add_row(
        f"小球 Under {market.ou_line:.1f}",
        f"{market.under_odds:.2f}",
        f"{1/market.under_odds*100:.1f}%",
        f"{p_under*100:.1f}%",
        _value_assessment(p_under, market.under_odds),
    )

    ah_line = market.asian_handicap_line
    ah_label = f"讓球 {ah_line:+.2f}"
    console.print(t)
    console.print(
        f"  亞洲讓球盤: [bold]{ah_label}[/]  "
        f"主{market.asian_handicap_home_odds:.2f} / 客{market.asian_handicap_away_odds:.2f}"
    )
    console.print()


def _print_final(result: EnsembleResult, home: TeamData, away: TeamData) -> None:
    top3 = result.most_likely_scores[:3]
    confidence, conf_label = _confidence_from_probs(result.p_home, result.p_draw, result.p_away)
    stars = "★" * confidence + "☆" * (10 - confidence)

    dominant = max(result.p_home, result.p_draw, result.p_away)
    if dominant == result.p_home:
        winner_str = f"[{C_HOME}]{home.name} 勝[/]"
    elif dominant == result.p_away:
        winner_str = f"[{C_AWAY}]{away.name} 勝[/]"
    else:
        winner_str = f"[{C_DRAW}]平局[/]"

    scores_str = "\n".join(
        f"  {'第'+str(i+1)+'推薦':>8}：[bold bright_white]{h} - {a}[/]  ({p*100:.1f}%)"
        for i, ((h, a), p) in enumerate(top3)
    )

    lam_h = result.lambda_home
    lam_a = result.lambda_away

    reasoning = (
        f"模型綜合預期進球：{home.name} {lam_h:.2f} / {away.name} {lam_a:.2f}\n"
        f"勝出方向：{winner_str}  (機率 {dominant*100:.1f}%)\n"
        f"預期總進球：{lam_h + lam_a:.2f}  |  BTTS 機率：{result.btts_prob()*100:.1f}%"
    )

    body = (
        f"\n{scores_str}\n\n"
        f"  信心等級：[{C_GOLD}]{stars}[/] ({confidence}/10 — {conf_label})\n\n"
        f"  {reasoning}\n"
    )

    console.print(Panel(body, title="【最終預測】", border_style="bright_yellow"))
    console.print()


def _print_risks(home: TeamData, away: TeamData) -> None:
    risks = [
        f"傷病不確定性：任一隊核心球員臨場退出可能大幅改變盤面。",
        f"氣候因素：極端高溫或強風可能使比賽物理強度下降，低分結果機率升高。",
        f"裁判執法：若裁判風格偏嚴，早紅牌可能完全推翻戰術部署。",
        f"心理壓力：世界盃淘汰賽階段心理因素比例可上升至 20–30%，超越純統計預測範圍。",
        f"陣型意外調整：教練臨場改變主要陣型，使戰術分析失效。",
        f"市場流動性：押注量不足時賠率波動大，市場模型可信度下降。",
    ]
    if home.injured_players or away.injured_players:
        inj = ", ".join(
            p.name for p in home.injured_players + away.injured_players
        )
        risks.insert(0, f"⚠ 已知傷病：{inj} — 若確定上場或缺席，需重新評估。")

    body = "\n".join(f"  • {r}" for r in risks)
    console.print(Panel(body, title="【風險因素】", border_style="red"))
    console.print()


# ── Main entry point ───────────────────────────────────────────────────────────

def print_report(
    home: TeamData,
    away: TeamData,
    result: EnsembleResult,
    market: Optional[MarketData] = None,
    match_date: str = "",
    venue: str = "中立場地",
    competition: str = "FIFA World Cup 2026",
    stage: str = "Group Stage",
) -> None:
    if not match_date:
        match_date = datetime.now().strftime("%Y-%m-%d")

    _print_header(home, away, match_date, venue, competition, stage)
    _print_team_overview(home, away)
    _print_form(home, away)
    _print_attack_defense(home, away)
    _print_advanced(home, away)
    _print_tactics(home, away)
    _print_players(home, away)
    _print_model_results(result, home, away)
    _print_score_predictions(result, home, away)
    _print_betting(result, home, away, market)
    _print_final(result, home, away)
    _print_risks(home, away)

    console.rule("[dim]報告由 Football Prediction System v1.0 生成[/]")
    console.print()
