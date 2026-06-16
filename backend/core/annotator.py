"""
NeuroScan — Annotated Image Generator
=======================================
Notebook: Stroke_detection_V_08.ipynb — Section 8 Cell 2

draw_annotated_image() taken directly from the notebook.
Draws face mesh + colored landmark circles + bottom risk banner.

Research basis (from notebook comments):
  - Aldridge et al. (2022) — explainability; users need to see WHY
  - Gomes et al. (2024)   — lower facial region most discriminative
  - Taufique & Savakis (2021) — landmark-based asymmetry regions
"""

import io
import logging
import numpy as np
import cv2
import mediapipe as mp
from PIL import Image

from core.features import FEATURE_LANDMARK_GROUPS, FEATURE_SHORT_NAMES, THRESHOLDS

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# draw_annotated_image — hbubu notebook Section 8 Cell 2
# Source: Stroke_detection_V_08.ipynb — Section 8 Cell 2
# ─────────────────────────────────────────────────────────────────────────────
def draw_annotated_image(
    img_rgb: np.ndarray,
    face_landmarks,
    features: dict,
    prediction: dict,
    thresholds: dict = None,
) -> np.ndarray:
    """
    Draw face mesh + colored landmark highlights on the image.

    Taken directly from Stroke_detection_V_08.ipynb Section 8 Cell 2.

    - Full face mesh: gray (background context)
    - Normal features: green circle
    - HIGH features:   red circle + label
    - Bottom banner:   risk result

    Returns
    -------
    np.ndarray : annotated image in RGB
    """
    if thresholds is None:
        thresholds = THRESHOLDS

    mp_drawing  = mp.solutions.drawing_utils
    mp_face_mesh = mp.solutions.face_mesh

    img = img_rgb.copy()
    h, w = img.shape[:2]
    lm = face_landmarks.landmark

    # ── Draw full face mesh (gray, thin) ──
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    mp_drawing.draw_landmarks(
        image=img_bgr,
        landmark_list=face_landmarks,
        connections=mp_face_mesh.FACEMESH_TESSELATION,
        landmark_drawing_spec=None,
        connection_drawing_spec=mp_drawing.DrawingSpec(
            color=(180, 180, 180), thickness=1, circle_radius=0
        ),
    )
    img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # ── Draw colored circles on landmark points ──
    for feat_key, lm_indices in FEATURE_LANDMARK_GROUPS.items():
        val     = features[feat_key]
        thresh  = thresholds[feat_key]
        is_high = val > thresh

        color  = (220, 50,  50)  if is_high else (50, 200, 80)   # red / green
        radius = 8               if is_high else 5

        for idx in lm_indices:
            px = int(lm[idx].x * w)
            py = int(lm[idx].y * h)
            cv2.circle(img, (px, py), radius, color, -1)
            cv2.circle(img, (px, py), radius + 2, (255, 255, 255), 1)  # white border

        # ── Label on first landmark point (HIGH features only) ──
        if is_high:
            px0 = int(lm[lm_indices[0]].x * w)
            py0 = int(lm[lm_indices[0]].y * h)
            label_txt = f"{FEATURE_SHORT_NAMES[feat_key]} ✗"
            cv2.putText(
                img, label_txt,
                (px0 + 10, py0 - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                (220, 50, 50), 1, cv2.LINE_AA,
            )

    # ── Bottom risk banner ──
    banner_h = 60
    overlay  = img.copy()
    cv2.rectangle(overlay, (0, h - banner_h), (w, h), (20, 20, 20), -1)
    img = cv2.addWeighted(overlay, 0.75, img, 0.25, 0)

    risk_pct = prediction['percentage']
    risk_lvl = prediction['risk_level'].split('—')[0].strip()

    banner_color = {
        'green':  (50,  200,  80),
        'orange': (255, 165,   0),
        'red':    (220,  50,  50),
    }[prediction['color_hint']]

    cv2.putText(
        img,
        f"{risk_lvl}  —  {risk_pct:.1f}%",
        (12, h - banner_h + 38),
        cv2.FONT_HERSHEY_DUPLEX, 0.75,
        banner_color, 1, cv2.LINE_AA,
    )

    return img


def annotated_image_to_bytes(annotated_rgb: np.ndarray, fmt: str = 'PNG') -> bytes:
    """Convert annotated numpy array (RGB) to PNG bytes."""
    pil_img = Image.fromarray(annotated_rgb)
    buf = io.BytesIO()
    pil_img.save(buf, format=fmt)
    buf.seek(0)
    return buf.read()
