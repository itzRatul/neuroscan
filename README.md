# 🧠 NeuroScan — AI-Powered Stroke Early-Warning Tool

A real-time stroke early-warning system that detects **facial movement asymmetry** using a webcam — no wearable or medical device required. Runs entirely in the browser; no data ever leaves your device.

---

## Medical Basis

Stroke causes sudden weakness on one side of the body, including the face. The **FAST** acronym is the standard pre-hospital stroke screening tool used worldwide:

| Letter | Sign | NeuroScan |
|--------|------|-----------|
| **F** | Face drooping | ✅ Detected via facial asymmetry |
| **A** | Arm weakness | 🔜 Planned |
| **S** | Speech difficulty | — |
| **T** | Time to call emergency | ✅ Timestamp on alert |

This project automates the **F (Face)** component of the FAST scale using computer vision.

---

## 🌐 Live Demo

| Service | URL |
|---|---|
| **Web App** | [neuroscan-diu.vercel.app](https://neuroscan-diu.vercel.app) |
| **Backend API** | [itzratul-neuroscan-backend.hf.space](https://itzratul-neuroscan-backend.hf.space) |

---

## How It Works

The system uses a **guided 5-phase test** that measures *movement asymmetry* rather than static facial asymmetry.

### Why movement asymmetry?

Static baseline calibration has a critical flaw for active stroke detection: if a person is already having a stroke at the time of the test, their resting face is already asymmetric — so the "normal" baseline is contaminated. Comparing a stroke face against a stroke baseline produces a near-zero delta, causing the system to falsely report **NORMAL**.

Movement asymmetry solves this. It measures how much each side of the face *responds* to a command. A stroke-affected side will fail to move even when the person tries — and this failure is detectable regardless of what the resting baseline looks like.

---

## Guided Test Protocol

| Phase | Duration | Instruction | What is measured |
|-------|----------|-------------|-----------------|
| REST | 4 s | Keep face normal | Landmark positions at rest (reference frame) |
| SMILE #1 | 3 s | Smile now | Upward pixel delta of each mouth corner vs rest |
| CLOSE EYES | 3 s | Close your eyes | Closure ratio of each eye relative to rest opening |
| OPEN EYES | 3 s | Open eyes wide | How much each eye opened wider vs rest |
| SMILE #2 | 3 s | Smile again | Confirmation smile for averaging |

**Scoring formula:**

```
Movement Score = (smile_asymmetry  × 0.50)
               + (eye_close_asymmetry × 0.25)
               + (eye_open_asymmetry  × 0.25)

Score × 100  →  0–100 scale

Score > 60  →  HIGH RISK  (red)
Score > 30  →  MODERATE   (orange)
Score ≤ 30  →  NORMAL     (green)
```

**Smile asymmetry example:**
```
Left corner moved up  12 px
Right corner moved up  2 px   ← affected side barely moved
Asymmetry ratio = |12 - 2| / 12 = 0.83  →  HIGH RISK
```

---

## Datasets Used

Two publicly available Kaggle datasets provide labeled facial images for ML model training:

| # | Dataset | Kaggle Link | Contents |
|---|---------|-------------|---------|
| 1 | Annotated Facial Images for Stroke Classification | [Link](https://www.kaggle.com/datasets/abdussalamelhanashy/annotated-facial-images-for-stroke-classification) | 2,490 stroke + 5,000 normal face images |
| 2 | Facial Droop and Facial Paralysis Images | [Link](https://www.kaggle.com/datasets/kaitavmehta/facial-droop-and-facial-paralysis-image) | 1,024 droopy/paralysis face images |

**Why these datasets?**
Stroke causes **facial palsy** — sudden drooping and weakness on one side of the face. Both datasets contain labeled examples of exactly that presentation, which is clinically validated by the **Cincinnati Prehospital Stroke Scale** (Kothari et al., 1999).

**ML Training Pipeline:**

```
Kaggle Images → MediaPipe Feature Extraction (4 features/image)
                          ↓
                80/20 Train/Test Split
                          ↓
    Logistic Regression | SVM | Random Forest
                          ↓
         Best model saved → stroke_model.pkl
```

> **Note:** The trained ML model (`stroke_model.pkl`) is used as a supplementary reference. The primary detection method is the guided movement asymmetry test, which does not rely on the ML model's absolute thresholds and is therefore robust for both first-time stroke and stroke-survivor screening.

---

## Landmark Indices Used

MediaPipe Face Landmarker provides 468 fixed landmarks on the face. The indices used in this project:

| Variable | Index | Location |
|----------|-------|----------|
| `MOUTH_LEFT` | 61 | Left mouth corner |
| `MOUTH_RIGHT` | 291 | Right mouth corner |
| `LEFT_EYE_TOP` | 159 | Left upper eyelid |
| `LEFT_EYE_BOTTOM` | 145 | Left lower eyelid |
| `RIGHT_EYE_TOP` | 386 | Right upper eyelid |
| `RIGHT_EYE_BOTTOM` | 374 | Right lower eyelid |
| `LEFT_EYEBROW` | 105 | Left eyebrow center |
| `RIGHT_EYEBROW` | 334 | Right eyebrow center |
| `NOSE_TIP` | 1 | Nose tip (center reference) |

---

## 🏗️ Project Structure

```
neuroscan/
├── webapp/                   # Static frontend (HTML/CSS/JS)
│   ├── index.html            # Landing page
│   ├── test.html             # Main screening interface
│   ├── how-it-works.html
│   ├── technology.html
│   ├── protocol.html
│   ├── scoring.html
│   ├── datasets.html
│   ├── references.html
│   ├── vercel.json           # COOP/COEP headers for Vercel
│   └── assets/
│       ├── app.js            # Core test logic (MediaPipe + scoring)
│       ├── nav.js            # Navigation injection
│       └── style.css         # Design system
│
└── backend/                  # Optional FastAPI ML backend
    ├── app.py                # /predict endpoint
    ├── stroke_model.pkl      # Pre-trained scikit-learn classifier
    ├── stroke_scaler.pkl     # StandardScaler
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

> **Note:** HTTPS is required on non-localhost — webcam access is blocked on plain HTTP.

### Run the backend locally

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7860
# API at http://localhost:7860
```

### Run with Docker

```bash
cd backend
docker build -t neuroscan-backend .
docker run -p 7860:7860 neuroscan-backend
```

---

## 🤖 Backend API

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

## 🛠️ Built With

| Layer | Technology |
|---|---|
| Face detection | [MediaPipe Face Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker) v0.10.9 |
| Charts | [Chart.js](https://www.chartjs.org/) |
| PDF export | [jsPDF](https://github.com/parallax/jsPDF) + [html2canvas](https://html2canvas.hertzen.com/) |
| Voice guidance | Web Speech API |
| ML backend | [FastAPI](https://fastapi.tiangolo.com/) + [scikit-learn](https://scikit-learn.org/) |
| Frontend deploy | [Vercel](https://vercel.com/) |
| Backend deploy | [Hugging Face Spaces](https://huggingface.co/spaces) |

---

## ⚠️ Disclaimer

This tool is **not a clinical diagnosis system**. It is an early-warning prototype intended to prompt the user to seek immediate medical attention. Always call emergency services if stroke symptoms are suspected.

---

## References

1. **Kothari, R. U., et al. (1999)**
   *Cincinnati Prehospital Stroke Scale: reproducibility and validity.*
   Annals of Emergency Medicine, 33(4), 373–378.
   https://doi.org/10.1016/S0196-0644(99)70299-4

2. **Luzniak, M., et al. (2021)**
   *Automated facial asymmetry analysis in stroke screening.*
   Journal of Stroke and Cerebrovascular Diseases.

3. **Google MediaPipe Face Mesh**
   *Face Landmark Detection — MediaPipe Solutions.*
   https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker

4. **Hochberg, G., et al. (2019)**
   *FAST and FASTER: A Systematic Review of Stroke Screening Tools.*
   Stroke, 50(9), 2572–2582.

---

## 📄 License

[MIT License](LICENSE) © 2025 itzRatul
