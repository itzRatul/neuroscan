"""
NeuroScan — Model Predictor
============================
Notebook: Stroke_detection_V_08.ipynb — Section 2 + Section 5B

predict_stroke_risk() taken directly from the notebook.
Risk thresholds: < 0.25 → LOW (green), 0.25–0.55 → MODERATE (orange), > 0.55 → HIGH (red)
"""

import os
import logging
import numpy as np
import joblib

from core.features import FEATURE_COLS

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Paths — relative to backend/
# ─────────────────────────────────────────────────────────────────────────────
BACKEND_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH   = os.path.join(BACKEND_DIR, 'stroke_model.pkl')
SCALER_PATH  = os.path.join(BACKEND_DIR, 'stroke_scaler.pkl')

# ─────────────────────────────────────────────────────────────────────────────
# Lazy-load — model loaded once on first request (or at startup)
# ─────────────────────────────────────────────────────────────────────────────
_model  = None
_scaler = None


def load_model():
    """Load stroke_model.pkl and stroke_scaler.pkl into memory."""
    global _model, _scaler
    if _model is None or _scaler is None:
        logger.info(f"Loading model  → {MODEL_PATH}")
        logger.info(f"Loading scaler → {SCALER_PATH}")
        _model  = joblib.load(MODEL_PATH)
        _scaler = joblib.load(SCALER_PATH)
        logger.info("✅ Model + scaler loaded successfully.")
    return _model, _scaler


def get_model():
    """Return cached (model, scaler) tuple."""
    return load_model()


# ─────────────────────────────────────────────────────────────────────────────
# predict_stroke_risk — hbubu notebook Section 2
# Source: Stroke_detection_V_08.ipynb — Section 2
# ─────────────────────────────────────────────────────────────────────────────
def predict_stroke_risk(features_dict: dict, model=None, scaler=None) -> dict:
    """
    Predict stroke risk from 6 extracted facial features.

    Taken directly from Stroke_detection_V_08.ipynb Section 2.
    Risk bands:
        < 0.25  → LOW RISK             (green)
        0.25–0.55 → MODERATE RISK      (orange)
        > 0.55  → HIGH RISK            (red)

    Parameters
    ----------
    features_dict : dict
        Output of extract_features()
    model, scaler : optional
        If None, uses globally loaded model/scaler

    Returns
    -------
    dict: probability, percentage, label, risk_level, color_hint
    """
    if model is None or scaler is None:
        model, scaler = get_model()

    X     = np.array([[features_dict[f] for f in FEATURE_COLS]])
    X_sc  = scaler.transform(X)
    prob  = model.predict_proba(X_sc)[0][1]
    label = model.predict(X_sc)[0]

    # Risk bands — identical to notebook
    if prob < 0.25:
        risk, hint = "LOW RISK", "green"
    elif prob < 0.55:
        risk, hint = "MODERATE RISK — Consult a doctor", "orange"
    else:
        risk, hint = "HIGH RISK — Seek immediate medical help", "red"

    return {
        'probability': round(float(prob), 4),
        'percentage':  round(float(prob) * 100, 2),
        'label':       int(label),
        'risk_level':  risk,
        'color_hint':  hint,
    }
