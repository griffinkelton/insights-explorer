"""Onboarding tour — browser-persisted onboarding via st.components.v1.html().

Renders a 3-step guided tour for first-time users.  Completion state is persisted
in the browser's localStorage under a versioned key:
    ga4_insight_explorer.onboarding.v1.completed

The iframe wholly owns tour visibility, progression, Skip, and its own completion
state.  Python passes a one-shot ``force_replay`` render flag to clear the key and
restart the tour; otherwise Python has no knowledge of localStorage.

``st.components.v1.html()`` is an HTML-embedding primitive — it does NOT provide a
bidirectional component-value channel.  The iframe does not rely on
``setComponentValue()`` or ``postMessage`` for state reporting.

Design note (v0.2.0)
--------------------
``st.components.v1.html()`` was deliberately chosen over a declared Streamlit
custom component for this browser-owned, non-telemetry tour:

- The tour has no need to report state back to Python — it reads and writes
  only localStorage, which Python cannot inspect synchronously anyway.
- ``components.html()`` avoids a frontend build pipeline, npm dependencies,
  and the complexity of a declared bidirectional component for what is
  fundamentally a self-contained UI widget.
- The trade-off is that Python cannot dynamically hide the iframe for
  already-completed users; the completed card renders at 420 px.

Escalation path: if a future phase requires Python to reliably receive
completion state, dynamically remove the iframe, record analytics, or
coordinate tour state with other app UI, migrate to a declared Streamlit
custom component with ``Streamlit.setComponentValue({ completed: true })``
and use a replay nonce (not a boolean) for repeated replay clicks.
"""

from __future__ import annotations

import json

import streamlit.components.v1 as components
import streamlit as st

STORAGE_KEY = "ga4_insight_explorer.onboarding.v1.completed"

TOUR_STEPS = [
    {
        "icon": "📂",
        "title": "Upload your data",
        "body": (
            "Upload a CSV or XLSX file in the sidebar, "
            "or connect live via Google sign-in to pull data "
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
            "Type natural-language questions in the chat box. "
            'Try: <em>"Which pages have the highest drop-off?"</em>'
        ),
    },
]

# ── HTML template (__FORCE_REPLAY__ replaced at render time) ─────────────────
# Using a template with a sentinel avoids recomputing the entire HTML constant
# on every call; only the boolean literal is swapped in.

_TOUR_HTML_TEMPLATE = """<!DOCTYPE html>
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
    /* Aligned to the app's light accent tokens (styles.py) for contrast on white */
    --accent: #4f46e5;
    --accent-hover: #6366f1;
    --success: #059669;
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
    transition: background 0.15s, transform 0.1s, outline 0.15s;
  }
  button:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
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
  const STORAGE_KEY = '__STORAGE_KEY__';
  const STEPS = __STEPS_JSON__;
  const FORCE_REPLAY = __FORCE_REPLAY__;

  let currentStep = 0;

  function isCompleted() { return localStorage.getItem(STORAGE_KEY) === 'true'; }
  function setCompleted() { localStorage.setItem(STORAGE_KEY, 'true'); }
  function clearCompleted() { localStorage.removeItem(STORAGE_KEY); }

  function syncTheme() {
    try {
      var parentHtml = window.parent.document.documentElement;
      var theme = parentHtml.getAttribute('data-theme');
      if (theme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
      } else {
        document.documentElement.removeAttribute('data-theme');
      }
    } catch (_) { /* cross-origin — ignore */ }
  }

  function focusTitle() {
    var title = document.querySelector('.step-title');
    if (title) { title.setAttribute('tabindex', '-1'); title.focus(); }
  }

  function renderDone() {
    var root = document.getElementById('root');
    root.innerHTML =
      '<div class="tour-card">' +
        '<div class="done-icon">🎉</div>' +
        '<div class="done-title">Tour completed</div>' +
        '<div class="done-body">Upload data in the sidebar to start exploring. Replay anytime from the hero.</div>' +
      '</div>';
    focusTitle();
  }

  function renderStep(idx) {
    var step = STEPS[idx];
    var root = document.getElementById('root');
    var backBtn = idx > 0
      ? '<button class="btn-back" onclick="prev()">← Back</button>'
      : '<span></span>';
    var nextLabel = idx === STEPS.length - 1 ? 'Finish' : 'Next →';
    var pct = ((idx + 1) / STEPS.length) * 100;

    root.innerHTML =
      '<div class="tour-card">' +
        '<div class="step-icon">' + step.icon + '</div>' +
        '<div class="step-badge">Step ' + (idx + 1) + ' of ' + STEPS.length + '</div>' +
        '<div class="step-title">' + step.title + '</div>' +
        '<div class="step-body">' + step.body + '</div>' +
        '<div class="progress-bar" role="progressbar" aria-valuenow="' + (idx + 1) + '" aria-valuemin="1" aria-valuemax="' + STEPS.length + '">' +
          '<div class="progress-fill" style="width:' + pct + '%"></div>' +
        '</div>' +
        '<div class="actions">' +
          backBtn +
          '<button class="btn-skip" onclick="skip()">Skip Tour</button>' +
          '<button class="btn-primary" onclick="next()">' + nextLabel + '</button>' +
        '</div>' +
      '</div>';
    focusTitle();
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
  }

  // ── Entry point ──────────────────────────────────────────────────────
  // Sync once on load, then keep following the app toggle live.
  // st.components.v1.html() only reloads the iframe when the HTML payload
  // changes, and a theme toggle leaves the payload byte-identical — so a
  // one-shot detect would go stale.  The MutationObserver propagates the
  // parent's html[data-theme] flip without any reload (C1, light-mode
  // spec §3.3).
  syncTheme();
  try {
    var themeObserver = new MutationObserver(syncTheme);
    themeObserver.observe(window.parent.document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    });
  } catch (_) { /* cross-origin — ignore */ }

  if (FORCE_REPLAY) {
    clearCompleted();
    currentStep = 0;
  }

  if (isCompleted()) {
    renderDone();
  } else {
    renderStep(0);
  }
</script>
</body>
</html>"""


def _tour_html(*, force_replay: bool) -> str:
    """Build the iframe HTML, injecting the one-shot replay flag."""
    return (
        _TOUR_HTML_TEMPLATE.replace("__STORAGE_KEY__", STORAGE_KEY)
        .replace("__STEPS_JSON__", json.dumps(TOUR_STEPS, ensure_ascii=False))
        .replace("__FORCE_REPLAY__", "true" if force_replay else "false")
    )


def render_onboarding_tour() -> None:
    """Render the browser-persisted onboarding tour.

    The iframe wholly owns visibility and completion.  Python passes a
    one-shot ``_tour_replay_requested`` flag (consumed via ``pop``) to
    clear the localStorage key and restart the tour at step 1.

    ``st.components.v1.html()`` is an HTML-embedding primitive — it does
    NOT return a component value.  The iframe does not attempt to report
    state back to Python via ``setComponentValue`` or ``postMessage``.
    """
    force_replay = st.session_state.pop("_tour_replay_requested", False)

    components.html(
        _tour_html(force_replay=force_replay),
        height=420,
        scrolling=False,
    )
