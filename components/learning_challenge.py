"""Interactive learning challenges — Scrimba/Codebuff-inspired pedagogy.

Provides a reusable `render_learning_challenge()` component for the Learn page.
Each challenge requires a learner action (predict, sequence, rewrite, check,
classify, or read code), gives immediate specific feedback, and uses
text/icons rather than color alone to communicate correctness.

State is session-only (st.session_state); no grades, persistence, telemetry,
or external services.  Every challenge is keyboard-operable.
"""

from __future__ import annotations

from typing import Literal

import streamlit as st

ChallengeKind = Literal[
    "predict",
    "sequence",
    "prompt_rewrite",
    "evidence_check",
    "scenario_choice",
    "code_reading",
]


def render_learning_challenge(
    key: str,
    kind: ChallengeKind,
    title: str,
    prompt: str,
    options: list[dict[str, str]],
    explanation: str = "",
    success_criterion: str = "",
    see_also_url: str | None = None,
) -> None:
    """Render a single interactive learning challenge.

    Args:
        key: Stable namespaced key, e.g. ``learn.follow_data.filter_clear.v1``.
             Used for session-state isolation — do not reuse across challenges.
        kind: The challenge type.  Determines the UI affordance:
              ``predict``        → radio choice with immediate reveal
              ``sequence``       → radio for each ordered position
              ``prompt_rewrite`` → radio choice picking strongest rewrite
              ``evidence_check`` → checkbox multi-select for missing evidence
              ``scenario_choice``→ radio choice with safe/needs-review/unsafe labels
              ``code_reading``   → radio choice interpreting a code excerpt
        title: Short challenge heading displayed above the prompt.
        prompt: The question or scenario presented to the learner.
        options: List of dicts, each with keys:
                 - ``label``   (str) — display text
                 - ``correct`` (bool) — whether this option is the right answer
                 - ``feedback``(str, optional) — shown after selection
        explanation: Full explanation revealed after the learner attempts.
        success_criterion: One-sentence observable check (displayed on success).
        see_also_url: Optional doc/source link to show after the explanation.
    """
    solved_key = f"challenge_{key}_solved"
    attempted_key = f"challenge_{key}_attempted"

    if solved_key not in st.session_state:
        st.session_state[solved_key] = False
    if attempted_key not in st.session_state:
        st.session_state[attempted_key] = False

    solved = st.session_state[solved_key]
    attempted = st.session_state[attempted_key]

    # ── Card wrapper ────────────────────────────────────────────────────
    # State styling lives in CSS (.challenge-card--solved/--attempted) so
    # both themes stay legible — the old inline white border and green
    # background were near-invisible on white (A2, light-mode spec).
    # The base .challenge-card rule styles the "default" (unsolved) state.
    state_cls = "solved" if solved else "attempted" if attempted else "default"
    st.markdown(
        f"""<div class="challenge-card challenge-card--{state_cls}"
        id="challenge-{key}">""",
        unsafe_allow_html=True,
    )

    # ── Header ──────────────────────────────────────────────────────────
    icon = {
        "predict": "🔮",
        "sequence": "🔗",
        "prompt_rewrite": "✏️",
        "evidence_check": "🔍",
        "scenario_choice": "🛡️",
        "code_reading": "📖",
    }.get(kind, "❓")
    kind_label = {
        "predict": "Predict",
        "sequence": "Put in order",
        "prompt_rewrite": "Improve the prompt",
        "evidence_check": "Check the evidence",
        "scenario_choice": "Safe or unsafe?",
        "code_reading": "Read the code",
    }.get(kind, "Challenge")

    if solved:
        st.markdown(f"#### {icon} ✅ {title}")
    else:
        st.markdown(f"#### {icon} {title}")
    st.caption(f"_{kind_label}_")
    st.markdown(prompt)

    # ── Interaction (by kind) ───────────────────────────────────────────
    selected_label: str | None = None
    is_correct = False

    if kind in ("predict", "prompt_rewrite", "scenario_choice", "code_reading"):
        # Radio-button choice
        labels = [opt["label"] for opt in options]
        choice = st.radio(
            "Choose one:",
            labels,
            key=f"{key}_radio",
            disabled=solved,
            label_visibility="visible",
        )
        if choice is not None:
            selected_label = choice
            matching = [o for o in options if o["label"] == choice]
            is_correct = matching[0]["correct"] if matching else False

    elif kind == "evidence_check":
        # Checkbox multi-select
        selected = []
        for i, opt in enumerate(options):
            checked = st.checkbox(opt["label"], key=f"{key}_cb_{i}", disabled=solved)
            if checked:
                selected.append(opt["label"])
        if selected:
            selected_label = ", ".join(selected)
            correct_labels = {o["label"] for o in options if o["correct"]}
            is_correct = set(selected) == correct_labels
            attempted = bool(selected)
        expected_count = len([o for o in options if o["correct"]])
        st.caption(f"Select exactly {expected_count}.")

    elif kind == "sequence":
        # Three separate radios for ordering
        items = [opt["label"] for opt in options]
        correct_order = [opt["label"] for opt in options if opt["correct"]]
        positions = ["First", "Second", "Third", "Fourth", "Fifth"]
        chosen = []
        for i in range(len(items)):
            pos = positions[i]
            c = st.radio(
                pos,
                items,
                key=f"{key}_seq_{i}",
                disabled=solved,
                label_visibility="visible",
                index=None,
            )
            chosen.append(c)
        if all(c is not None for c in chosen):
            selected_label = " → ".join(chosen)
            is_correct = chosen == correct_order
            attempted = True

    # ── Submit / Check button ──────────────────────────────────────────
    if not solved and not attempted:
        col_a, col_b = st.columns([1, 3])
        with col_a:
            if st.button("Check answer", key=f"{key}_check", type="primary"):
                if selected_label is not None:
                    st.session_state[attempted_key] = True
                else:
                    st.warning("Select an answer first.")
                    return
                if is_correct:
                    st.session_state[solved_key] = True
                st.rerun()

    # ── Show answer (accessibility: always available) ───────────────────
    if not solved:
        with st.expander("👁️ Show answer", expanded=False):
            _render_explanation(options, explanation)

    # ── Post-attempt feedback ───────────────────────────────────────────
    if attempted or solved:
        if is_correct or solved:
            st.success(success_criterion or "Correct!")
            _render_explanation(options, explanation)
            if see_also_url:
                st.caption(f"📎 See also: {see_also_url}")
        else:
            st.error("Not quite — review the explanation below.")
            _render_explanation(options, explanation)

        # Retry affordance (only if not yet solved)
        if not solved:
            if st.button("🔄 Try again", key=f"{key}_retry"):
                st.session_state[attempted_key] = False
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def _render_explanation(options: list[dict[str, str]], explanation: str) -> None:
    """Render the full explanation with per-option feedback."""
    if explanation:
        st.markdown("##### Explanation")
        st.markdown(explanation)

    # Per-option feedback
    for opt in options:
        if opt.get("feedback"):
            marker = "✅" if opt.get("correct") else "❌"
            st.caption(f"{marker} **{opt['label']}** — {opt['feedback']}")


def render_before_you_conclude() -> None:
    """Render the reusable 'Before you conclude' verification checklist.

    This appears in chart, summary, and prompt lessons to normalize analytical
    skepticism.  It does NOT call Gemini or store answers.
    """
    with st.expander("📋 Before you conclude — verification checklist", expanded=False):
        st.markdown(
            """
        Before acting on an insight, check:

        - ✅ **Active scope:** What date range and filters are applied?
        - ✅ **Metric definition:** What exactly is being counted or averaged?
        - ✅ **Fair comparison:** Are the periods, segments, or groups equally comparable?
        - ✅ **Sample size:** Are row counts large enough to interpret reliably?
        - ✅ **Data quality:** Could tracking changes, delays, or missing data affect the result?
        - ✅ **Correlation vs. causation:** Does the evidence support a causal claim, or only a pattern?
        - ✅ **Reproducible:** Can I verify the result with a chart, table, or direct calculation?

        > A chart or AI summary can *suggest* a pattern.  Verification turns it into a defensible insight.
        """
        )
