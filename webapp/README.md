# NeuroScan — Stroke Detection Web App

Browser-based stroke early-warning screening using **MediaPipe Face Mesh**, **Web Speech API**, **Chart.js**, and **jsPDF**.

100% client-side — no server, no backend, no data leaves the user's browser.

---

## Features

- Real-time 468-landmark face tracking (MediaPipe Tasks Vision)
- Five-phase guided test: REST → SMILE → EYES CLOSE → EYES OPEN → SMILE AGAIN
- Action-triggered timing (no premature countdowns)
- Voice guidance via Web Speech API
- Movement asymmetry scoring (immune to baseline contamination)
- Interactive charts: bar (per-phase), doughnut (score composition), grouped bar (left vs right)
- Downloadable PDF report

---

## Quick start (local)

ES modules need to be served over HTTP — opening `index.html` directly will not work.

```bash
cd webapp
python3 -m http.server 8000
```

Then open: **http://localhost:8000**

---

## Deploy (free hosting)

The whole app is three static files. Any static host works:

- **GitHub Pages** — push `webapp/` to a `gh-pages` branch
- **Netlify / Vercel** — drag-and-drop the `webapp/` folder
- **Cloudflare Pages** — connect a repo, build command empty, publish dir `webapp`

No environment variables, no build step.

---

## Browser support

| Browser            | Webcam | MediaPipe | Speech |
|--------------------|--------|-----------|--------|
| Chrome / Edge (desktop + Android) | ✅ | ✅ | ✅ |
| Firefox            | ✅ | ✅ | ⚠️ (limited voices) |
| Safari (iOS 14.5+) | ✅ | ✅ | ✅ |

HTTPS is required for camera access on any non-localhost domain.

---

## File map

```
webapp/
├── index.html   # markup (landing / test / results screens)
├── style.css    # all styling
├── app.js       # MediaPipe, voice, state machine, charts, PDF
└── README.md
```
