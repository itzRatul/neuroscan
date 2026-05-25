/* ============================================================
   NeuroScan — Test page logic
   Loaded only by test.html.
   MediaPipe Face Landmarker + Web Speech + Chart.js + jsPDF.
============================================================ */

// ── Hugging Face backend URL ──────────────────────────────────
// After deploying to HF Spaces, replace this with your Space URL.
// Example: "https://your-username-neuroscan-backend.hf.space"
const HF_API = "https://itzratul-neuroscan-backend.hf.space";
// ─────────────────────────────────────────────────────────────

import {
  FaceLandmarker,
  FilesetResolver,
} from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.9/vision_bundle.mjs";

/* ---------- Landmark indices ---------- */
const IDX = {
  MOUTH_LEFT:        61,
  MOUTH_RIGHT:      291,
  LEFT_EYE_TOP:     159,
  LEFT_EYE_BOTTOM:  145,
  RIGHT_EYE_TOP:    386,
  RIGHT_EYE_BOTTOM: 374,
  NOSE_TIP:           1,
};

/* ---------- Thresholds ---------- */
// Smile trigger is ~1% of frame height so the detector behaves the same on a
// 480p webcam and a 720p+ phone camera.
const SMILE_TRIGGER_FRACTION = 0.0104;
const CLOSE_RATIO      = 0.35;
const OPEN_RATIO       = 1.25;
const ACTION_DURATION  = 3.0;
const REST_DURATION    = 4.0;

/* ---------- DOM refs ---------- */
const $ = (id) => document.getElementById(id);

const video        = $("webcam");
const overlay      = $("overlay");
const ctx          = overlay.getContext("2d");

const phaseLabel   = $("phase-label");
const promptEl     = $("action-prompt");
const promptIcon   = $("prompt-icon");
const promptText   = $("prompt-text");
const promptSub    = $("prompt-sub");

const ring         = $("progress-ring");
const ringFg       = $("ring-fg");
const ringText     = $("ring-text");
const RING_LEN     = 276.46;

const mFace        = $("m-face");
const mFps         = $("m-fps");

const resultsPanel = $("results-panel");

/* Lucide-style mini SVG icons used by the prompt area */
const SVG = {
  rest:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/></svg>`,
  smile:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>`,
  close:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7"/><line x1="2" y1="20" x2="22" y2="4"/></svg>`,
  open:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>`,
  init:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>`,
};

/* ---------- State ---------- */
let landmarker = null;
let stream     = null;
let running    = false;
let lastVideoTime = -1;
let fpsCounter = { frames: 0, last: performance.now(), val: 0 };

let stateName  = "init";
let stateStart = 0;
let restSamples = [];
let restRef = null;
let measurements = {
  smile1: null, smile2: null, close: null, open: null,
  sideMove: { leftMouth: 0, rightMouth: 0, leftEye: 0, rightEye: 0 },
};
let liveMax = {
  smile1: { lm_up: 0, rm_up: 0 },
  smile2: { lm_up: 0, rm_up: 0 },
  close:  { le_min: Infinity, re_min: Infinity },
  open:   { le_max: 0, re_max: 0 },
};

/* ---------- Voice ---------- */
const voiceQueue = [];
let voiceBusy = false;
function speak(text) {
  if (!("speechSynthesis" in window)) return;
  voiceQueue.push(text);
  drainVoice();
}
function drainVoice() {
  if (voiceBusy || voiceQueue.length === 0) return;
  const text = voiceQueue.shift();
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 1.0; u.pitch = 1.0;
  u.lang = (navigator.language && navigator.language.startsWith("en"))
    ? navigator.language
    : "en-US";
  u.onend   = () => { voiceBusy = false; drainVoice(); };
  u.onerror = () => { voiceBusy = false; drainVoice(); };
  voiceBusy = true;
  speechSynthesis.speak(u);
}

/* ---------- Buttons ---------- */
$("btn-cancel")?.addEventListener("click", () => { stopWebcam(); window.location.href = "index.html"; });
$("btn-retest")?.addEventListener("click", () => { hideResults(); startTest(); });
$("btn-home")  ?.addEventListener("click", () => { stopWebcam(); window.location.href = "index.html"; });
$("btn-download")?.addEventListener("click", () => downloadReport());

