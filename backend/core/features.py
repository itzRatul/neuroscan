"""
NeuroScan — Feature Extraction
================================
Notebook: Stroke_detection_V_08.ipynb — Section 2
(MediaPipe Landmark Indices & Feature Functions)

All landmark indices, thresholds, and feature extraction logic
taken directly from the research notebook to ensure identical results.
"""

import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# Landmark indices (MediaPipe 468-point Face Mesh model)
# Source: Stroke_detection_V_08.ipynb — Section 2
# ─────────────────────────────────────────────────────────────────────────────
LANDMARKS = {
    'left_eye_top':     159,  'left_eye_bottom':  145,
    'right_eye_top':    386,  'right_eye_bottom': 374,
    'mouth_left':        61,  'mouth_right':      291,
    'mouth_top':         13,  'mouth_bottom':      14,
    'left_eyebrow':      70,  'right_eyebrow':    300,
    'nose_tip':           1,
    'left_nasolabial':   92,  'right_nasolabial': 322,
    'left_face_edge':   234,  'right_face_edge':  454,
    'chin':             152,  'forehead':          10,
}

# ─────────────────────────────────────────────────────────────────────────────
# Feature columns — order MUST match training order in notebook
# Source: Stroke_detection_V_08.ipynb — Section 2
# ─────────────────────────────────────────────────────────────────────────────
FEATURE_COLS = [
    'eye_asymmetry',
    'mouth_corner_drop',
    'eyebrow_height_diff',
    'nasolabial_asymmetry',
    'face_midline_deviation',
    'mouth_width_asymmetry',
]

# ─────────────────────────────────────────────────────────────────────────────
# Clinical thresholds
# Source: Stroke_detection_V_08.ipynb — Section 2
# Based on: FAST Protocol, Sunnybrook FGS, CPSS, Taufique & Savakis (2021)
# ─────────────────────────────────────────────────────────────────────────────
THRESHOLDS = {
    'eye_asymmetry':          0.12,
    'mouth_corner_drop':      0.10,
    'eyebrow_height_diff':    0.08,
    'nasolabial_asymmetry':   0.10,
    'face_midline_deviation': 0.05,
    'mouth_width_asymmetry':  0.10,
}

# ─────────────────────────────────────────────────────────────────────────────
# Human-readable display names
# ─────────────────────────────────────────────────────────────────────────────
FEATURE_DISPLAY_NAMES = {
    'eye_asymmetry':          'Eye Asymmetry (Ptosis)',
    'mouth_corner_drop':      'Mouth Corner Droop',
    'eyebrow_height_diff':    'Eyebrow Height Difference',
    'nasolabial_asymmetry':   'Nasolabial Fold Asymmetry',
    'face_midline_deviation': 'Facial Midline Deviation',
    'mouth_width_asymmetry':  'Mouth Width Asymmetry',
}

# Short names for annotated image labels
FEATURE_SHORT_NAMES = {
    'eye_asymmetry':          'Eye Asym',
    'mouth_corner_drop':      'Mouth Drop',
    'eyebrow_height_diff':    'Brow Diff',
    'nasolabial_asymmetry':   'Nasolabial',
    'face_midline_deviation': 'Midline',
    'mouth_width_asymmetry':  'Mouth Width',
}

# Clinical basis references (used in PDF report)
FEATURE_CLINICAL_BASIS = {
    'eye_asymmetry':          'Ross et al. (Sunnybrook FGS)',
    'mouth_corner_drop':      'Kothari et al. (CPSS FAST)',
    'eyebrow_height_diff':    'Ross et al. (Sunnybrook FGS)',
    'nasolabial_asymmetry':   'Taufique & Savakis (2021)',
    'face_midline_deviation': 'Taufique & Savakis (2021)',
    'mouth_width_asymmetry':  'Kothari et al. (CPSS FAST)',
}

