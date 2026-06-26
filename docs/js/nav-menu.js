/* WC2026 — Shared hamburger navigation drawer
   Fixes: safe-area insets (Dynamic Island / Home Bar), font consistency,
   touch-target size (≥44px per Apple HIG) */
(function () {
  var s = document.createElement('style');
  s.textContent = [
    /* Hide floating help button */
    '#wc-help-btn{display:none!important}',

    /* ── Hamburger trigger ─────────────────────────────────── */
    '.nd-hamburger{',
      'background:none;border:none;cursor:pointer;',
      'color:rgba(255,255,255,.8);font-size:1.2rem;line-height:1;',
      /* 44×44pt Apple minimum touch target */
      'min-width:44px;height:44px;',
      'display:flex;align-items:center;justify-content:center;',
      'border-radius:10px;transition:background .18s;',
      'flex-shrink:0;-webkit-tap-highlight-color:transparent;',
    '}',
    '.nd-hamburger:hover{background:rgba(255,255,255,.09);color:#fff}',
    '.nd-hamburger:active{background:rgba(255,255,255,.14)}',

    /* ── Dim overlay ───────────────────────────────────────── */
    '#nd-overlay{',
      'display:none;position:fixed;inset:0;z-index:1900;',
      'background:rgba(2,6,23,.7);backdrop-filter:blur(4px);',
      '-webkit-backdrop-filter:blur(4px);',
    '}',
    '#nd-overlay.open{display:block}',

    /* ── Drawer ────────────────────────────────────────────── */
    '#nd-drawer{',
      'position:fixed;top:0;left:0;bottom:0;z-index:1901;',
      'width:268px;max-width:84vw;',
      'background:#07091a;',
      'border-right:1px solid rgba(0,229,255,.12);',
      'display:flex;flex-direction:column;',
      'transform:translateX(-100%);',
      'transition:transform .28s cubic-bezier(.4,0,.2,1);',
      'box-shadow:6px 0 48px rgba(0,0,0,.75);',
      /* safe-area: top for Dynamic Island / notch */
      'padding-top:env(safe-area-inset-top);',
    '}',
    '#nd-drawer.open{transform:translateX(0)}',

    /* ── Drawer header ─────────────────────────────────────── */
    '.nd-hd{',
      'display:flex;align-items:center;gap:.6rem;',
      'padding:.9rem 1.1rem .8rem;',
      'border-bottom:1px solid rgba(255,255,255,.07);',
      'flex-shrink:0;',
    '}',
    '.nd-logo{',
      'flex:1;font-size:.82rem;font-weight:900;letter-spacing:2px;',
      'background:linear-gradient(90deg,#00E5FF,#FFD700);',
      '-webkit-background-clip:text;-webkit-text-fill-color:transparent;',
      /* Orbitron loaded on all pages */
      "font-family:'Orbitron',sans-serif;",
    '}',
    '.nd-close{',
      /* 44×44pt touch target */
      'min-width:44px;height:44px;',
      'display:flex;align-items:center;justify-content:center;',
      'background:rgba(255,255,255,.06);',
      'border:1px solid rgba(255,255,255,.1);',
      'border-radius:50%;',
      'color:rgba(255,255,255,.55);font-size:1rem;cursor:pointer;',
      'transition:background .18s;flex-shrink:0;',
      '-webkit-tap-highlight-color:transparent;',
    '}',
    '.nd-close:hover{background:rgba(255,255,255,.14);color:#fff}',
    '.nd-close:active{background:rgba(255,255,255,.2)}',

    /* ── Nav links ─────────────────────────────────────────── */
    '.nd-nav{flex:1;padding:.6rem .55rem;overflow-y:auto;-webkit-overflow-scrolling:touch;}',
    '.nd-a{',
      'display:flex;align-items:center;gap:.65rem;',
      /* min 44pt height per Apple HIG */
      'min-height:50px;',
      'padding:.55rem 1rem;border-radius:11px;',
      'color:rgba(255,255,255,.68);text-decoration:none;',
      /* Inter loaded on all pages, consistent across all */
      "font-family:'Inter',sans-serif;",
      'font-size:.88rem;font-weight:500;letter-spacing:.01em;',
      'transition:all .18s;border:1px solid transparent;',
      'margin-bottom:.12rem;',
      'background:none;width:100%;text-align:left;cursor:pointer;',
      '-webkit-tap-highlight-color:transparent;',
    '}',
    '.nd-a:hover{color:#fff;background:rgba(255,255,255,.07);border-color:rgba(255,255,255,.1)}',
    '.nd-a:active{background:rgba(255,255,255,.12)}',
    '.nd-a.nd-active{',
      'color:#00E5FF;',
      'background:rgba(0,229,255,.09);',
      'border-color:rgba(0,229,255,.22);',
      'font-weight:600;',
    '}',
    '.nd-a.nd-gold{color:#FFD700}',
    '.nd-a.nd-gold.nd-active{color:#FFD700;background:rgba(255,215,0,.08);border-color:rgba(255,215,0,.25)}',
    '.nd-a.nd-gold:hover{background:rgba(255,215,0,.07);border-color:rgba(255,215,0,.18)}',
    '.nd-sep{border:none;border-top:1px solid rgba(255,255,255,.07);margin:.45rem .3rem}',

    /* ── Drawer footer ─────────────────────────────────────── */
    '.nd-foot{',
      'padding:.65rem 1.1rem;',
      'border-top:1px solid rgba(255,255,255,.05);',
      'flex-shrink:0;text-align:center;',
      /* safe-area: bottom for Home Bar */
      'padding-bottom:max(.65rem, env(safe-area-inset-bottom));',
    '}',
  ].join('');
  document.head.appendChild(s);

  /* ── Inject HTML ─────────────────────────────────────────── */
  var overlay = document.createElement('div');
  overlay.id = 'nd-overlay';

  var drawer = document.createElement('aside');
  drawer.id = 'nd-drawer';
  drawer.setAttribute('role', 'dialog');
  drawer.setAttribute('aria-label', '導航選單');
  drawer.innerHTML =
    '<div class="nd-hd">'
    + '<span class="nd-logo">⚽ WC 2026 AI</span>'
    + '<button class="nd-close" id="nd-close-btn" aria-label="關閉">✕</button>'
    + '</div>'
    + '<nav class="nd-nav">'
    + '<a href="index.html"   class="nd-a nd-page-home">🏠&ensp;首頁</a>'
    + '<a href="groups.html"  class="nd-a nd-page-groups">📊&ensp;小組賽</a>'
    + '<a href="bracket.html" class="nd-a nd-page-bracket nd-gold">🏆&ensp;淘汰賽對陣表</a>'
    + '<a href="accuracy.html" class="nd-a nd-page-accuracy">🎯&ensp;預測準確度</a>'
    + '<hr class="nd-sep">'
    + '<button class="nd-a nd-help-btn">❓&ensp;使用說明</button>'
    + '</nav>'
    + '<div class="nd-foot">'
    + '<span style="font-size:.6rem;color:rgba(255,255,255,.22);letter-spacing:.08em;font-family:\'Inter\',sans-serif">AI WC2026 &nbsp;·&nbsp; 僅供參考</span>'
    + '</div>';

  document.body.insertBefore(drawer, document.body.firstChild);
  document.body.insertBefore(overlay, document.body.firstChild);

  /* ── Active page highlight ───────────────────────────────── */
  var path = window.location.pathname.split('/').pop() || 'index.html';
  var pageMap = {
    'index.html'   : '.nd-page-home',
    ''             : '.nd-page-home',
    'groups.html'  : '.nd-page-groups',
    'bracket.html' : '.nd-page-bracket',
    'accuracy.html': '.nd-page-accuracy',
  };
  var sel = pageMap[path];
  if (sel) {
    var el = document.querySelector(sel);
    if (el) el.classList.add('nd-active');
  }

  /* ── Open / close ────────────────────────────────────────── */
  window.ndOpen = function () {
    drawer.classList.add('open');
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  };
  window.ndClose = function () {
    drawer.classList.remove('open');
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  };

  overlay.addEventListener('click', window.ndClose);
  document.getElementById('nd-close-btn').addEventListener('click', window.ndClose);

  document.querySelector('.nd-help-btn').addEventListener('click', function () {
    window.ndClose();
    setTimeout(function () {
      if (window.WCHelp && window.WCHelp.openTab) {
        window.WCHelp.openTab('intro');
      }
    }, 220);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') window.ndClose();
  });
})();