/* ---------- MediaPipe init ---------- */
async function initLandmarker() {
  if (landmarker) return landmarker;
  const fileset = await FilesetResolver.forVisionTasks(
    "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.9/wasm"
  );
  landmarker = await FaceLandmarker.createFromOptions(fileset, {
    baseOptions: {
      modelAssetPath:
        "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
      delegate: "GPU",
    },
    outputFaceBlendshapes: false,
    runningMode: "VIDEO",
    numFaces: 1,
  });
  return landmarker;
}

/* ---------- Webcam ---------- */
async function startWebcam() {
  // Request an ideal HD frame but accept whatever the device offers — keeps
  // quality high on modern phones while still working on low-res webcams.
  stream = await navigator.mediaDevices.getUserMedia({
    video: {
      width:  { ideal: 1280 },
      height: { ideal: 720 },
      facingMode: "user",
    },
    audio: false,
  });
  video.srcObject = stream;
  await new Promise((res) => (video.onloadedmetadata = res));
  await video.play();
  overlay.width  = video.videoWidth;
  overlay.height = video.videoHeight;
}
function stopWebcam() {
  running = false;
  if (stream) {
    stream.getTracks().forEach((t) => t.stop());
    stream = null;
  }
  speechSynthesis.cancel();
  voiceQueue.length = 0;
  voiceBusy = false;
}

/* ---------- Start test ---------- */
async function startTest() {
  resetState();
  setPrompt("Initialising camera…", "Please allow camera access when prompted.", "waiting", SVG.init);
  setPhase("INIT");

  try {
    await initLandmarker();
    await startWebcam();
  } catch (e) {
    console.error(e);
    setPrompt("Camera access denied", "Please allow camera permissions and reload the page.", "waiting", SVG.init);
    return;
  }

  running = true;
  transition("rest", performance.now() / 1000);
  loop();
}

function resetState() {
  stateName = "init";
  restSamples = [];
  restRef = null;
  measurements = {
    smile1: null, smile2: null, close: null, open: null,
    sideMove: { leftMouth: 0, rightMouth: 0, leftEye: 0, rightEye: 0 },
  };
  liveMax = {
    smile1: { lm_up: 0, rm_up: 0 },
    smile2: { lm_up: 0, rm_up: 0 },
    close:  { le_min: Infinity, re_min: Infinity },
    open:   { le_max: 0, re_max: 0 },
  };
  document.querySelectorAll(".step").forEach((s) => s.classList.remove("active", "done"));
  ring.classList.remove("visible");
  ringFg.style.strokeDashoffset = RING_LEN;
}

/* ---------- State transitions ---------- */
const VOICE = {
  rest:        "Keep your face relaxed and natural.",
  smile1_wait: "Now please smile.",
  smile1_act:  "Great. Hold your smile.",
  close_wait:  "Now close your eyes gently.",
  close_act:   "Good. Keep them closed.",
  open_wait:   "Now open your eyes wide.",
  open_act:    "Good. Hold it.",
  smile2_wait: "Smile one more time.",
  smile2_act:  "Excellent. Hold your smile.",
};
const PROMPT = {
  rest:        { icon: SVG.rest,  text: "Rest — keep face natural", sub: "Look straight at the camera" },
  smile1_wait: { icon: SVG.smile, text: "Smile naturally",          sub: "Waiting for you to smile…" },
  smile1_act:  { icon: SVG.smile, text: "Hold that smile",          sub: "Counting down…" },
  close_wait:  { icon: SVG.close, text: "Close your eyes",          sub: "Waiting for you to close…" },
  close_act:   { icon: SVG.close, text: "Keep them closed",         sub: "Counting down…" },
  open_wait:   { icon: SVG.open,  text: "Open eyes wide",           sub: "Waiting for you to open wide…" },
  open_act:    { icon: SVG.open,  text: "Hold them wide",           sub: "Counting down…" },
  smile2_wait: { icon: SVG.smile, text: "Smile again",              sub: "Waiting for you to smile…" },
  smile2_act:  { icon: SVG.smile, text: "Hold that smile",          sub: "Counting down…" },
};
const STEP_OF = {
  rest: 0, smile1_wait: 1, smile1_act: 1,
  close_wait: 2, close_act: 2,
  open_wait: 3, open_act: 3,
  smile2_wait: 4, smile2_act: 4,
};

