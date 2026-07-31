"""Onboarding tour — frontend-owned custom component with localStorage persistence.

Renders a 3-step guided tour for first-time users via st.components.v1.html().
Completion state is persisted in the browser's localStorage under a versioned key:
    ga4_insight_explorer.onboarding.v1.completed

The component owns tour visibility, progression, Skip, and Replay.  Python receives
only a boolean indicating whether the tour is currently active.
"""

from __future__ import annotations

import streamlit.components.v1 as components
import streamlit as st

STORAGE_KEY = "ga4_insight_explorer.onboarding.v1.completed"

TOUR_STEPS = [
    {
        "icon": "📂",
        "title": "Upload your data",
        "body": (
            "Upload a CSV or XLSX file in the sidebar, "
            "or connect live via Google sign‑in to pull data "
            "directly from GA4."
        ),
    },
    {
        "icon": "✨",
        "title": "Generate an AI summary",
        "body": (
            "Click <strong>Generate Summary</strong> to get an instant overview "
            "of your dataset — date range, top pages, anomalies, and key metrics."
        ),
    },
    {
        "icon": "💬",
        "title": "Ask questions",
        "body": (
            "Type natural‑language questions in the chat box. "
            'Try: <em>"Which pages have the highest drop-off?"</em>'
        ),
    },
]


def _to_json(steps: list[dict[str, str]]) -> str:
    """Serialize tour steps to a compact JSON string for embedding in JS."""
    import json

    return json.dumps(steps, ensure_ascii=False)


# ── Self-contained tour HTML / JS / CSS ──────────────────────────────────────
# Inline in a single constant so that components.html() receives everything in
# one call.  The iframe is height=0 when already completed and height=420 when
# the tour is shown, avoiding a visible flash on the first rerun after the
# localStorage flag is read.

