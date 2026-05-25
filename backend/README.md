---
title: NeuroScan Backend API
emoji: 🧠
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# NeuroScan — Stroke Detection Backend

FastAPI backend that runs the trained ML model for secondary stroke risk validation.

## Endpoint

`POST /predict`

```json
{
  "mouth_asym": 0.42,
  "eye_asym":   0.18,
  "brow_asym":  0.0
}
```

Returns:
```json
{
  "prediction":  "stroke",
  "probability": 0.731,
  "confidence":  73.1
}
```

## Setup

Before deploying, copy these two files from the project root into this folder:
- `stroke_model.pkl`
- `stroke_scaler.pkl`

Generate them by running Steps 1–9 of `Stroke_detection.ipynb`.