function transition(newState, t) {
  const prevStep = STEP_OF[stateName];
  const newStep  = STEP_OF[newState];
  if (prevStep !== undefined && newStep !== undefined && newStep > prevStep) {
    const prevEl = document.querySelector(`.step[data-step="${prevStep}"]`);
    if (prevEl) { prevEl.classList.remove("active"); prevEl.classList.add("done"); }
  }
  document.querySelectorAll(".step").forEach((s) => s.classList.remove("active"));
  const curEl = document.querySelector(`.step[data-step="${newStep}"]`);
  if (curEl) curEl.classList.add("active");

  stateName  = newState;
  stateStart = t;

  const p = PROMPT[newState];
  if (p) {
    const cls = newState.endsWith("_act") || newState === "rest" ? "acting" : "waiting";
    setPrompt(p.text, p.sub, cls, p.icon);
  }
  setPhase(newState.toUpperCase().replace("_", " "));

  if (VOICE[newState]) speak(VOICE[newState]);

  if (newState === "rest" || newState.endsWith("_act")) ring.classList.add("visible");
  else ring.classList.remove("visible");
}

function setPrompt(text, sub, cls, icon) {
  promptText.textContent = text;
  promptSub.textContent  = sub || "";
  promptEl.classList.remove("waiting", "acting");
  if (cls)  promptEl.classList.add(cls);
  if (icon) promptIcon.innerHTML = icon;
}
function setPhase(label) { phaseLabel.textContent = label; }

/* ---------- Action detectors ---------- */
function isSmiling(ml_y, mr_y) {
  if (!restRef) return false;
  const up = ((restRef.ml_y - ml_y) + (restRef.mr_y - mr_y)) / 2;
  const triggerPx = video.videoHeight * SMILE_TRIGGER_FRACTION;
  return up > triggerPx;
}
function isEyesClosed(le, re) {
  if (!restRef) return false;
  return (le + re) / 2 < (restRef.le_h + restRef.re_h) / 2 * CLOSE_RATIO;
}
function isEyesWide(le, re) {
  if (!restRef) return false;
  return (le + re) / 2 > (restRef.le_h + restRef.re_h) / 2 * OPEN_RATIO;
}

/* ---------- Main loop ---------- */
function loop() {
  if (!running) return;
  const tNow = performance.now() / 1000;

  if (video.currentTime !== lastVideoTime && video.readyState >= 2) {
    lastVideoTime = video.currentTime;
    const result = landmarker.detectForVideo(video, performance.now());

    fpsCounter.frames++;
    const dt = performance.now() - fpsCounter.last;
    if (dt > 500) {
      fpsCounter.val = (fpsCounter.frames * 1000 / dt).toFixed(0);
      fpsCounter.frames = 0;
      fpsCounter.last = performance.now();
      mFps.textContent = `${fpsCounter.val} FPS`;
    }

    drawOverlay(result);
    if (result.faceLandmarks && result.faceLandmarks.length > 0) {
      mFace.textContent = "Yes";
      processLandmarks(result.faceLandmarks[0], tNow);
    } else {
      mFace.textContent = "No";
    }
  }

  updateProgressRing(tNow);
  requestAnimationFrame(loop);
}

/* ---------- Overlay ---------- */
function drawOverlay(result) {
  ctx.clearRect(0, 0, overlay.width, overlay.height);
  if (!result.faceLandmarks || result.faceLandmarks.length === 0) return;
  const lm = result.faceLandmarks[0];
  const w = overlay.width, h = overlay.height;

  ctx.fillStyle = "rgba(31, 111, 235, 0.55)";
  for (let i = 0; i < lm.length; i += 8) {
    ctx.beginPath();
    ctx.arc(lm[i].x * w, lm[i].y * h, 1.2, 0, Math.PI * 2);
    ctx.fill();
  }
  const keys = [
    IDX.MOUTH_LEFT, IDX.MOUTH_RIGHT,
    IDX.LEFT_EYE_TOP, IDX.LEFT_EYE_BOTTOM,
    IDX.RIGHT_EYE_TOP, IDX.RIGHT_EYE_BOTTOM,
  ];
  ctx.fillStyle = "#10b981";
  keys.forEach((idx) => {
    const p = lm[idx];
    ctx.beginPath();
    ctx.arc(p.x * w, p.y * h, 4.5, 0, Math.PI * 2);
    ctx.fill();
  });
}

