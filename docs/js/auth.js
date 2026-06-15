/* Password gate for non-index pages — SHA-256 verified */
(function () {
  'use strict';

  /* index.html is handled by the disclaimer flow in help.js */
  var path = window.location.pathname;
  if (/\/(index\.html)?$/.test(path) || path === '/') return;

  var HASH = 'e9adc021389854afa805943ff9900c72b7a0713128aaa593c29585098a2855b6';

  /* Already authenticated (remembered or this session) */
  try {
    if (localStorage.getItem('wc_auth_ok') === '1') return;
    if (sessionStorage.getItem('wc_auth_session') === '1') return;
  } catch (e) {}

  /* Hide body until authenticated */
  var lockStyle = document.createElement('style');
  lockStyle.id = 'wc-auth-lock';
  lockStyle.textContent = 'body{visibility:hidden!important}';
  document.head.appendChild(lockStyle);

  function sha256(str) {
    return crypto.subtle.digest('SHA-256', new TextEncoder().encode(str))
      .then(function (h) {
        return Array.from(new Uint8Array(h))
          .map(function (b) { return b.toString(16).padStart(2, '0'); })
          .join('');
      });
  }

  var CSS = [
    '#wc-auth-ov{position:fixed;inset:0;z-index:29000;',
    'background:linear-gradient(160deg,#020617 0%,#050d1f 60%,#080e1e 100%);',
    'display:flex;align-items:center;justify-content:center;padding:1.2rem;',
    'animation:wcAuthFade .4s ease}',
    '@keyframes wcAuthFade{from{opacity:0}to{opacity:1}}',
    '#wc-auth-box{width:100%;max-width:360px;',
    'background:rgba(8,14,30,.94);border:1px solid rgba(255,215,0,.2);',
    'border-radius:20px;overflow:hidden;position:relative;',
    'box-shadow:0 0 60px rgba(255,215,0,.07),0 32px 64px rgba(0,0,0,.9)}',
    '#wc-auth-box::before{content:"";position:absolute;top:0;left:15%;right:15%;height:1px;',
    'background:linear-gradient(90deg,transparent,rgba(255,215,0,.6),rgba(0,229,255,.4),transparent)}',
    '#wc-auth-top{padding:1.6rem 1.6rem 1rem;text-align:center}',
    '#wc-auth-logo{font-family:"Orbitron","Inter",sans-serif;font-size:1rem;font-weight:900;',
    'background:linear-gradient(90deg,#ffd700,#00e5ff);',
    '-webkit-background-clip:text;-webkit-text-fill-color:transparent;',
    'letter-spacing:2px;margin-bottom:.35rem}',
    '#wc-auth-sub{font-family:"Inter",sans-serif;font-size:.72rem;',
    'color:rgba(240,244,255,.35);letter-spacing:.5px}',
    '#wc-auth-form{padding:.4rem 1.6rem 1.6rem;display:flex;flex-direction:column;gap:.8rem}',
    '#wc-auth-label{font-family:"Orbitron","Inter",sans-serif;font-size:.62rem;',
    'letter-spacing:2px;color:rgba(255,215,0,.65);text-transform:uppercase}',
    '#wc-auth-wrap{position:relative}',
    '#wc-auth-input{width:100%;background:rgba(255,255,255,.05);',
    'border:1px solid rgba(255,255,255,.12);color:rgba(255,255,255,.92);',
    'font-family:"Inter",sans-serif;font-size:.95rem;letter-spacing:4px;',
    'padding:.72rem 2.8rem .72rem 1rem;border-radius:11px;outline:none;',
    'transition:border-color .2s;-webkit-appearance:none;caret-color:#ffd700}',
    '#wc-auth-input:focus{border-color:rgba(255,215,0,.5)}',
    '#wc-auth-input.wc-shake{border-color:rgba(255,51,102,.65);animation:wcShakeA .35s ease}',
    '@keyframes wcShakeA{0%,100%{transform:translateX(0)}25%{transform:translateX(-6px)}75%{transform:translateX(6px)}}',
    '#wc-auth-eye{position:absolute;right:.8rem;top:50%;transform:translateY(-50%);',
    'background:none;border:none;cursor:pointer;color:rgba(255,255,255,.3);font-size:.95rem;',
    'padding:.15rem;line-height:1;transition:color .2s;-webkit-tap-highlight-color:transparent}',
    '#wc-auth-eye:hover{color:rgba(255,255,255,.65)}',
    '#wc-auth-err{font-size:.73rem;color:#ff3366;min-height:.95rem;text-align:center;',
    'font-family:"Inter",sans-serif}',
    '#wc-auth-remember-wrap{display:flex;align-items:center;gap:.6rem;cursor:pointer;',
    'user-select:none;-webkit-user-select:none}',
    '#wc-auth-remember{width:18px;height:18px;accent-color:#ffd700;cursor:pointer;flex-shrink:0}',
    '#wc-auth-remember-text{font-size:.79rem;color:rgba(240,244,255,.5);font-family:"Inter",sans-serif}',
    '#wc-auth-btn{width:100%;padding:.72rem;',
    'background:linear-gradient(135deg,rgba(255,215,0,.17),rgba(0,229,255,.09));',
    'border:1px solid rgba(255,215,0,.38);color:#ffd700;border-radius:12px;',
    'font-family:"Orbitron","Inter",sans-serif;font-size:.72rem;font-weight:900;',
    'letter-spacing:1.2px;cursor:pointer;transition:all .2s;-webkit-tap-highlight-color:transparent}',
    '#wc-auth-btn:hover{background:rgba(255,215,0,.26);border-color:rgba(255,215,0,.7)}',
    '#wc-auth-btn:active{transform:scale(.97)}',
    '#wc-auth-btn:disabled{opacity:.4;cursor:not-allowed}',
  ].join('');

  function build() {
    var styleEl = document.createElement('style');
    styleEl.textContent = CSS;
    document.head.appendChild(styleEl);

    var ov = document.createElement('div');
    ov.id = 'wc-auth-ov';
    ov.innerHTML = '<div id="wc-auth-box">'
      + '<div id="wc-auth-top">'
      +   '<div id="wc-auth-logo">⚽ WC2026 PREDICTOR</div>'
      +   '<div id="wc-auth-sub">請輸入密碼以繼續</div>'
      + '</div>'
      + '<div id="wc-auth-form">'
      +   '<label id="wc-auth-label" for="wc-auth-input">密碼</label>'
      +   '<div id="wc-auth-wrap">'
      +     '<input id="wc-auth-input" type="password" autocomplete="current-password" placeholder="••••••••" spellcheck="false">'
      +     '<button id="wc-auth-eye" type="button" aria-label="顯示密碼">👁</button>'
      +   '</div>'
      +   '<div id="wc-auth-err"></div>'
      +   '<label id="wc-auth-remember-wrap" for="wc-auth-remember">'
      +     '<input type="checkbox" id="wc-auth-remember" checked>'
      +     '<span id="wc-auth-remember-text">記住密碼（下次免輸入）</span>'
      +   '</label>'
      +   '<button id="wc-auth-btn" type="button">進入 →</button>'
      + '</div>'
      + '</div>';

    document.body.insertBefore(ov, document.body.firstChild);
    document.body.style.visibility = 'visible';

    var lockEl = document.getElementById('wc-auth-lock');
    if (lockEl) lockEl.remove();

    var inp    = document.getElementById('wc-auth-input');
    var btn    = document.getElementById('wc-auth-btn');
    var eye    = document.getElementById('wc-auth-eye');
    var errEl  = document.getElementById('wc-auth-err');
    var remCb  = document.getElementById('wc-auth-remember');

    inp.focus();

    eye.addEventListener('click', function () {
      inp.type = inp.type === 'password' ? 'text' : 'password';
      eye.textContent = inp.type === 'password' ? '👁' : '🙈';
    });

    inp.addEventListener('keydown', function (e) {
      errEl.textContent = '';
      if (e.key === 'Enter') attempt();
    });
    btn.addEventListener('click', attempt);

    function attempt() {
      var val = inp.value;
      if (!val) { showErr('請輸入密碼'); return; }
      btn.disabled = true;
      sha256(val).then(function (digest) {
        if (digest === HASH) {
          try { sessionStorage.setItem('wc_auth_session', '1'); } catch (e) {}
          if (remCb.checked) { try { localStorage.setItem('wc_auth_ok', '1'); } catch (e) {} }
          ov.style.transition = 'opacity .35s';
          ov.style.opacity = '0';
          setTimeout(function () { ov.remove(); }, 340);
        } else {
          showErr('密碼錯誤，請重試');
          btn.disabled = false;
          inp.value = ''; inp.focus();
        }
      }).catch(function () {
        showErr('驗證失敗，請重新整理頁面');
        btn.disabled = false;
      });
    }

    function showErr(msg) {
      errEl.textContent = msg;
      inp.classList.remove('wc-shake');
      void inp.offsetWidth;
      inp.classList.add('wc-shake');
      setTimeout(function () { inp.classList.remove('wc-shake'); }, 380);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }
})();
