/* WC2026 — Shared hamburger navigation drawer */
(function () {
  var s = document.createElement('style');
  s.textContent = [
    /* Hide floating help button — it lives inside the drawer */
    '#wc-help-btn{display:none!important}',

    /* Hamburger trigger button */
    '.nd-hamburger{background:none;border:none;cursor:pointer;',
    'color:rgba(255,255,255,.75);font-size:1.25rem;line-height:1;',
    'padding:.32rem .44rem;border-radius:8px;transition:background .18s,color .18s;',
    'flex-shrink:0;-webkit-tap-highlight-color:transparent;}',
    '.nd-hamburger:hover{background:rgba(255,255,255,.09);color:#fff}',

    /* Dim overlay */
    '#nd-overlay{display:none;position:fixed;inset:0;z-index:1900;',
    'background:rgba(2,6,23,.65);backdrop-filter:blur(3px);}',
    '#nd-overlay.open{display:block}',

    /* Slide-in drawer */
    '#nd-drawer{position:fixed;top:0;left:0;bottom:0;z-index:1901;',
    'width:264px;max-width:82vw;background:#070d1e;',
    'border-right:1px solid rgba(0,229,255,.13);',
    'display:flex;flex-direction:column;',
    'transform:translateX(-100%);transition:transform .28s cubic-bezier(.4,0,.2,1);',
    'box-shadow:6px 0 48px rgba(0,0,0,.7);}',
    '#nd-drawer.open{transform:translateX(0)}',

    /* Drawer header */
    '.nd-hd{display:flex;align-items:center;gap:.6rem;',
    'padding:1.05rem 1.2rem .9rem;',
    'border-bottom:1px solid rgba(255,255,255,.07);flex-shrink:0;}',
    '.nd-logo{flex:1;font-size:.88rem;font-weight:900;letter-spacing:2px;',
    'background:linear-gradient(90deg,#00E5FF,#FFD700);',
    '-webkit-background-clip:text;-webkit-text-fill-color:transparent;',
    "font-family:'Orbitron','Inter',sans-serif;}",
    '.nd-close{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);',
    'color:rgba(255,255,255,.55);width:30px;height:30px;border-radius:50%;',
    'cursor:pointer;font-size:1rem;display:flex;align-items:center;',
    'justify-content:center;transition:background .18s;flex-shrink:0;}',
    '.nd-close:hover{background:rgba(255,255,255,.14);color:#fff}',

    /* Nav links */
    '.nd-nav{flex:1;padding:.75rem .65rem;overflow-y:auto;}',
    '.nd-a{display:flex;align-items:center;gap:.6rem;',
    'padding:.7rem 1rem;border-radius:10px;',
    'color:rgba(255,255,255,.62);text-decoration:none;',
    'font-size:.84rem;font-weight:500;transition:all .18s;',
    'border:1px solid transparent;margin-bottom:.15rem;',
    'background:none;width:100%;text-align:left;cursor:pointer;',
    "font-family:'Inter','Space Grotesk',sans-serif;",
    '-webkit-tap-highlight-color:transparent;}',
    '.nd-a:hover{color:#fff;background:rgba(255,255,255,.06);border-color:rgba(255,255,255,.1)}',
    '.nd-a.nd-active{color:#00E5FF;background:rgba(0,229,255,.09);border-color:rgba(0,229,255,.22)}',
    '.nd-a.nd-gold{color:#FFD700}',
    '.nd-a.nd-gold:hover{background:rgba(255,215,0,.07);border-color:rgba(255,215,0,.2)}',
    '.nd-sep{border:none;border-top:1px solid rgba(255,255,255,.07);margin:.5rem .2rem}',

    /* Drawer footer */
    '.nd-foot{padding:.75rem 1.2rem;border-top:1px solid rgba(255,255,255,.05);',
    'flex-shrink:0;text-align:center;}',
  ].join('');
  document.head.appendChild(s);

  /* ── Inject HTML ─────────────────────────────────────────────────────── */
  var el = document.createElement('div');
  el.innerHTML = '<div id="nd-overlay"></div>'
    + '<aside id="nd-drawer" role="dialog" aria-label="導航選單">'
    + '<div class="nd-hd">'
    +   '<span class="nd-logo">⚽ WC 2026 AI</span>'
    +   '<button class="nd-close" id="nd-close-btn" aria-label="關閉">✕</button>'
    + '</div>'
    + '<nav class="nd-nav">'
    +   '<a href="index.html"  class="nd-a nd-page-home">🏠 首頁</a>'
    +   '<a href="groups.html" class="nd-a nd-page-groups">📊 小組賽</a>'
    +   '<a href="bracket.html" class="nd-a nd-page-bracket nd-gold">🏆 淘汰賽對陣表</a>'
    +   '<a href="accuracy.html" class="nd-a nd-page-accuracy">🎯 預測準確度</a>'
    +   '<hr class="nd-sep">'
    +   '<button class="nd-a nd-help-btn">❓ 使用說明</button>'
    + '</nav>'
    + '<div class="nd-foot">'
    +   '<span style="font-size:.58rem;color:rgba(255,255,255,.22);letter-spacing:1px">AI WC2026 · 僅供參考</span>'
    + '</div>'
    + '</aside>';
  document.body.insertBefore(el.firstChild, document.body.firstChild);
  document.body.insertBefore(el.firstChild, document.body.firstChild);

  /* ── Active page highlight ───────────────────────────────────────────── */
  var path = window.location.pathname.split('/').pop() || 'index.html';
  var pageMap = {
    'index.html'   : '.nd-page-home',
    ''             : '.nd-page-home',
    'groups.html'  : '.nd-page-groups',
    'bracket.html' : '.nd-page-bracket',
    'accuracy.html': '.nd-page-accuracy',
  };
  var activeSel = pageMap[path];
  if (activeSel) {
    var activeEl = document.querySelector(activeSel);
    if (activeEl) activeEl.classList.add('nd-active');
  }

  /* ── Open / close ────────────────────────────────────────────────────── */
  window.ndOpen = function () {
    document.getElementById('nd-drawer').classList.add('open');
    document.getElementById('nd-overlay').classList.add('open');
    document.body.style.overflow = 'hidden';
  };
  window.ndClose = function () {
    document.getElementById('nd-drawer').classList.remove('open');
    document.getElementById('nd-overlay').classList.remove('open');
    document.body.style.overflow = '';
  };

  document.getElementById('nd-overlay').addEventListener('click', window.ndClose);
  document.getElementById('nd-close-btn').addEventListener('click', window.ndClose);

  document.querySelector('.nd-help-btn').addEventListener('click', function () {
    window.ndClose();
    setTimeout(function () {
      if (window.WCHelp && window.WCHelp.openTab) {
        window.WCHelp.openTab('intro');
      }
    }, 200);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') window.ndClose();
  });
})();