/* ---------- Landmark processor per state ---------- */
function processLandmarks(lm, t) {
  const w = video.videoWidth, h = video.videoHeight;
  const ml_y = lm[IDX.MOUTH_LEFT].y * h;
  const mr_y = lm[IDX.MOUTH_RIGHT].y * h;
  const ml_x = lm[IDX.MOUTH_LEFT].x * w;
  const mr_x = lm[IDX.MOUTH_RIGHT].x * w;
  const le_h = Math.abs(lm[IDX.LEFT_EYE_TOP].y - lm[IDX.LEFT_EYE_BOTTOM].y) * h;
  const re_h = Math.abs(lm[IDX.RIGHT_EYE_TOP].y - lm[IDX.RIGHT_EYE_BOTTOM].y) * h;
  const mouth_w = Math.abs(mr_x - ml_x);

  const elapsed = t - stateStart;

  switch (stateName) {
    case "rest": {
      restSamples.push({ ml_y, mr_y, le_h, re_h, mouth_w });
      if (elapsed >= REST_DURATION) {
        restRef = avg(restSamples);
        transition("smile1_wait", t);
      }
      break;
    }
    case "smile1_wait":
      if (isSmiling(ml_y, mr_y)) transition("smile1_act", t);
      break;
    case "smile1_act": {
      const lm_up = restRef.ml_y - ml_y;
      const rm_up = restRef.mr_y - mr_y;
      if (lm_up > liveMax.smile1.lm_up) liveMax.smile1.lm_up = lm_up;
      if (rm_up > liveMax.smile1.rm_up) liveMax.smile1.rm_up = rm_up;
      if (elapsed >= ACTION_DURATION) {
        const { lm_up: L, rm_up: R } = liveMax.smile1;
        const denom = Math.max(L, R, 1);
        measurements.smile1 = Math.abs(L - R) / denom;
        measurements.sideMove.leftMouth  = L;
        measurements.sideMove.rightMouth = R;
        transition("close_wait", t);
      }
      break;
    }
    case "close_wait":
      if (isEyesClosed(le_h, re_h)) transition("close_act", t);
      break;
    case "close_act": {
      if (le_h < liveMax.close.le_min) liveMax.close.le_min = le_h;
      if (re_h < liveMax.close.re_min) liveMax.close.re_min = re_h;
      if (elapsed >= ACTION_DURATION) {
        const lClose = 1 - liveMax.close.le_min / restRef.le_h;
        const rClose = 1 - liveMax.close.re_min / restRef.re_h;
        const denom  = Math.max(lClose, rClose, 0.01);
        measurements.close = Math.abs(lClose - rClose) / denom;
        transition("open_wait", t);
      }
      break;
    }
    case "open_wait":
      if (isEyesWide(le_h, re_h)) transition("open_act", t);
      break;
    case "open_act": {
      if (le_h > liveMax.open.le_max) liveMax.open.le_max = le_h;
      if (re_h > liveMax.open.re_max) liveMax.open.re_max = re_h;
      if (elapsed >= ACTION_DURATION) {
        const lOpen = liveMax.open.le_max / restRef.le_h - 1;
        const rOpen = liveMax.open.re_max / restRef.re_h - 1;
        const denom = Math.max(lOpen, rOpen, 0.01);
        measurements.open = Math.abs(lOpen - rOpen) / denom;
        measurements.sideMove.leftEye  = lOpen;
        measurements.sideMove.rightEye = rOpen;
        transition("smile2_wait", t);
      }
      break;
    }
    case "smile2_wait":
      if (isSmiling(ml_y, mr_y)) transition("smile2_act", t);
      break;
    case "smile2_act": {
      const lm_up = restRef.ml_y - ml_y;
      const rm_up = restRef.mr_y - mr_y;
      if (lm_up > liveMax.smile2.lm_up) liveMax.smile2.lm_up = lm_up;
      if (rm_up > liveMax.smile2.rm_up) liveMax.smile2.rm_up = rm_up;
      if (elapsed >= ACTION_DURATION) {
        const { lm_up: L, rm_up: R } = liveMax.smile2;
        const denom = Math.max(L, R, 1);
        measurements.smile2 = Math.abs(L - R) / denom;
        finishTest();
      }
      break;
    }
  }
}

/* ---------- Progress ring ---------- */
function updateProgressRing(t) {
  const elapsed = t - stateStart;
  let duration = 0;
  if (stateName === "rest") duration = REST_DURATION;
  else if (stateName.endsWith("_act")) duration = ACTION_DURATION;
  else { ringText.textContent = ""; return; }

  const pct = Math.min(elapsed / duration, 1);
  const remaining = Math.max(0, Math.ceil(duration - elapsed));
  ringText.textContent = remaining;
  ringFg.style.strokeDashoffset = RING_LEN * (1 - pct);
}

/* ---------- Helpers ---------- */
function avg(arr) {
  const k = Object.keys(arr[0]);
  const o = {};
  k.forEach((key) => o[key] = arr.reduce((s, x) => s + x[key], 0) / arr.length);
  return o;
}

