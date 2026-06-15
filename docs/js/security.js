(function () {
  'use strict';

  /* ── 1. Headless / bot detection ──────────────────────────────────────── */
  var botChecks = [
    function () { return navigator.webdriver === true; },
    function () { return /HeadlessChrome|HeadlessFirefox/.test(navigator.userAgent); },
    function () { return /PhantomJS/.test(navigator.userAgent); },
    function () { return typeof window.callPhantom !== 'undefined'; },
    function () { return typeof window._phantom !== 'undefined'; },
    function () { return typeof window.__nightmare !== 'undefined'; },
    function () { return document.documentElement.getAttribute('webdriver') !== null; },
  ];

  var isBot = botChecks.some(function (fn) {
    try { return fn(); } catch (e) { return false; }
  });

  if (isBot) {
    document.addEventListener('DOMContentLoaded', function () {
      var b = document.createElement('div');
      b.style.cssText = [
        'position:fixed;top:0;left:0;right:0;z-index:2147483647',
        'background:#ff3366;color:#fff;text-align:center',
        'padding:14px 16px;font-family:sans-serif;font-size:14px;font-weight:600',
        'letter-spacing:.5px;box-shadow:0 2px 12px rgba(0,0,0,.5)',
      ].join(';');
      b.textContent = '⚠️ Automated access detected. This site is for human visitors only.';
      document.body.insertBefore(b, document.body.firstChild);
    });
  }

  /* ── 2. Basic click-jacking guard (redundant with CSP but belt+braces) ── */
  if (window.self !== window.top) {
    document.addEventListener('DOMContentLoaded', function () {
      document.body.style.display = 'none';
    });
  }

  /* ── 3. Disable context-menu on elements marked [data-no-copy] ─────────── */
  document.addEventListener('contextmenu', function (e) {
    if (e.target && e.target.closest && e.target.closest('[data-no-copy]')) {
      e.preventDefault();
    }
  });

  /* ── 4. Very simple honeypot timing — flag suspiciously rapid navigation ── */
  var _t0 = Date.now();
  window.addEventListener('beforeunload', function () {
    if (Date.now() - _t0 < 300) {
      /* Page left in <300 ms — likely a scraper; nothing actionable on
         a static site but keeps the pattern available for future logging. */
    }
  });

})();
