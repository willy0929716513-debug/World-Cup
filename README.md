# ⚽ Football Prediction System — World Cup 2026

職業級足球比分預測框架，整合 7 個統計模型 × 14 維度分析 × 100,000 次 Monte Carlo 模擬。

## 快速使用

```bash
pip install -r requirements.txt

# 阿根廷 vs 巴西（預設示例）
python main.py ARG BRA

# 指定場地、日期與賽制
python main.py ESP FRA --stage "Quarter-Final" --venue "AT&T Stadium, Dallas" --date "2026-07-04"

# 查看所有可用球隊代碼
python main.py --list
```

## 系統架構

```
main.py                     ← CLI 入口
config/settings.py          ← 全域設定（模型權重 / ELO / DC-ρ 等）
data/teams.json             ← 球隊完整數據庫
src/
  data/
    structures.py           ← 所有資料類別（TeamData / AttackStats / …）
    loader.py               ← JSON → Python 物件轉換
  models/
    elo.py                  ← ELO Rating 模型
    poisson.py              ← 獨立 Poisson 模型
    dixon_coles.py          ← Dixon-Coles (1997) 修正模型
    xg_model.py             ← Expected Goals 模型
    market.py               ← 市場賠率反推模型
    monte_carlo.py          ← 100,000 次 Monte Carlo 模擬
    ensemble.py             ← 加權整合模型
  report/
    generator.py            ← Rich 彩色終端報告輸出
```

## 7 個預測模型

| 模型 | 權重 | 說明 |
|------|------|------|
| Dixon-Coles | 25% | 修正低比分相關性的 Poisson |
| xG Model | 25% | 基於預期進球，含陣容折扣 |
| ELO | 20% | ELO 評分差異 → 勝率 |
| Market | 20% | 莊家賠率反推真實機率 |
| Monte Carlo | 10% | 10 萬次模擬帶入 Gamma 不確定性 |

## 可用球隊

ARG BRA FRA ENG ESP GER POR NED URU USA MAR

在 `data/teams.json` 中依照現有格式新增球隊，無需修改任何程式碼。