# Landmark groups for each feature (for annotated image drawing)
# Source: Stroke_detection_V_08.ipynb — Section 8 Cell 2
FEATURE_LANDMARK_GROUPS = {
    'eye_asymmetry':          [159, 145, 386, 374],
    'mouth_corner_drop':      [61, 291],
    'eyebrow_height_diff':    [70, 300],
    'nasolabial_asymmetry':   [92, 322, 1],
    'face_midline_deviation': [1, 234, 454],
    'mouth_width_asymmetry':  [61, 291, 13, 14],
}


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# Source: Stroke_detection_V_08.ipynb — Section 2
# ─────────────────────────────────────────────────────────────────────────────
def euclidean(p1, p2) -> float:
    return float(np.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2))


# ─────────────────────────────────────────────────────────────────────────────
# Feature extraction — hbubu notebook Section 2 extract_features()
# Source: Stroke_detection_V_08.ipynb — Section 2
# ─────────────────────────────────────────────────────────────────────────────
def extract_features(landmarks: list) -> dict:
    """
    Extract 6 facial asymmetry features from MediaPipe 468-point landmarks.

    Taken directly from Stroke_detection_V_08.ipynb Section 2.

    Parameters
    ----------
    landmarks : list
        MediaPipe face landmarks (results.multi_face_landmarks[0].landmark)

    Returns
    -------
    dict with keys: eye_asymmetry, mouth_corner_drop, eyebrow_height_diff,
                    nasolabial_asymmetry, face_midline_deviation, mouth_width_asymmetry
    """
    lm = landmarks

    # Eye asymmetry — ptosis indicator (FAST "F")
    left_eye_h  = abs(lm[159].y - lm[145].y)
    right_eye_h = abs(lm[386].y - lm[374].y)
    eye_asym = abs(left_eye_h - right_eye_h) / (max(left_eye_h, right_eye_h) + 1e-6)

    # Mouth corner drop — FAST "F" / CPSS
    face_height = abs(lm[10].y - lm[152].y) + 1e-6
    mouth_drop  = abs(lm[61].y - lm[291].y) / face_height

    # Eyebrow height difference — Sunnybrook FGS
    left_brow  = abs(lm[70].y  - lm[159].y)
    right_brow = abs(lm[300].y - lm[386].y)
    brow_diff  = abs(left_brow - right_brow) / (max(left_brow, right_brow) + 1e-6)

    # Nasolabial fold asymmetry — Taufique & Savakis (2021)
    n2l  = euclidean(lm[1], lm[92])
    n2r  = euclidean(lm[1], lm[322])
    naso = abs(n2l - n2r) / (max(n2l, n2r) + 1e-6)

    # Face midline deviation — Taufique & Savakis (2021)
    face_cx = (lm[234].x + lm[454].x) / 2
    face_w  = abs(lm[234].x - lm[454].x) + 1e-6
    midline = abs(lm[1].x - face_cx) / face_w

    # Mouth width asymmetry — CPSS FAST
    mcx    = (lm[61].x + lm[291].x) / 2
    mw_l   = abs(lm[61].x  - mcx)
    mw_r   = abs(lm[291].x - mcx)
    mw_asy = abs(mw_l - mw_r) / (max(mw_l, mw_r) + 1e-6)

    return {
        'eye_asymmetry':          float(eye_asym),
        'mouth_corner_drop':      float(mouth_drop),
        'eyebrow_height_diff':    float(brow_diff),
        'nasolabial_asymmetry':   float(naso),
        'face_midline_deviation': float(midline),
        'mouth_width_asymmetry':  float(mw_asy),
    }


def build_feature_flags(features: dict) -> dict:
    """
    Build a per-feature status dict with value, threshold, and status.
    """
    flags = {}
    for key in FEATURE_COLS:
        val    = features[key]
        thresh = THRESHOLDS[key]
        flags[key] = {
            'display_name':    FEATURE_DISPLAY_NAMES[key],
            'clinical_basis':  FEATURE_CLINICAL_BASIS[key],
            'value':     round(val, 4),
            'threshold': thresh,
            'status':    'HIGH' if val > thresh else 'Normal',
            'flagged':   val > thresh,
        }
    return flags
