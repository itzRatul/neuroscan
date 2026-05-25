/* ============================================================
   NeuroScan — Shared navbar + footer injector
   Included by every page. Marks active link based on URL.
============================================================ */

(function () {
  const PAGES = {
    home:     { href: 'index.html',         label: 'Home' },
    how:      { href: 'how-it-works.html',  label: 'How it works' },
    tech:     { href: 'technology.html',    label: 'Technology' },
    protocol: { href: 'protocol.html',      label: 'Protocol' },
    scoring:  { href: 'scoring.html',       label: 'Scoring' },
    datasets: { href: 'datasets.html',      label: 'Datasets' },
    refs:     { href: 'references.html',    label: 'References' },
    test:     { href: 'test.html',          label: 'Start Test' },
  };

  // ---------- Lucide-style inline SVG icons ----------
  const ICONS = {
    logo: `<svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M16 3c-5 0-9 4-9 9 0 2 .8 4 2 5.5L8 25l4-2 1 4 4-3 4 3 1-4 4 2-1-7.5c1.2-1.5 2-3.5 2-5.5 0-5-4-9-9-9z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/>
      <circle cx="13" cy="12" r="1.2" fill="currentColor"/>
      <circle cx="19" cy="12" r="1.2" fill="currentColor"/>
    </svg>`,
    chevron: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>`,
    arrow:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7h10v10"/><path d="M7 17 17 7"/></svg>`,
    menu:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16"/><path d="M4 12h16"/><path d="M4 19h16"/></svg>`,
    close:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>`,
    brain:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 18V5"/><path d="M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"/><path d="M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"/><path d="M17.997 5.125a4 4 0 0 1 2.526 5.77"/><path d="M18 18a4 4 0 0 0 2-7.464"/><path d="M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"/><path d="M6 18a4 4 0 0 1-2-7.464"/><path d="M6.003 5.125a4 4 0 0 0-2.526 5.77"/></svg>`,
    eye:     `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>`,
    activity:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/></svg>`,
    cpu:     `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20v2"/><path d="M12 2v2"/><path d="M17 20v2"/><path d="M17 2v2"/><path d="M2 12h2"/><path d="M2 17h2"/><path d="M2 7h2"/><path d="M20 12h2"/><path d="M20 17h2"/><path d="M20 7h2"/><path d="M7 20v2"/><path d="M7 2v2"/><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="8" y="8" width="8" height="8" rx="1"/></svg>`,
    clipboard:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/></svg>`,
    target:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>`,
    database:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/></svg>`,
    book:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>`,
    camera:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>`,
  };

  // ---------- Build header ----------
  function buildHeader() {
    return `
      <header class="navbar">
        <div class="nav-inner">
          <a href="index.html" class="brand">
            ${ICONS.logo}
            <span class="brand-text">
              <span class="brand-name">NeuroScan</span>
              <span class="brand-tag">Stroke screening · MediaPipe</span>
            </span>
          </a>

          <nav class="nav-links" aria-label="Main navigation">
            <a class="nav-link" data-page="home" href="index.html">Home</a>

            <div class="nav-dropdown">
              <span class="nav-trigger" data-group="learn">Learn ${ICONS.chevron}</span>
              <div class="nav-menu" data-menu="learn">
                <a data-page="how"      href="how-it-works.html">${ICONS.activity} How it works</a>
                <a data-page="tech"     href="technology.html">${ICONS.cpu} Technology</a>
                <a data-page="protocol" href="protocol.html">${ICONS.clipboard} Protocol</a>
                <a data-page="scoring"  href="scoring.html">${ICONS.target} Scoring</a>
              </div>
            </div>

            <div class="nav-dropdown">
              <span class="nav-trigger" data-group="research">Research ${ICONS.chevron}</span>
              <div class="nav-menu" data-menu="research">
                <a data-page="datasets" href="datasets.html">${ICONS.database} Datasets</a>
                <a data-page="refs"     href="references.html">${ICONS.book} References</a>
              </div>
            </div>
          </nav>

          <a class="nav-cta" data-page="test" href="test.html">
            ${ICONS.camera} Start Test ${ICONS.arrow}
          </a>

          <button class="mobile-toggle" aria-label="Toggle menu" id="mobileToggle">
            ${ICONS.menu}
          </button>
        </div>

        <div class="mobile-menu" id="mobileMenu">
          <a data-page="home"     href="index.html">Home</a>
          <div class="mobile-section-label">Learn</div>
          <a data-page="how"      href="how-it-works.html">How it works</a>
          <a data-page="tech"     href="technology.html">Technology</a>
          <a data-page="protocol" href="protocol.html">Protocol</a>
          <a data-page="scoring"  href="scoring.html">Scoring</a>
          <div class="mobile-section-label">Research</div>
          <a data-page="datasets" href="datasets.html">Datasets</a>
          <a data-page="refs"     href="references.html">References</a>
          <div class="mobile-section-label">Get started</div>
          <a data-page="test"     href="test.html" class="mobile-cta">Start the test →</a>
        </div>
      </header>
    `;
  }

  // ---------- Build footer ----------
  function buildFooter() {
    const year = new Date().getFullYear();
    return `
      <footer class="footer">
        <div class="container">
          <div>
            <div class="footer-brand">
              ${ICONS.logo}
              <strong>NeuroScan</strong>
            </div>
            <p class="footer-about">
              Browser-based facial-asymmetry stroke screening built on Google MediaPipe.
              100% on-device — no data ever leaves your browser.
            </p>
          </div>

          <div>
            <h4>Learn</h4>
            <ul>
              <li><a href="how-it-works.html">How it works</a></li>
              <li><a href="technology.html">Technology</a></li>
              <li><a href="protocol.html">Test protocol</a></li>
              <li><a href="scoring.html">Scoring</a></li>
            </ul>
          </div>

          <div>
            <h4>Research</h4>
            <ul>
              <li><a href="datasets.html">Training datasets</a></li>
              <li><a href="references.html">References</a></li>
              <li><a href="https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker" target="_blank" rel="noopener">MediaPipe docs</a></li>
            </ul>
          </div>

          <div>
            <h4>Get started</h4>
            <ul>
              <li><a href="test.html">Run the test</a></li>
              <li><a href="index.html">Home</a></li>
            </ul>
          </div>
        </div>

        <div class="footer-bottom">
          <strong>NeuroScan</strong> &middot; Not a clinical diagnosis · For early-warning screening only ·
          &copy; ${year}
        </div>
      </footer>
    `;
  }

  // ---------- Mark active link ----------
  function markActive() {
    const path = (window.location.pathname.split('/').pop() || 'index.html').toLowerCase();
    const key = Object.entries(PAGES).find(([, p]) => p.href === path)?.[0];
    if (!key) return;
    document.querySelectorAll(`[data-page="${key}"]`).forEach((el) => el.classList.add('active'));
  }

  // ---------- Mobile toggle ----------
  function wireMobile() {
    const btn = document.getElementById('mobileToggle');
    const menu = document.getElementById('mobileMenu');
    if (!btn || !menu) return;
    btn.addEventListener('click', () => {
      menu.classList.toggle('open');
      btn.innerHTML = menu.classList.contains('open') ? ICONS.close : ICONS.menu;
    });
  }

  // ---------- Dropdown click for touch devices ----------
  function wireDropdowns() {
    document.querySelectorAll('.nav-dropdown').forEach((dd) => {
      const trigger = dd.querySelector('.nav-trigger');
      trigger?.addEventListener('click', (e) => {
        e.stopPropagation();
        document.querySelectorAll('.nav-dropdown.open').forEach((other) => {
          if (other !== dd) other.classList.remove('open');
        });
        dd.classList.toggle('open');
      });
    });
    document.addEventListener('click', () => {
      document.querySelectorAll('.nav-dropdown.open').forEach((dd) => dd.classList.remove('open'));
    });
  }

  // ---------- Inject ----------
  function inject() {
    const headerSlot = document.getElementById('site-header');
    const footerSlot = document.getElementById('site-footer');
    if (headerSlot) headerSlot.innerHTML = buildHeader();
    if (footerSlot) footerSlot.innerHTML = buildFooter();
    markActive();
    wireMobile();
    wireDropdowns();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inject);
  } else {
    inject();
  }
})();