_TOUR_HTML = (
    """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  :root {
    --bg: #0f0f1a;
    --card: #1a1a26;
    --border: rgba(255,255,255,0.06);
    --text: #e0e0f0;
    --muted: #8888a0;
    --accent: #818cf8;
    --accent-hover: #6366f1;
    --success: #22c55e;
    --radius: 14px;
  }
  [data-theme="light"] {
    --bg: #f8f9fc;
    --card: #ffffff;
    --border: rgba(0,0,0,0.08);
    --text: #1e1e2e;
    --muted: #686880;
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: 1rem;
  }
  .tour-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 2rem 2rem 1.5rem;
    max-width: 520px;
    width: 100%;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0,0,0,0.15);
  }
  .step-icon { font-size: 3rem; margin-bottom: 0.5rem; }
  .step-badge {
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--accent);
    margin-bottom: 0.5rem;
  }
  .step-title { font-size: 1.25rem; font-weight: 700; margin-bottom: 0.75rem; }
  .step-body { font-size: 0.9rem; color: var(--muted); line-height: 1.6; margin-bottom: 1.25rem; }
  .progress-bar {
    height: 4px;
    background: var(--border);
    border-radius: 2px;
    margin-bottom: 1.5rem;
    overflow: hidden;
  }
  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--accent-hover));
    border-radius: 2px;
    transition: width 0.3s ease;
  }
  .actions { display: flex; gap: 0.75rem; justify-content: center; flex-wrap: wrap; }
  button {
    border: none;
    border-radius: 8px;
    padding: 0.55rem 1.25rem;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s, transform 0.1s;
  }
  button:active { transform: scale(0.97); }
  .btn-back { background: transparent; color: var(--muted); }
  .btn-back:hover { color: var(--text); }
  .btn-skip { background: transparent; color: var(--muted); }
  .btn-skip:hover { color: var(--text); }
  .btn-primary { background: var(--accent); color: #fff; }
  .btn-primary:hover { background: var(--accent-hover); }
  .done-icon { font-size: 3.5rem; margin-bottom: 0.75rem; }
  .done-title { font-size: 1.3rem; font-weight: 700; margin-bottom: 0.5rem; }
  .done-body { font-size: 0.9rem; color: var(--muted); margin-bottom: 1.5rem; }
</style>
</head>
<body>
<div id="root"></div>
<script>
  const STORAGE_KEY = '"""
    + STORAGE_KEY
    + """';
  const STEPS = """
    + _to_json(TOUR_STEPS)
    + """;

  let currentStep = 0;  // 0-based

  function isCompleted() { return localStorage.getItem(STORAGE_KEY) === 'true'; }
  function setCompleted() { localStorage.setItem(STORAGE_KEY, 'true'); }
  function clearCompleted() { localStorage.removeItem(STORAGE_KEY); }

  // Detect if the parent page is in light theme (via URL param or body attribute)
  function detectTheme() {
    try {
      const parentHtml = window.parent.document.documentElement;
      const theme = parentHtml.getAttribute('data-theme');
      if (theme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
      }
    } catch (_) { /* cross-origin — ignore */ }
  }

  function renderDone() {
    const root = document.getElementById('root');
    root.innerHTML = `
      <div class="tour-card">
        <div class="done-icon">🎉</div>
        <div class="done-title">You're all set!</div>
        <div class="done-body">Upload data in the sidebar to start exploring.</div>
      </div>`;
  }

  function renderStep(idx) {
    const step = STEPS[idx];
    const root = document.getElementById('root');
    const backBtn = idx > 0
      ? '<button class="btn-back" onclick="prev()">← Back</button>'
      : '<span></span>';
    const nextLabel = idx === STEPS.length - 1 ? 'Finish ✅' : 'Next →';

    root.innerHTML = `
      <div class="tour-card">
        <div class="step-icon">${step.icon}</div>
        <div class="step-badge">Step ${idx + 1} of ${STEPS.length}</div>
        <div class="step-title">${step.title}</div>
        <div class="step-body">${step.body}</div>
        <div class="progress-bar">
          <div class="progress-fill" style="width:${((idx + 1) / STEPS.length) * 100}%"></div>
        </div>
        <div class="actions">
          ${backBtn}
          <button class="btn-skip" onclick="skip()">Skip Tour</button>
          <button class="btn-primary" onclick="next()">${nextLabel}</button>
        </div>
      </div>`;
  }

  function next() {
    if (currentStep < STEPS.length - 1) {
      currentStep++;
      renderStep(currentStep);
    } else {
      finish();
    }
  }

  function prev() {
    if (currentStep > 0) {
      currentStep--;
      renderStep(currentStep);
    }
  }

  function skip() { finish(); }

  function finish() {
    setCompleted();
    renderDone();
    // Notify Streamlit that the tour is complete.
    if (window.Streamlit) { window.Streamlit.setComponentValue(true); }
  }

  // ── Entry point ──────────────────────────────────────────────────────
  detectTheme();

  if (isCompleted()) {
    renderDone();
    // Tell Streamlit immediately so Python can use height=0 on next render.
    if (window.Streamlit) { window.Streamlit.setComponentValue(true); }
  } else {
    renderStep(0);
    // Tour is active — tell Streamlit so Python can show it.
    if (window.Streamlit) { window.Streamlit.setComponentValue(false); }
  }

  // Listen for replay requests from the parent (Streamlit button).
  window.addEventListener('message', function(e) {
    if (e.data && e.data.type === 'replay_tour') {
      clearCompleted();
      currentStep = 0;
      renderStep(0);
      if (window.Streamlit) { window.Streamlit.setComponentValue(true); }
    }
  });
</script>
</body>
</html>"""
)


def render_onboarding_tour() -> bool:
    """Render the onboarding tour and return whether it should be dismissed.

    The tour is rendered inside an iframe via st.components.v1.html().
    JavaScript in the iframe manages localStorage persistence, Skip, Replay,
    and forwards the completion state back to Python.

    Returns:
        True if the tour has been completed (or was already completed in a
        previous session).  False while the user is still stepping through.
    """
    tour_done = st.session_state.get("_tour_completed", False)
    height = 0 if tour_done else 420

    result = components.html(_TOUR_HTML, height=height, scrolling=False)

    if result is True and not tour_done:
        st.session_state._tour_completed = True
        st.rerun()

    return tour_done
