# NeuroScan — Face Analysis Backend

## Overview

FastAPI backend that accepts a face photo, runs MediaPipe facial landmark detection, applies a trained ML classifier, and returns a complete stroke risk report — including an annotated image, gauge chart, and downloadable 2-page clinical PDF.

All core logic is taken directly from **`Stroke_detection_V_08.ipynb`** to ensure results are identical to the research notebook.

---

## Research Foundation

### Why This Approach?

This system is grounded in the **FAST protocol** (Face, Arm, Speech, Time) — the internationally validated stroke screening tool. The **"F" (Face drooping)** component is the core of our detection system.

> *"Facial asymmetry is a key clinical indicator of stroke. However, human assessment is highly subjective — paramedics failed to detect facial weakness in 17% of stroke patients."*
> — Herpich et al., Frontiers in Neurology (2022)

### Reference Papers

| # | Authors | Title | Journal / Source | Link |
|---|---------|-------|------------------|------|
| 1 | Herpich et al. (2022) | Human vs. Machine Learning Based Detection of Facial Weakness Using Video Analysis | *Frontiers in Neurology* | [🔗 Link](https://www.frontiersin.org/journals/neurology/articles/10.3389/fneur.2022.878282/full) |
| 2 | Taufique & Savakis (2021) | Automatic Quantification of Facial Asymmetry Using Facial Landmarks | *arXiv:2103.11059* | [🔗 Link](https://arxiv.org/pdf/2103.11059) |
| 3 | Oliveira et al. (2023) | Facial Point Graphs for Stroke Identification | *ResearchGate* | [🔗 Link](https://www.researchgate.net/publication/375956719_Facial_Point_Graphs_for_Stroke_Identification) |
| 4 | Frontera et al. (2026) | Systematic Review of Facial Expression Recognition in Stroke | *Frontiers in Neurology* | [🔗 Link](https://www.frontiersin.org/journals/neurology/articles/10.3389/fneur.2026.1744257/full) |
| 5 | Baptista et al. (2022) | Systematic Review Comparing FAST and BE-FAST | *PMC8837419* | [🔗 Link](https://pmc.ncbi.nlm.nih.gov/articles/PMC8837419/) |

### Clinical Threshold Basis

| Feature | Clinical Reference | Threshold |
|---|---|---|
| Eye Asymmetry (Ptosis) | Ross et al. — Sunnybrook Facial Grading System | 0.12 |
| Mouth Corner Droop | Kothari et al. — Cincinnati Prehospital Stroke Scale (CPSS) | 0.10 |
| Eyebrow Height Difference | Ross et al. — Sunnybrook FGS | 0.08 |
| Nasolabial Fold Asymmetry | Taufique & Savakis (2021) | 0.10 |
| Facial Midline Deviation | Taufique & Savakis (2021) | 0.05 |
| Mouth Width Asymmetry | Kothari et al. — CPSS FAST | 0.10 |

---

## Training Data

### Why Synthetic Data?

The only publicly available stroke facial dataset is the **Toronto Neuroface (TNF)** dataset — which contains data from only **14 stroke patients** (Frontera et al., 2026). This is insufficient for training a reliable classifier.

Therefore, we generate a **clinically-inspired synthetic dataset (N = 3,000 samples)** based on:
- FAST protocol thresholds (Kothari et al., 1999)
- Asymmetry score equations (Taufique & Savakis, 2021)
- Sunnybrook Facial Grading System criteria (Ross et al., 1996)

The synthetic dataset uses:
- **1,500 normal samples** — Gaussian distribution within clinical thresholds
- **1,500 stroke samples** — Bimodal distribution (60% mild + 40% severe) for realistic variety

### Real-World Validation

Real-world images from the **Annotated Stroke and Non-Stroke Dataset** (Kaggle) are used **only for model selection** — to determine which trained model generalises best to actual clinical images (noise, lighting variation, angle).

> 📦 **Kaggle Dataset:** [Annotated Facial Images for Stroke Classification](https://www.kaggle.com/datasets/abdussalamelhanashy/annotated-facial-images-for-stroke-classification)
>
> 100 stroke images + 100 non-stroke images used for validation.

### Model Selection

Four models trained and compared on the real-world validation set (priority metric: **Recall** — minimise missed strokes):
- Logistic Regression
- Random Forest (300 estimators)
- Gradient Boosting (300 estimators)
- XGBoost (300 estimators)

The best-performing model is saved as `stroke_model.pkl`.

---

## Files

```
backend/
├── app.py                  — FastAPI main application
├── core/
│   ├── features.py         — extract_features() from notebook Section 2
│   ├── predictor.py        — predict_stroke_risk() from notebook Section 2
│   ├── annotator.py        — draw_annotated_image() from notebook Section 8 Cell 2
│   └── gauge.py            — draw_gauge() from notebook Section 8 Cell 3
├── generate_report.py      — 2-page PDF generator (notebook Section 10)
├── stroke_model.pkl        — trained ML classifier
├── stroke_scaler.pkl       — StandardScaler (must match training)
├── requirements.txt
└── README.md
```

---

## API

### `POST /analyze`

Accepts a face image, returns JSON with features, prediction, and file URLs.

**Headers:**
```
X-API-Key: your-api-key
Content-Type: multipart/form-data
```

**Body:** `file` — JPG / PNG / WEBP face photo

**Response:**
```json
{
  "success": true,
  "report_id": "NS-20260615-123456-abc123",
  "features": { "eye_asymmetry": 0.082, ... },
  "feature_flags": {
    "eye_asymmetry": { "value": 0.082, "threshold": 0.12, "status": "Normal", "flagged": false }
  },
  "prediction": {
    "probability": 0.1234, "percentage": 12.34,
    "label": 0, "risk_level": "LOW RISK", "color_hint": "green"
  },
  "annotated_image_url": "/results/NS-.../annotated.png",
  "gauge_image_url":     "/results/NS-.../gauge.png",
  "pdf_url":             "/results/NS-.../report.pdf"
}
```

### `GET /health`

Returns `{"status": "ok"}`.

---

## Setup & Run

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key (optional for local dev)
export NEUROSCAN_API_KEY="your-secret-key-here"

# Run locally
uvicorn app:app --reload --port 8000
```

### API Key Setup
The same API key is used by:
- **Website** — set as `NEUROSCAN_API_KEY` in frontend config
- **Telegram bot** — set as env variable in the bot process
- **WhatsApp bot** (future) — set as env variable

---

## Medical Disclaimer

> ⚠️ **NeuroScan is a SCREENING TOOL, not a diagnostic tool.**
>
> This system flags *potential* stroke risk from facial asymmetry only.
> It does NOT replace clinical diagnosis by a licensed medical professional.
> A positive result must prompt immediate medical consultation.
> False positives and false negatives are inherent to any screening tool.
>
> *"If you notice facial drooping, seek emergency medical help immediately."*
> — American Stroke Association (FAST protocol)
