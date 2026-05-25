# 🧠 NeuroScan — AI-Powered Stroke Screening Tool

NeuroScan is a browser-based stroke early-warning tool that detects **facial movement asymmetry** — the strongest clinical indicator of acute stroke — using your device's webcam. No app installation required. All processing happens locally in your browser; no data is ever sent to a server.

> Built on the **Cincinnati Prehospital Stroke Scale (CPSS)** — Kothari et al., 1999.

---

## 🌐 Live Demo

| Service | URL |
|---|---|
| **Web App** | [neuroscan.vercel.app](https://neuroscan.vercel.app) |
| **Backend API** | [itzratul-neuroscan-backend.hf.space](https://itzratul-neuroscan-backend.hf.space) |

---

## ✨ Features

- **Real-time face tracking** — MediaPipe Face Landmarker (468 landmarks, 30 FPS, <30ms latency)
- **5-phase guided test** — Rest → Smile → Close eyes → Open eyes → Confirm smile
- **Movement asymmetry scoring** — measures how each side *responds* to commands, not resting appearance
- **Voice guidance** — Web Speech API directs the user through each phase
- **Instant risk verdict** — HIGH / MODERATE / NORMAL with score breakdown
- **PDF report download** — shareable clinical summary
- **ML secondary validation** — optional FastAPI backend with scikit-learn classifier
- **100% private** — zero data leaves your device

---

## 🏗️ Project Structure

```
neuroscan/
├── webapp/               # Static frontend (HTML/CSS/JS)
│   ├── index.html        # Landing page
│   ├── test.html         # Main screening interface
│   ├── assets/
│   │   ├── app.js        # Core test logic (MediaPipe + scoring)
│   │   ├── nav.js        # Navigation injection
│   │   └── style.css     # Design system
│   └── vercel.json       # COOP/COEP headers for Vercel
│
└── backend/              # Optional FastAPI ML backend
    ├── app.py            # /predict endpoint
    ├── stroke_model.pkl  # Pre-trained scikit-learn classifier
    ├── stroke_scaler.pkl # StandardScaler
    ├── requirements.txt
    └── Dockerfile
```

---

## 🚀 Quick Start

### Run the webapp locally

```bash
cd webapp
python3 -m http.server 8000
# Open http://localhost:8000
```

> **HTTPS required** on non-localhost — webcam access is blocked on plain HTTP.

### Run the backend locally

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7860
# API available at http://localhost:7860
```

### Run with Docker

```bash
cd backend
docker build -t neuroscan-backend .
docker run -p 7860:7860 neuroscan-backend
```

---

## 🧪 How It Works

### 5-Phase Test Protocol

| Phase | Action | Duration |
|---|---|---|
| 0 — REST | Neutral face (baseline) | 4 sec |
| 1 — SMILE #1 | Smile and hold | 3 sec |
| 2 — CLOSE EYES | Close both eyes | 3 sec |
| 3 — OPEN EYES | Open eyes wide | 3 sec |
| 4 — SMILE #2 | Confirmation smile | 3 sec |

### Scoring Formula

```
Score = (smile_asymmetry × 0.50) + (eye_close_asymmetry × 0.25) + (eye_open_asymmetry × 0.25)
Final = min(Score × 100, 100)
```

| Score | Verdict |
|---|---|
| > 60 | 🔴 HIGH RISK — Seek emergency services |
| 30–60 | 🟡 MODERATE — Consult a doctor |
| < 30 | 🟢 NORMAL |

---

## 🤖 ML Backend API

### `POST /predict`

```json
{
  "mouth_asym": 0.42,
  "eye_asym": 0.18,
  "brow_asym": 0.0
}
```

**Response:**
```json
{
  "prediction": "stroke",
  "probability": 0.731,
  "confidence": 73.1
}
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Face detection | MediaPipe Face Landmarker v0.10.9 |
| Charts | Chart.js |
| PDF export | jsPDF + html2canvas |
| Voice | Web Speech API |
| Backend | FastAPI + scikit-learn |
| Deployment | Vercel (webapp) + Hugging Face Spaces (backend) |

---

## 📊 Training Data

- **7,490 images** — 2,490 stroke cases + 5,000 normal controls
- Source: Kaggle facial asymmetry datasets
- Labels: unilateral facial droop, asymmetric smile, eyelid weakness

---

## 📚 Clinical Reference

> Kothari RU, et al. *"Cincinnati Prehospital Stroke Scale: reproducibility and validity."* Annals of Emergency Medicine, 1999.

---

## ⚠️ Disclaimer

NeuroScan is a **screening aid only** — not a medical diagnostic tool. A high-risk result does not confirm a stroke. Always contact emergency services if stroke is suspected.

---

## 📄 License

[MIT License](LICENSE) © 2025 itzRatul
