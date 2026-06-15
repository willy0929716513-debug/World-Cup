/* WC2026 Prediction System — Floating Help Button + Modal */
(function(){
'use strict';

const SCHEDULE = [
  {grp:'A',teams:'MEX · RSA · KOR · CZE',  md1:'6/11',md2:'6/17',md3:'6/23'},
  {grp:'B',teams:'CAN · SUI · QAT · BIH',  md1:'6/11',md2:'6/17',md3:'6/23'},
  {grp:'C',teams:'BRA · MAR · SCO · HAI',  md1:'6/12',md2:'6/18',md3:'6/24'},
  {grp:'D',teams:'USA · PAR · AUS · TUR',  md1:'6/12',md2:'6/18',md3:'6/24'},
  {grp:'E',teams:'GER · CUW · CIV · ECU',  md1:'6/13',md2:'6/19',md3:'6/25'},
  {grp:'F',teams:'NED · JPN · SWE · TUN',  md1:'6/13',md2:'6/19',md3:'6/25'},
  {grp:'G',teams:'BEL · EGY · IRN · NZL',  md1:'6/14',md2:'6/20',md3:'6/25'},
  {grp:'H',teams:'ESP · CPV · KSA · URU',  md1:'6/14',md2:'6/20',md3:'6/26'},
  {grp:'I',teams:'FRA · SEN · IRQ · NOR',  md1:'6/15',md2:'6/21',md3:'6/26'},
  {grp:'J',teams:'ARG · ALG · AUT · JOR',  md1:'6/15',md2:'6/21',md3:'6/26'},
  {grp:'K',teams:'POR · COD · UZB · COL',  md1:'6/16',md2:'6/22',md3:'6/26'},
  {grp:'L',teams:'ENG · CRO · GHA · PAN',  md1:'6/16',md2:'6/22',md3:'6/26'},
];

const TABS = [
  {id:'intro',  label:'系統介紹'},
  {id:'predict',label:'比賽預測'},
  {id:'groups', label:'小組賽'},
  {id:'bracket',label:'淘汰賽'},
  {id:'models', label:'預測模型'},
  {id:'schedule',label:'比賽日程'},
  {id:'settings',label:'⚙️ 設定'},
];

const CSS = `
#wc-help-btn{
  position:fixed;bottom:24px;right:24px;z-index:8000;
  width:52px;height:52px;border-radius:50%;border:none;cursor:pointer;
  background:linear-gradient(135deg,#0070ff,#00d4ff);
  color:#fff;font-size:1.4rem;font-weight:700;
  box-shadow:0 4px 24px rgba(0,212,255,.45);
  display:flex;align-items:center;justify-content:center;
  transition:transform .2s,box-shadow .2s;
  font-family:'Orbitron','Inter',sans-serif;
  -webkit-tap-highlight-color:transparent;
}
#wc-help-btn:hover{transform:scale(1.1);box-shadow:0 6px 32px rgba(0,212,255,.65)}
#wc-help-btn:active{transform:scale(.95)}

#wc-help-overlay{
  display:none;position:fixed;inset:0;z-index:9000;
  background:rgba(5,8,15,.88);backdrop-filter:blur(12px);
  align-items:flex-end;justify-content:center;
}
#wc-help-overlay.open{display:flex}
@media(min-width:640px){
  #wc-help-overlay{align-items:center}
}

#wc-help-modal{
  background:#090d1c;border:1px solid rgba(255,255,255,.1);
  border-radius:24px 24px 0 0;width:100%;max-width:680px;
  max-height:92vh;display:flex;flex-direction:column;
  overflow:hidden;box-shadow:0 -8px 48px rgba(0,0,0,.7);
}
@media(min-width:640px){
  #wc-help-modal{border-radius:24px;max-height:86vh}
}

#wc-help-header{
  padding:1.1rem 1.4rem .8rem;border-bottom:1px solid rgba(255,255,255,.08);
  display:flex;align-items:center;gap:.8rem;flex-shrink:0;
}
#wc-help-header-title{
  flex:1;font-family:'Orbitron','Inter',sans-serif;font-size:.88rem;font-weight:900;
  background:linear-gradient(90deg,#00d4ff,#ffd700);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  letter-spacing:1px;
}
#wc-help-close{
  background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);
  color:rgba(255,255,255,.7);width:32px;height:32px;border-radius:50%;
  font-size:1.1rem;cursor:pointer;display:flex;align-items:center;justify-content:center;
  flex-shrink:0;transition:background .2s;
}
#wc-help-close:hover{background:rgba(255,255,255,.14)}

#wc-help-tabs{
  display:flex;gap:.3rem;padding:.6rem 1rem;
  border-bottom:1px solid rgba(255,255,255,.06);
  overflow-x:auto;flex-shrink:0;
  scrollbar-width:none;
}
#wc-help-tabs::-webkit-scrollbar{display:none}
.wc-tab-btn{
  white-space:nowrap;padding:.35rem .8rem;border-radius:20px;
  border:1px solid rgba(255,255,255,.1);background:transparent;
  color:rgba(255,255,255,.45);font-size:.73rem;cursor:pointer;
  transition:all .18s;font-family:'Inter',sans-serif;
  -webkit-tap-highlight-color:transparent;
}
.wc-tab-btn:hover{color:rgba(255,255,255,.8);background:rgba(255,255,255,.06)}
.wc-tab-btn.active{
  background:rgba(0,212,255,.12);border-color:rgba(0,212,255,.4);
  color:#00d4ff;
}

#wc-help-body{
  flex:1;overflow-y:auto;padding:1.2rem 1.4rem 2rem;
  scrollbar-width:thin;scrollbar-color:rgba(0,212,255,.3) transparent;
}
#wc-help-body::-webkit-scrollbar{width:4px}
#wc-help-body::-webkit-scrollbar-thumb{background:rgba(0,212,255,.3);border-radius:2px}

.wc-panel{display:none}
.wc-panel.active{display:block}

.wc-h2{font-family:'Orbitron','Inter',sans-serif;font-size:.82rem;font-weight:900;
  color:#ffd700;letter-spacing:1px;margin-bottom:.9rem;margin-top:1.4rem}
.wc-h2:first-child{margin-top:0}
.wc-p{color:rgba(240,244,255,.7);font-size:.83rem;line-height:1.65;margin-bottom:.75rem}
.wc-ul{color:rgba(240,244,255,.7);font-size:.83rem;line-height:1.65;
  padding-left:1.2rem;margin-bottom:.75rem}
.wc-ul li{margin-bottom:.3rem}
.wc-chip{display:inline-block;background:rgba(0,212,255,.1);border:1px solid rgba(0,212,255,.25);
  border-radius:6px;padding:.15rem .5rem;font-size:.72rem;color:#00d4ff;margin:.15rem .15rem .15rem 0}
.wc-chip.gold{background:rgba(255,215,0,.1);border-color:rgba(255,215,0,.3);color:#ffd700}
.wc-chip.green{background:rgba(0,230,118,.1);border-color:rgba(0,230,118,.3);color:#00e676}

.wc-step{display:flex;gap:.8rem;margin-bottom:.9rem;align-items:flex-start}
.wc-step-num{flex-shrink:0;width:26px;height:26px;border-radius:50%;
  background:linear-gradient(135deg,#0070ff,#00d4ff);
  color:#fff;font-size:.75rem;font-weight:700;
  display:flex;align-items:center;justify-content:center;margin-top:.05rem}
.wc-step-text{color:rgba(240,244,255,.75);font-size:.83rem;line-height:1.6}
.wc-step-text strong{color:rgba(240,244,255,.95)}

.wc-model-row{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);
  border-radius:12px;padding:.75rem 1rem;margin-bottom:.6rem}
.wc-model-name{font-size:.8rem;font-weight:700;color:rgba(240,244,255,.9);margin-bottom:.25rem;
  display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.3rem}
.wc-model-weight{font-size:.7rem;color:#00d4ff;font-family:'Orbitron','Inter',sans-serif}
.wc-model-desc{font-size:.77rem;color:rgba(240,244,255,.55);line-height:1.5}

/* Schedule table */
.wc-sched-table{width:100%;border-collapse:collapse;font-size:.78rem;margin-top:.5rem}
.wc-sched-table th{color:rgba(240,244,255,.4);font-size:.66rem;letter-spacing:1.5px;
  text-transform:uppercase;padding:.4rem .6rem;text-align:left;
  border-bottom:1px solid rgba(255,255,255,.08)}
.wc-sched-table td{padding:.45rem .6rem;border-bottom:1px solid rgba(255,255,255,.04);
  color:rgba(240,244,255,.75);vertical-align:middle}
.wc-sched-table tr:last-child td{border-bottom:none}
.wc-grp-badge{display:inline-block;width:22px;height:22px;border-radius:6px;
  background:rgba(0,212,255,.15);border:1px solid rgba(0,212,255,.3);
  font-family:'Orbitron','Inter',sans-serif;font-size:.7rem;font-weight:900;
  color:#00d4ff;text-align:center;line-height:22px}
.wc-md-date{font-family:'Orbitron','Inter',sans-serif;font-size:.72rem;
  color:#ffd700;white-space:nowrap}

.wc-divider{border:none;border-top:1px solid rgba(255,255,255,.06);margin:1.2rem 0}
.wc-note{background:rgba(255,215,0,.06);border:1px solid rgba(255,215,0,.15);
  border-radius:10px;padding:.7rem 1rem;font-size:.78rem;color:rgba(240,244,255,.65);line-height:1.55}
.wc-note strong{color:#ffd700}

/* Settings form */
.wc-settings-row{margin-bottom:1.4rem}
.wc-settings-label{font-size:.72rem;letter-spacing:1.5px;color:rgba(255,255,255,.45);text-transform:uppercase;margin-bottom:.5rem;display:block}
.wc-settings-input{width:100%;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);color:rgba(255,255,255,.9);font-family:'Inter',sans-serif;font-size:.85rem;padding:.65rem 1rem;border-radius:10px;outline:none;transition:border-color .2s;-webkit-appearance:none;appearance:none}
.wc-settings-input:focus{border-color:rgba(0,212,255,.5)}
.wc-btn-row{display:flex;gap:.6rem;margin-top:.6rem;flex-wrap:wrap}
.wc-save-btn{background:linear-gradient(135deg,#0070ff,#00d4ff);border:none;color:#fff;font-family:'Inter',sans-serif;font-size:.82rem;font-weight:700;padding:.55rem 1.2rem;border-radius:10px;cursor:pointer;transition:opacity .2s;-webkit-tap-highlight-color:transparent}
.wc-save-btn:hover{opacity:.85}
.wc-clear-btn{background:rgba(255,107,107,.1);border:1px solid rgba(255,107,107,.25);color:#ff6b6b;font-family:'Inter',sans-serif;font-size:.82rem;font-weight:600;padding:.55rem 1.2rem;border-radius:10px;cursor:pointer;transition:opacity .2s;-webkit-tap-highlight-color:transparent}
.wc-clear-btn:hover{opacity:.75}
.wc-api-status{font-size:.77rem;margin-top:.55rem;min-height:1.1rem}
.wc-step-link{color:#00d4ff;text-decoration:none}
.wc-step-link:hover{text-decoration:underline}
`;

const PANELS = {
intro: `
<h3 class="wc-h2">⚽ WC2026 Football Prediction System</h3>
<p class="wc-p">本系統整合 <strong>7 種統計預測模型</strong>，透過 <strong>10 萬次 Monte Carlo 模擬</strong> 分析 FIFA 2026 世界盃每場比賽的勝負機率、預期進球數、晉級概率等資訊。</p>

<div class="wc-step"><div class="wc-step-num">1</div><div class="wc-step-text"><strong>首頁</strong> — 選擇任意兩支球隊，設定比賽日期、賽制階段與場地，點擊「開始預測分析」</div></div>
<div class="wc-step"><div class="wc-step-num">2</div><div class="wc-step-text"><strong>預測報告</strong> — 查看詳細勝率分析、比分概率熱力圖、7 模型集成結果與投注建議</div></div>
<div class="wc-step"><div class="wc-step-num">3</div><div class="wc-step-text"><strong>小組賽頁面</strong> — 瀏覽 12 組預測積分榜、晉級概率與所有 72 場小組賽預測</div></div>
<div class="wc-step"><div class="wc-step-num">4</div><div class="wc-step-text"><strong>淘汰賽頁面</strong> — 查看 R32 到決賽的完整賽程預測與奪冠概率排行</div></div>

<hr class="wc-divider">
<h3 class="wc-h2">📱 資料如何產生</h3>
<p class="wc-p">所有預測數據由 GitHub Actions 自動運算並存入靜態 JSON 檔案，每次更新 main 分支時自動重新生成。若頁面顯示「資料尚未生成」，請在 GitHub 上手動觸發 <span class="wc-chip">Build workflow</span>。</p>

<h3 class="wc-h2">🏆 賽制說明</h3>
<ul class="wc-ul">
  <li>48 支球隊分為 12 組（A–L），每組 4 隊</li>
  <li>每組前 2 名 + 各組最佳第三名（共 8 隊）= <strong>32 強</strong></li>
  <li>淘汰賽：32 強 → 16 強 → 8 強 → 4 強 → 決賽</li>
  <li>舉辦地：美國 🇺🇸 / 加拿大 🇨🇦 / 墨西哥 🇲🇽</li>
</ul>
`,

predict: `
<h3 class="wc-h2">📊 如何讀懂預測報告</h3>

<h3 class="wc-h2" style="margin-top:1rem">① 主要勝率區塊</h3>
<p class="wc-p">顯示主隊勝、平局、客隊勝的百分比。數字為 Monte Carlo 模擬統計結果，不是單一模型輸出。</p>

<h3 class="wc-h2">② 比分熱力圖</h3>
<p class="wc-p">6×6 格的熱力圖，橫軸為主隊進球數（0–5），縱軸為客隊進球數（0–5）。顏色越深代表該比分發生概率越高。最可能比分會標示框線。</p>

<h3 class="wc-h2">③ 最可能比分 Top 10</h3>
<p class="wc-p">列出概率最高的 10 個比分組合，每個比分旁邊顯示對應勝負結果（主勝 / 平 / 客勝）。</p>

<h3 class="wc-h2">④ 模型集成表格</h3>
<p class="wc-p">顯示 7 個模型各自對主隊勝率的預測。最右欄 <span class="wc-chip gold">集成</span> 是加權平均結果（各模型權重不同）。</p>

<h3 class="wc-h2">⑤ 投注價值分析</h3>
<p class="wc-p">將系統預測概率與市場賠率對比。若系統概率顯著高於賠率隱含概率，標示為 <span class="wc-chip green">正期望值</span>，代表理論上具有投注價值。</p>

<h3 class="wc-h2">⑥ 風險提示</h3>
<p class="wc-p">列出可能影響預測精準度的因素：傷病、紅牌風險、氣候、心理壓力等統計模型無法完整量化的變量。</p>

<div class="wc-note"><strong>注意：</strong>本系統為統計預測工具，所有結果僅供參考，不構成任何投注建議。足球比賽結果受諸多隨機因素影響。</div>
`,

groups: `
<h3 class="wc-h2">🏟️ 小組賽頁面說明</h3>

<h3 class="wc-h2" style="margin-top:1rem">積分榜預測</h3>
<p class="wc-p">每個小組卡片顯示 4 支球隊的預測最終排名。排名依據為模擬積分、勝負場次的統計平均。</p>
<ul class="wc-ul">
  <li><span class="wc-chip green">晉級</span> 橫條 — 表示該隊晉級 32 強的概率</li>
  <li>前兩名直接晉級，第三名需與其他組第三名競爭最佳 8 席</li>
  <li>🇺🇸🇨🇦🇲🇽 圖示 — 表示主辦國球隊</li>
</ul>

<h3 class="wc-h2">聯合會徽章顏色</h3>
<p class="wc-p">
  <span class="wc-chip" style="background:rgba(68,136,255,.15);border-color:rgba(68,136,255,.3);color:#4488ff">UEFA</span>
  <span class="wc-chip" style="background:rgba(0,204,119,.15);border-color:rgba(0,204,119,.3);color:#00cc77">CONMEBOL</span>
  <span class="wc-chip" style="background:rgba(255,136,68,.15);border-color:rgba(255,136,68,.3);color:#ff8844">CAF</span>
  <span class="wc-chip" style="background:rgba(204,68,255,.15);border-color:rgba(204,68,255,.3);color:#cc44ff">AFC</span>
  <span class="wc-chip" style="background:rgba(255,204,0,.15);border-color:rgba(255,204,0,.3);color:#ffcc00">CONCACAF</span>
  <span class="wc-chip" style="background:rgba(68,221,221,.15);border-color:rgba(68,221,221,.3);color:#44dddd">OFC</span>
</p>

<h3 class="wc-h2">篩選功能</h3>
<p class="wc-p">頂部篩選列可依聯合會（UEFA / CONMEBOL / CAF / AFC / CONCACAF）過濾顯示對應小組。點「全部」可回到完整檢視。</p>

<h3 class="wc-h2">比賽預測切換</h3>
<p class="wc-p">每個小組卡片右上角有「📅 場次」按鈕，點擊可展開該組所有 6 場比賽的預測比分。再次點擊可收合。</p>

<h3 class="wc-h2">最佳第三名面板</h3>
<p class="wc-p">頁面底部顯示所有第三名的晉級概率排名，最高 8 隊晉入 32 強。</p>
`,

bracket: `
<h3 class="wc-h2">🥇 淘汰賽頁面說明</h3>

<h3 class="wc-h2" style="margin-top:1rem">冠亞季軍台</h3>
<p class="wc-p">頁面頂部顯示系統預測的冠（🥇）、亞（🥈）、季軍（🥉），以及各隊的奪冠概率百分比。</p>

<h3 class="wc-h2">奪冠概率排行</h3>
<p class="wc-p">列出所有 32 強球隊的奪冠概率，依概率高低排序，顏色越亮代表概率越高。</p>

<h3 class="wc-h2">完整賽程預測</h3>
<p class="wc-p">頁面下方以橫向捲動表格（📱 手機可左右滑動）顯示從 32 強到決賽的完整預測路徑：</p>
<ul class="wc-ul">
  <li><strong>32 強</strong> — 基於小組積分排名對陣</li>
  <li><strong>16 強</strong> — 勝者對決</li>
  <li><strong>8 強</strong> — 四分之一決賽</li>
  <li><strong>4 強</strong> — 半決賽</li>
  <li><strong>決賽</strong> — 最終冠軍</li>
</ul>
<div class="wc-note"><strong>說明：</strong>預測為基於 ELO 等級分的確定性預測，非 Monte Carlo 隨機模擬結果。奪冠概率才是基於 10 萬次模擬的統計值。</div>
`,

models: `
<h3 class="wc-h2">🤖 預測模型說明</h3>
<p class="wc-p">系統整合以下 7 種模型，透過加權集成得出最終預測：</p>

<div class="wc-model-row">
  <div class="wc-model-name">ELO 等級分模型 <span class="wc-model-weight">權重 20%</span></div>
  <div class="wc-model-desc">基於國際比賽歷史戰績計算的動態等級分系統，反映球隊長期整體實力。勝強隊可獲更多積分，每場賽後即時更新。</div>
</div>

<div class="wc-model-row">
  <div class="wc-model-name">Poisson 進球模型 <span class="wc-model-weight">參與集成</span></div>
  <div class="wc-model-desc">假設每支球隊的進球數服從 Poisson 分佈，依照球隊進攻實力與對手防守能力估算期望進球數，生成完整比分矩陣。</div>
</div>

<div class="wc-model-row">
  <div class="wc-model-name">Dixon-Coles 修正模型 <span class="wc-model-weight">權重 25%</span></div>
  <div class="wc-model-desc">在 Poisson 基礎上修正低比分（0-0、1-0、0-1、1-1）的概率，更準確反映現代足球低進球比賽的頻率。</div>
</div>

<div class="wc-model-row">
  <div class="wc-model-name">xG 期望進球模型 <span class="wc-model-weight">權重 25%</span></div>
  <div class="wc-model-desc">基於球隊近期比賽的期望進球數（xG）統計，衡量「應得」進球能力而非實際進球，過濾運氣因素。</div>
</div>

<div class="wc-model-row">
  <div class="wc-model-name">市場賠率模型 <span class="wc-model-weight">權重 20%</span></div>
  <div class="wc-model-desc">博彩市場匯聚大量資金與資訊，賠率隱含概率通常具有較高預測效力。系統將市場賠率轉換為概率並去除超額收益。</div>
</div>

<div class="wc-model-row">
  <div class="wc-model-name">Monte Carlo 模擬 <span class="wc-model-weight">權重 10%</span></div>
  <div class="wc-model-desc">對整個賽事進行 10,000 次完整模擬，統計各種結果的出現頻率，捕捉賽制結構與對陣籤表帶來的影響。</div>
</div>

<div class="wc-model-row">
  <div class="wc-model-name">集成 Ensemble 模型 <span class="wc-model-weight">最終輸出</span></div>
  <div class="wc-model-desc">對上述各模型的輸出結果進行加權平均，各模型依其歷史準確率與穩定性分配不同權重，得出最終預測概率。</div>
</div>
`,

schedule: `
<h3 class="wc-h2">📅 小組賽比賽日程（2026 年 6 月）</h3>
<p class="wc-p">每組進行三輪比賽，最後一輪（MD3）兩場同時開踢，確保公平競爭。</p>

<div style="overflow-x:auto">
<table class="wc-sched-table">
<thead>
<tr>
  <th>組別</th>
  <th>球隊</th>
  <th>第一輪</th>
  <th>第二輪</th>
  <th>第三輪</th>
</tr>
</thead>
<tbody>
${SCHEDULE.map(s=>`<tr>
  <td><span class="wc-grp-badge">${s.grp}</span></td>
  <td style="font-size:.73rem;color:rgba(240,244,255,.6)">${s.teams}</td>
  <td><span class="wc-md-date">${s.md1}</span></td>
  <td><span class="wc-md-date">${s.md2}</span></td>
  <td><span class="wc-md-date">${s.md3}</span></td>
</tr>`).join('')}
</tbody>
</table>
</div>

<hr class="wc-divider">
<h3 class="wc-h2">📆 賽程總覽</h3>
<ul class="wc-ul">
  <li><strong>小組賽開幕：</strong> 2026 年 6 月 11 日</li>
  <li><strong>小組賽結束：</strong> 2026 年 6 月 26 日</li>
  <li><strong>32 強賽：</strong> 6 月 28 日 – 7 月 1 日</li>
  <li><strong>16 強賽：</strong> 7 月 3 日 – 7 月 6 日</li>
  <li><strong>8 強賽：</strong> 7 月 9 日 – 7 月 10 日</li>
  <li><strong>4 強賽：</strong> 7 月 14 日 – 7 月 15 日</li>
  <li><strong>季軍賽：</strong> 7 月 18 日</li>
  <li><strong>決賽：</strong> 2026 年 7 月 19 日（MetLife Stadium, NJ）</li>
</ul>
<div class="wc-note"><strong>日程為系統預設值，</strong>實際 FIFA 官方場次安排請以官網公告為準。</div>
`,

settings: `
<h3 class="wc-h2">⚙️ 即時賠率設定</h3>
<p class="wc-p">設定 <strong>The Odds API</strong> 金鑰後，預測報告的投注分析區塊將自動更新為 Pinnacle、Bet365 等主流莊家的即時賠率（取代模型估計值）。</p>

<div class="wc-settings-row">
  <label class="wc-settings-label" for="wc-odds-api-key">API 金鑰</label>
  <input type="text" id="wc-odds-api-key" class="wc-settings-input" placeholder="貼入您的 The Odds API 金鑰..." autocomplete="off" spellcheck="false">
  <div class="wc-btn-row">
    <button class="wc-save-btn" id="wc-save-api-key">💾 儲存金鑰</button>
    <button class="wc-clear-btn" id="wc-clear-api-key">🗑 清除</button>
  </div>
  <div id="wc-api-key-status" class="wc-api-status"></div>
</div>

<hr class="wc-divider">
<h3 class="wc-h2">如何取得免費 API 金鑰</h3>
<div class="wc-step"><div class="wc-step-num">1</div><div class="wc-step-text">前往 <strong>the-odds-api.com</strong> 免費注冊帳號（每月 500 次免費請求）</div></div>
<div class="wc-step"><div class="wc-step-num">2</div><div class="wc-step-text">登入後在 <strong>Dashboard</strong> 頁面複製您的 API Key</div></div>
<div class="wc-step"><div class="wc-step-num">3</div><div class="wc-step-text">貼入上方欄位並點擊「儲存金鑰」，之後每次查看比賽報告都會自動套用即時賠率</div></div>

<div class="wc-note" style="margin-top:1rem">
  <strong>注意：</strong>API 金鑰僅儲存於您的本地瀏覽器（localStorage），不會上傳至任何伺服器。每次載入報告頁時會消耗 1 次 API 請求，結果快取 5 分鐘。若賽前無即時賠率，系統自動回退為模型估計值。
</div>
`
};

function build(){
  // Inject CSS
  const style = document.createElement('style');
  style.textContent = CSS;
  document.head.appendChild(style);

  // Floating button
  const btn = document.createElement('button');
  btn.id = 'wc-help-btn';
  btn.setAttribute('aria-label','使用說明');
  btn.textContent = '?';
  document.body.appendChild(btn);

  // Overlay
  const overlay = document.createElement('div');
  overlay.id = 'wc-help-overlay';
  overlay.setAttribute('role','dialog');
  overlay.setAttribute('aria-modal','true');

  // Modal
  const modal = document.createElement('div');
  modal.id = 'wc-help-modal';

  // Header
  const header = document.createElement('div');
  header.id = 'wc-help-header';
  header.innerHTML = `
    <span id="wc-help-header-title">⚽ WC2026 使用說明</span>
    <button id="wc-help-close" aria-label="關閉">✕</button>
  `;

  // Tabs
  const tabBar = document.createElement('div');
  tabBar.id = 'wc-help-tabs';
  tabBar.innerHTML = TABS.map((t,i)=>
    `<button class="wc-tab-btn${i===0?' active':''}" data-tab="${t.id}">${t.label}</button>`
  ).join('');

  // Body
  const body = document.createElement('div');
  body.id = 'wc-help-body';
  body.innerHTML = TABS.map((t,i)=>
    `<div class="wc-panel${i===0?' active':''}" id="wc-panel-${t.id}">${PANELS[t.id]}</div>`
  ).join('');

  modal.appendChild(header);
  modal.appendChild(tabBar);
  modal.appendChild(body);
  overlay.appendChild(modal);
  document.body.appendChild(overlay);

  // Load saved API key into settings input
  const savedApiKey = (typeof localStorage !== 'undefined' && localStorage.getItem('wc_odds_api_key')) || '';
  const apiKeyInput = document.getElementById('wc-odds-api-key');
  if(apiKeyInput) {
    apiKeyInput.value = savedApiKey;
    _updateApiStatus(savedApiKey ? 'saved' : '');
  }

  document.getElementById('wc-save-api-key').addEventListener('click', function(){
    const key = (document.getElementById('wc-odds-api-key').value || '').trim();
    if(!key){ _updateApiStatus('empty'); return; }
    try{ localStorage.setItem('wc_odds_api_key', key); }catch(e){}
    _updateApiStatus('saved');
  });

  document.getElementById('wc-clear-api-key').addEventListener('click', function(){
    try{ localStorage.removeItem('wc_odds_api_key'); }catch(e){}
    document.getElementById('wc-odds-api-key').value = '';
    _updateApiStatus('cleared');
  });

  // Events
  btn.addEventListener('click', open);
  document.getElementById('wc-help-close').addEventListener('click', close);
  overlay.addEventListener('click', function(e){ if(e.target===overlay) close(); });

  tabBar.addEventListener('click', function(e){
    const tb = e.target.closest('.wc-tab-btn');
    if(!tb) return;
    const tid = tb.dataset.tab;
    tabBar.querySelectorAll('.wc-tab-btn').forEach(b=>b.classList.toggle('active', b===tb));
    body.querySelectorAll('.wc-panel').forEach(p=>p.classList.toggle('active', p.id==='wc-panel-'+tid));
    body.scrollTop = 0;
  });

  document.addEventListener('keydown', function(e){
    if(e.key==='Escape' && overlay.classList.contains('open')) close();
  });

  // Expose for external use (e.g. report.html opens settings tab directly)
  window.WCHelp = {
    open: open,
    openTab: function(tabId){
      open();
      setTimeout(function(){
        const tb = tabBar.querySelector('[data-tab="'+tabId+'"]');
        if(tb) tb.click();
      }, 60);
    }
  };
}

/* ── Disclaimer modal (shown once per browser session) ──────────────── */
(function(){
  try{ if(sessionStorage.getItem('wc_disclaimer_ok')) return; }catch(e){}

  const CSS = `
#wc-disc-ov{position:fixed;inset:0;z-index:19000;background:rgba(2,6,23,.95);
  backdrop-filter:blur(16px);display:flex;align-items:center;justify-content:center;
  padding:1rem;animation:discFade .4s ease}
@keyframes discFade{from{opacity:0}to{opacity:1}}
#wc-disc-box{background:#080e1e;border:1px solid rgba(255,215,0,.22);border-radius:22px;
  width:100%;max-width:480px;overflow:hidden;
  box-shadow:0 0 80px rgba(255,215,0,.08),0 40px 80px rgba(0,0,0,.8);position:relative}
#wc-disc-box::before{content:'';position:absolute;top:0;left:10%;right:10%;height:1px;
  background:linear-gradient(90deg,transparent,#ffd700,rgba(0,229,255,.6),transparent)}
#wc-disc-head{padding:1.1rem 1.4rem .9rem;border-bottom:1px solid rgba(255,255,255,.07);
  display:flex;align-items:center;gap:.7rem}
#wc-disc-icon{font-size:1.4rem}
#wc-disc-title{font-family:'Orbitron','Inter',sans-serif;font-size:.78rem;font-weight:900;
  letter-spacing:2px;background:linear-gradient(90deg,#ffd700,#00e5ff);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent}
#wc-disc-body{padding:1.2rem 1.4rem;font-family:'Inter','Space Grotesk',sans-serif;
  font-size:.8rem;line-height:1.7;color:rgba(240,244,255,.72);max-height:55vh;overflow-y:auto}
#wc-disc-body h3{font-size:.72rem;letter-spacing:1.5px;text-transform:uppercase;
  color:rgba(255,215,0,.8);margin:1rem 0 .4rem;font-family:'Orbitron','Inter',sans-serif}
#wc-disc-body h3:first-child{margin-top:0}
#wc-disc-body p{margin-bottom:.5rem}
#wc-disc-body a{color:#00e5ff;text-decoration:none}
#wc-disc-foot{padding:.9rem 1.4rem 1.2rem;border-top:1px solid rgba(255,255,255,.06);
  display:flex;gap:.6rem;align-items:center}
#wc-disc-agree{flex:1;padding:.65rem;
  background:linear-gradient(135deg,rgba(255,215,0,.15),rgba(0,229,255,.08));
  border:1px solid rgba(255,215,0,.35);color:#ffd700;border-radius:11px;
  font-family:'Orbitron','Inter',sans-serif;font-size:.68rem;font-weight:900;
  letter-spacing:.8px;cursor:pointer;transition:all .2s}
#wc-disc-agree:hover{background:rgba(255,215,0,.22);border-color:rgba(255,215,0,.7)}
#wc-disc-age{font-size:.68rem;color:rgba(240,244,255,.35);text-align:center;min-width:60px}
`;

  const style = document.createElement('style');
  style.textContent = CSS;
  document.head.appendChild(style);

  const ov = document.createElement('div');
  ov.id = 'wc-disc-ov';
  ov.innerHTML = `
<div id="wc-disc-box">
  <div id="wc-disc-head">
    <span id="wc-disc-icon">⚠️</span>
    <span id="wc-disc-title">使用聲明 · DISCLAIMER</span>
  </div>
  <div id="wc-disc-body">
    <h3>📊 預測準確性</h3>
    <p>本網站所有 AI 預測結果（包含比分、勝負機率、賠率分析）均由統計模型自動生成，<strong style="color:#ffd700">僅供娛樂及學術參考用途</strong>，不代表任何保證或承諾。預測結果可能與實際比賽結果存在重大差異。</p>

    <h3>🎰 投注免責聲明</h3>
    <p>本網站任何內容均<strong style="color:#ff6b6b">不構成投注建議或金融建議</strong>。任何人因參考本網站資料而進行投注或其他財務行為所造成的損失，本網站概不負責。請依據您所在地區的法律法規謹慎行事。</p>

    <h3>🔐 個人資料與隱私</h3>
    <p>本網站為靜態網頁，<strong>不收集、儲存或傳輸任何使用者個人資料</strong>。您在「設定」中輸入的賠率 API 金鑰僅儲存於您的瀏覽器本機（localStorage），不會上傳至任何伺服器。本站不使用追蹤 Cookie。</p>

    <h3>📋 智慧財產權</h3>
    <p>本網站內容（預測模型、視覺設計、程式碼）受著作權保護。未經授權禁止複製、重製或商業使用。</p>

    <h3>🔞 年齡限制</h3>
    <p>本網站包含博彩賠率分析內容，<strong style="color:#ff6b6b">限 18 歲（或您所在地區法定年齡）以上人士瀏覽</strong>。</p>
  </div>
  <div id="wc-disc-foot">
    <span id="wc-disc-age">18+</span>
    <button id="wc-disc-agree">✓ 我已閱讀並同意，繼續使用</button>
  </div>
</div>`;

  document.body.appendChild(ov);

  document.getElementById('wc-disc-agree').addEventListener('click', function(){
    try{ sessionStorage.setItem('wc_disclaimer_ok','1'); }catch(e){}
    ov.style.animation = 'discFade .3s ease reverse';
    setTimeout(function(){ ov.remove(); }, 280);
  });
})();

function _updateApiStatus(state){
  const el = document.getElementById('wc-api-key-status');
  if(!el) return;
  if(state==='saved')   el.innerHTML = '<span style="color:#00e676">✓ 已儲存 — 下次查看報告頁時將自動載入即時賠率</span>';
  else if(state==='empty')   el.innerHTML = '<span style="color:#ff6b6b">請輸入 API 金鑰</span>';
  else if(state==='cleared') el.innerHTML = '<span style="color:#ff6b6b">已清除 — 將使用模型估計賠率</span>';
  else el.innerHTML = '<span style="color:rgba(255,255,255,.35)">尚未設定 — 將使用模型估計賠率</span>';
}

function open(){
  document.getElementById('wc-help-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function close(){
  document.getElementById('wc-help-overlay').classList.remove('open');
  document.body.style.overflow = '';
}

if(document.readyState === 'loading'){
  document.addEventListener('DOMContentLoaded', build);
} else {
  build();
}
})();