/* ---------- ML backend call ---------- */
async function fetchMLPrediction(mouthAsym, eyeAsym) {
  const card = document.getElementById("ml-card");
  const badge = document.getElementById("ml-badge");
  const pred  = document.getElementById("ml-prediction");
  const conf  = document.getElementById("ml-confidence");
  if (!card) return;

  try {
    const res = await fetch(`${HF_API}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mouth_asym: mouthAsym, eye_asym: eyeAsym, brow_asym: 0 }),
    });
    if (!res.ok) throw new Error("Server error");
    const data = await res.json();

    const isStroke = data.prediction === "stroke";
    badge.textContent = isStroke ? "Stroke detected" : "Normal";
    badge.className   = "ml-badge " + (isStroke ? "ml-badge-high" : "ml-badge-normal");
    pred.textContent  = `${data.confidence}% confidence`;
    conf.textContent  = `Model probability: ${(data.probability * 100).toFixed(1)}%`;
  } catch {
    badge.textContent = "Unavailable";
    badge.className   = "ml-badge ml-badge-off";
    pred.textContent  = "Could not reach ML backend.";
    conf.textContent  = "Deploy the backend on Hugging Face first.";
  }
}

/* ---------- Finish ---------- */
function finishTest() {
  running = false;
  stopWebcam();

  const smileAvg = (measurements.smile1 + measurements.smile2) / 2;
  const closeAsym = measurements.close;
  const openAsym  = measurements.open;

  const rawScore = smileAvg * 0.5 + closeAsym * 0.25 + openAsym * 0.25;
  const score = Math.min(100, Math.round(rawScore * 100));

  let verdict, verdictClass, recommendation, voice;
  if (score > 60) {
    verdict = "HIGH RISK";
    verdictClass = "high";
    recommendation = "The test detected significant facial movement asymmetry — a possible sign of stroke. Please contact emergency services or visit the nearest hospital immediately. Time is critical.";
    voice = "High risk detected. Please seek immediate medical attention.";
  } else if (score > 30) {
    verdict = "MODERATE";
    verdictClass = "moderate";
    recommendation = "Mild asymmetry detected. While not alarming on its own, we recommend repeating the test and consulting a clinician if you notice other symptoms (weakness, slurred speech, dizziness).";
    voice = "Moderate risk detected. Please monitor closely.";
  } else {
    verdict = "NORMAL";
    verdictClass = "normal";
    recommendation = "Your facial movement appears symmetric. No signs of stroke-related asymmetry were detected in this screening. Continue routine health monitoring.";
    voice = "Test complete. Result appears normal.";
  }

  speak(voice);
  renderResults({
    score, verdict, verdictClass, recommendation,
    smile1: measurements.smile1, smile2: measurements.smile2,
    smileAvg, closeAsym, openAsym,
    side: measurements.sideMove,
  });
  showResults();

  // ML backend — secondary validation (non-blocking)
  const eyeAsym = (closeAsym + openAsym) / 2;
  fetchMLPrediction(smileAvg, eyeAsym);
}

/* ---------- Show / hide results panel ---------- */
function showResults() {
  resultsPanel.style.display = "block";
  requestAnimationFrame(() => resultsPanel.classList.add("shown"));
  setTimeout(() => resultsPanel.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
}
function hideResults() {
  resultsPanel.classList.remove("shown");
  resultsPanel.style.display = "none";
}

/* ---------- Render results ---------- */
let charts = { bars: null, pie: null, side: null };

function renderResults(r) {
  // ML card reset করো যাতে retest-এ "Checking…" দেখায়
  const mlBadge = $("ml-badge");
  if (mlBadge) {
    mlBadge.textContent = "Checking…";
    mlBadge.className   = "ml-badge";
    $("ml-prediction").textContent = "—";
    $("ml-confidence").textContent = "Waiting for server response…";
  }

  $("verdict-text").textContent  = r.verdict;
  $("verdict-score").textContent = r.score;
  $("recommendation-text").textContent = r.recommendation;
  const v = $("verdict");
  v.classList.remove("normal", "moderate", "high");
  v.classList.add(r.verdictClass);

  const now = new Date();
  $("report-meta").textContent =
    `Generated ${now.toLocaleDateString()} · ${now.toLocaleTimeString()} · ID #${Math.random().toString(36).slice(2, 8).toUpperCase()}`;

  Object.values(charts).forEach((c) => c && c.destroy());

  const isMobile = window.matchMedia("(max-width: 600px)").matches;
  const axisFontSize   = isMobile ? 10 : 12;
  const legendFontSize = isMobile ? 11 : 12;

  charts.bars = new Chart($("chart-bars"), {
    type: "bar",
    data: {
      labels: ["Smile #1", "Smile #2", "Smile Avg", "Eyes Close", "Eyes Open"],
      datasets: [{
        label: "Asymmetry",
        data: [r.smile1, r.smile2, r.smileAvg, r.closeAsym, r.openAsym].map((x) => +x.toFixed(3)),
        backgroundColor: ["#93c5fd", "#93c5fd", "#1f6feb", "#a78bfa", "#34d399"],
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, max: 1, grid: { color: "#eef1f6" }, ticks: { font: { size: axisFontSize } } },
        x: {
          grid: { display: false },
          ticks: {
            font: { size: axisFontSize },
            maxRotation: isMobile ? 40 : 0,
            minRotation: isMobile ? 40 : 0,
            autoSkip: false,
          },
        },
      },
    },
  });

  const pieData = [
    +(r.smileAvg * 0.5 * 100).toFixed(1),
    +(r.closeAsym * 0.25 * 100).toFixed(1),
    +(r.openAsym  * 0.25 * 100).toFixed(1),
  ];
  charts.pie = new Chart($("chart-pie"), {
    type: "doughnut",
    data: {
      labels: ["Smile (50%)", "Eyes Close (25%)", "Eyes Open (25%)"],
      datasets: [{ data: pieData, backgroundColor: ["#1f6feb", "#a78bfa", "#34d399"], borderWidth: 0 }],
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: "60%",
      plugins: {
        legend: {
          position: "bottom",
          labels: { boxWidth: 12, padding: 10, font: { size: legendFontSize } },
        },
      },
    },
  });

  charts.side = new Chart($("chart-side"), {
    type: "bar",
    data: {
      labels: ["Mouth corner (smile)", "Eye opening (wide)"],
      datasets: [
        { label: "Left side",  data: [+r.side.leftMouth.toFixed(2),  +(r.side.leftEye  * 100).toFixed(2)], backgroundColor: "#1f6feb", borderRadius: 6 },
        { label: "Right side", data: [+r.side.rightMouth.toFixed(2), +(r.side.rightEye * 100).toFixed(2)], backgroundColor: "#f59e0b", borderRadius: 6 },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { boxWidth: 12, padding: 10, font: { size: legendFontSize } },
        },
      },
      scales: {
        y: { beginAtZero: true, grid: { color: "#eef1f6" }, ticks: { font: { size: axisFontSize } } },
        x: { grid: { display: false }, ticks: { font: { size: axisFontSize } } },
      },
    },
  });
}

/* ---------- PDF download ---------- */
async function downloadReport() {
  const node = $("report-area");
  const canvas = await html2canvas(node, { scale: 2, backgroundColor: "#ffffff" });
  const img = canvas.toDataURL("image/png");
  const { jsPDF } = window.jspdf;
  const pdf = new jsPDF({ orientation: "portrait", unit: "pt", format: "a4" });
  const pageW = pdf.internal.pageSize.getWidth();
  const pageH = pdf.internal.pageSize.getHeight();
  const imgW  = pageW - 40;
  const imgH  = canvas.height * imgW / canvas.width;

  if (imgH < pageH - 40) {
    pdf.addImage(img, "PNG", 20, 20, imgW, imgH);
  } else {
    let y = 0;
    const pageHpx = (pageH - 40) * canvas.width / imgW;
    while (y < canvas.height) {
      const slice = document.createElement("canvas");
      slice.width  = canvas.width;
      slice.height = Math.min(pageHpx, canvas.height - y);
      slice.getContext("2d").drawImage(canvas, 0, y, canvas.width, slice.height, 0, 0, canvas.width, slice.height);
      const sliceImg = slice.toDataURL("image/png");
      if (y > 0) pdf.addPage();
      pdf.addImage(sliceImg, "PNG", 20, 20, imgW, slice.height * imgW / canvas.width);
      y += pageHpx;
    }
  }

  pdf.save(`NeuroScan-Report-${new Date().toISOString().slice(0, 10)}.pdf`);
}

/* ---------- Auto-start ---------- */
window.addEventListener("DOMContentLoaded", () => {
  // Hide results panel until test completes
  if (resultsPanel) resultsPanel.style.display = "none";
  startTest();
});
