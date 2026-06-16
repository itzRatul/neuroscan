"""
NeuroScan — FastAPI Backend
============================
Face Analysis API — image upload → MediaPipe → ML model → report

Endpoints:
  POST /analyze          — main analysis endpoint
  GET  /results/{id}/{f} — serve annotated image, gauge, PDF
  GET  /health           — health check

API Key Protection:
  Pass X-API-Key header with every request.
  Set NEUROSCAN_API_KEY env variable on the server.
  Same key used by: website, Telegram bot, future WhatsApp bot.
"""

import os
import sys
import uuid
import logging
import datetime
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure backend root is on path (for generate_report.py)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
import mediapipe as mp
import requests
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from core.features  import extract_features, build_feature_flags
from core.predictor import predict_stroke_risk, load_model
from core.annotator import draw_annotated_image, annotated_image_to_bytes
from core.gauge     import generate_gauge_bytes
from generate_report import generate_pdf_report

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("neuroscan")

# ─────────────────────────────────────────────────────────────────────────────
# Config from environment variables
# ─────────────────────────────────────────────────────────────────────────────
API_KEY     = os.getenv("NEUROSCAN_API_KEY", "")          # Set this on the server!
RESULTS_DIR = Path(os.getenv("RESULTS_DIR", "results"))   # Where to store output files
MAX_MB      = int(os.getenv("MAX_UPLOAD_MB", "10"))        # Max upload size (MB)

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# MediaPipe global ref
# ─────────────────────────────────────────────────────────────────────────────
mp_face_mesh = None


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan — startup + shutdown (MUST be defined before app = FastAPI(...))
# ─────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(application: FastAPI):
    global mp_face_mesh
    logger.info("🚀 NeuroScan backend starting …")
    load_model()
    mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
    )
    logger.info("✅ Model + scaler + MediaPipe ready.")
    yield
    if mp_face_mesh:
        mp_face_mesh.close()
    logger.info("🛑 NeuroScan backend stopped.")


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="NeuroScan Face Analysis API",
    description=(
        "Upload a face photo → MediaPipe + ML model → stroke risk report.\n\n"
        "Method: MediaPipe Face Mesh (468 landmarks) → 6 asymmetry features "
        "→ stroke_model.pkl → risk prediction + annotated image + gauge + PDF.\n\n"
        "Notebook: Stroke_detection_V_08.ipynb"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ─────────────────────────────────────────────────────────────────────────────
# CORS — website, Telegram webhook, future WhatsApp can all call this
# ─────────────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production if needed
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Static file mount — serve results (images, PDFs)
# ─────────────────────────────────────────────────────────────────────────────
app.mount("/results", StaticFiles(directory=str(RESULTS_DIR)), name="results")


# ─────────────────────────────────────────────────────────────────────────────
# API Key dependency — used by /analyze endpoint
# ─────────────────────────────────────────────────────────────────────────────
async def verify_api_key(request: Request):
    """
    Verify X-API-Key header.
    If NEUROSCAN_API_KEY env var is empty, all requests pass (development mode).
    """
    if not API_KEY:
        # Dev mode — no key required
        return
    key = request.headers.get("X-API-Key", "")
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


# ─────────────────────────────────────────────────────────────────────────────
# GET /
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/", tags=["System"])
async def root():
    return {
        "status": "ok",
        "service": "NeuroScan Face Analysis API",
        "message": "Welcome to NeuroScan Face Analysis API! Health check at /health.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /health
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "ok",
        "service": "NeuroScan Face Analysis API",
        "version": "1.0.0",
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /analyze — main endpoint
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/analyze", tags=["Analysis"])
async def analyze(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Face photo (JPG / PNG / WEBP)"),
    session_id: str = Form(None, description="Optional chat session ID to sync results"),
    _: None = Depends(verify_api_key),
):
    """
    Analyze a face photo for stroke risk using MediaPipe + ML model.

    Pipeline (from Stroke_detection_V_08.ipynb):
    1. MediaPipe Face Mesh — detect 468 landmarks
    2. extract_features()  — 6 asymmetry metrics (Section 2)
    3. stroke_scaler.pkl   — StandardScaler normalize
    4. stroke_model.pkl    — predict probability (Section 5B)
    5. draw_annotated_image() — face mesh + colored markers (Section 8 Cell 2)
    6. draw_gauge()           — semicircular gauge (Section 8 Cell 3)
    7. generate_pdf_report()  — 2-page clinical PDF (Section 10)

    Returns JSON with features, prediction, and URLs for images + PDF.
    """

    # ── 1. Validate file type ──
    allowed = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
    if file.content_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Use JPG, PNG, or WEBP.",
        )

    # ── 2. Read & decode image ──
    raw = await file.read()
    if len(raw) > MAX_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large. Max {MAX_MB} MB.")

    img_arr = np.frombuffer(raw, np.uint8)
    img_bgr = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise HTTPException(status_code=400, detail="Could not decode image. Please send a valid photo.")

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # ── 3. MediaPipe landmark detection ──
    results = mp_face_mesh.process(img_rgb)
    if not results.multi_face_landmarks:
        raise HTTPException(
            status_code=422,
            detail=(
                "No face detected in the photo. "
                "Please use a clear, front-facing headshot with good lighting."
            ),
        )

    face_landmarks = results.multi_face_landmarks[0]

    # ── 4. Feature extraction (notebook Section 2) ──
    features = extract_features(face_landmarks.landmark)
    flags    = build_feature_flags(features)

    # ── 5. ML prediction (notebook Section 2 + 5B) ──
    prediction = predict_stroke_risk(features)

    # ── 6. Create report directory ──
    report_id  = f"NS-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    report_dir = RESULTS_DIR / report_id
    report_dir.mkdir(parents=True, exist_ok=True)

    # ── 7. Annotated image (notebook Section 8 Cell 2) ──
    annotated_rgb = draw_annotated_image(img_rgb, face_landmarks, features, prediction)
    annotated_bytes = annotated_image_to_bytes(annotated_rgb)
    annotated_path  = report_dir / "annotated.png"
    annotated_path.write_bytes(annotated_bytes)

    # ── 8. Gauge chart (notebook Section 8 Cell 3) ──
    gauge_bytes = generate_gauge_bytes(prediction)
    gauge_path  = report_dir / "gauge.png"
    gauge_path.write_bytes(gauge_bytes)

    # ── 9. PDF report (notebook Section 10) ──
    date_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    pdf_filename = f"NeuroScan_Report_{date_str}.pdf"
    pdf_path = str(report_dir / pdf_filename)
    generate_pdf_report(
        features=features,
        prediction=prediction,
        annotated_img_path=str(annotated_path),
        gauge_img_path=str(gauge_path),
        output_pdf_path=pdf_path,
        pagesize_name="letter",
    )

    # ── 10. Build response ──
    base_url = f"/results/{report_id}"

    result_data = {
        "features": {k: round(v, 4) for k, v in features.items()},
        "feature_flags": flags,
        "prediction": prediction
    }

    if session_id:
        def sync_result():
            try:
                chat_url = os.getenv("CHAT_BACKEND_URL", "http://localhost:8001").rstrip("/")
                requests.post(f"{chat_url}/webhook/test_result", json={
                    "session_id": session_id,
                    "result_data": result_data
                }, timeout=5)
            except Exception as e:
                logger.error(f"Failed to sync result to chat backend: {e}")
        background_tasks.add_task(sync_result)

    return JSONResponse({
        "success":    True,
        "report_id":  report_id,

        # Raw feature values
        "features": result_data["features"],

        # Per-feature flag table (matching notebook Section 7 output)
        "feature_flags": result_data["feature_flags"],

        # ML prediction result
        "prediction": result_data["prediction"],

        # Output file URLs
        "annotated_image_url": f"{base_url}/annotated.png",
        "gauge_image_url":     f"{base_url}/gauge.png",
        "pdf_url":             f"{base_url}/{pdf_filename}",
    })
