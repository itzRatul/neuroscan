/* ============================================================
   NeuroScan — Shared navbar + footer injector
   Included by every page. Marks active link based on URL.
============================================================ */

(function () {
  const PAGES = {
    home:      { href: 'index.html',         label: 'Home' },
    photoscan: { href: 'photo-scan.html',    label: 'Photo Scan' },
    chat:      { href: 'ai-chat.html',       label: 'AI Chat' },
    research:  { href: 'research.html',      label: 'Research & Learn' },
    test:      { href: 'test.html',          label: 'Start Test' },
  };

  // ---------- Lucide-style inline SVG icons ----------
  const ICONS = {
    logo: `<svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M16 3c-5 0-9 4-9 9 0 2 .8 4 2 5.5L8 25l4-2 1 4 4-3 4 3 1-4 4 2-1-7.5c1.2-1.5 2-3.5 2-5.5 0-5-4-9-9-9z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/>
      <circle cx="13" cy="12" r="1.2" fill="currentColor"/>
      <circle cx="19" cy="12" r="1.2" fill="currentColor"/>
    </svg>`,
    arrow:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7h10v10"/><path d="M7 17 17 7"/></svg>`,
    menu:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16"/><path d="M4 12h16"/><path d="M4 19h16"/></svg>`,
    close:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>`,
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
            <a class="nav-link" data-page="photoscan" href="photo-scan.html">Photo Scan</a>
            <a class="nav-link" data-page="chat" href="ai-chat.html">AI Chat</a>
            <a class="nav-link" data-page="research" href="research.html">Research &amp; Learn</a>
          </nav>

          <a class="nav-cta" data-page="test" href="test.html">
            ${ICONS.camera} Start Test ${ICONS.arrow}
          </a>

          <button class="mobile-toggle" aria-label="Toggle menu" id="mobileToggle">
            ${ICONS.menu}
          </button>
        </div>

        <div class="mobile-menu" id="mobileMenu">
          <a data-page="home"      href="index.html">Home</a>
          <a data-page="photoscan" href="photo-scan.html">Photo Scan</a>
          <a data-page="chat"      href="ai-chat.html">AI Chat</a>
          <a data-page="research"  href="research.html">Research &amp; Learn</a>
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
              Runs on synthetic data training and real-world Kaggle testing.
            </p>
          </div>

          <div>
            <h4>Learn &amp; Research</h4>
            <ul>
              <li><a href="research.html">Methodology</a></li>
              <li><a href="research.html">Test protocol</a></li>
              <li><a href="research.html">Publications timeline</a></li>
              <li><a href="research.html">Training datasets</a></li>
            </ul>
          </div>

          <div>
            <h4>Resources</h4>
            <ul>
              <li><a href="https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker" target="_blank" rel="noopener">MediaPipe docs</a></li>
              <li><a href="https://www.kaggle.com/datasets/abdussalamelhanashy/annotated-facial-images-for-stroke-classification" target="_blank" rel="noopener">Kaggle Stroke Dataset</a></li>
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

  // ---------- Inject ----------
  function inject() {
    const headerSlot = document.getElementById('site-header');
    const footerSlot = document.getElementById('site-footer');
    if (headerSlot) headerSlot.innerHTML = buildHeader();
    if (footerSlot) footerSlot.innerHTML = buildFooter();
    markActive();
    wireMobile();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inject);
  } else {
    inject();
  }
})();
