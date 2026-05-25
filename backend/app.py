from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import numpy as np
import os

app = FastAPI(title="NeuroScan Stroke Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Load model at startup
if not os.path.exists("stroke_model.pkl") or not os.path.exists("stroke_scaler.pkl"):
    raise RuntimeError(
        "stroke_model.pkl or stroke_scaler.pkl not found. "
        "Run the Jupyter notebook (Steps 1–9) first to generate these files."
    )

model  = joblib.load("stroke_model.pkl")
scaler = joblib.load("stroke_scaler.pkl")


class Features(BaseModel):
    # Webapp sends these three values after the guided test
    mouth_asym: float   # smile asymmetry  (0–1)
    eye_asym:   float   # eye asymmetry    (0–1)
    brow_asym:  float = 0.0  # not measured in webapp, defaults to 0


@app.get("/")
def root():
    return {"status": "ok", "service": "NeuroScan Stroke Detection API"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(f: Features):
    # Kothari 1999: facial droop = most sensitive CPSS sign → 50%; eye signs (CN VII palsy) → 40%; brow not in CPSS → 10%
    risk_score = min((f.mouth_asym * 0.5 + f.eye_asym * 0.4 + f.brow_asym * 0.1) * 100, 100)

    X        = np.array([[f.mouth_asym, f.eye_asym, f.brow_asym, risk_score]])
    X_scaled = scaler.transform(X)

    prob  = float(model.predict_proba(X_scaled)[0][1])
    label = "stroke" if prob > 0.5 else "normal"

    return {
        "prediction":  label,
        "probability": round(prob, 3),
        "confidence":  round(max(prob, 1 - prob) * 100, 1),
    }
