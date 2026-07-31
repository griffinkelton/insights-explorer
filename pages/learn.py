"""Learn -- interactive, analyst-first learning experience for GA4 Insight Explorer.

Refactored for v0.2.0: side navigation replaces the old tab layout.  Each section
follows a Scrimba/Codebuff-inspired pedagogy:
    why this matters → see it in the app → trace the flow → try a challenge → check yourself

The page teaches analysts to use the app correctly, verify results, and understand
privacy boundaries -- not to read a reference manual.
"""

import streamlit as st

from components.learning_challenge import (
    render_before_you_conclude,
    render_learning_challenge,
)
from utils.styles import inject_custom_css, inject_favicon_meta

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Learn · GA4 Insight Explorer",
    page_icon="assets/favicon.ico",
)

# ── Theme-aware CSS + favicon ─────────────────────────────────────────────────
inject_custom_css(theme=st.session_state.get("theme", "dark"))
inject_favicon_meta(theme=st.session_state.get("theme", "dark"))

# ── Hero ─────────────────────────────────────────────────────────────────────
_theme = st.session_state.get("theme", "dark")
_hero_color = "#6b7280" if _theme == "light" else "#9898b0"
st.markdown(
    f"""
<div style="text-align:center;padding:2rem 1rem 1.5rem 1rem;">
    <div style="font-size:3.5rem;margin-bottom:0.5rem;">📚</div>
    <h1 style="font-size:2.2rem;margin-bottom:0.3rem;">
        Learn How Insight Explorer Works
    </h1>
    <p style="color:{_hero_color};font-size:1rem;max-width:700px;margin:0 auto;line-height:1.6;">
        Predict, inspect, and verify -- a guided journey from uploading data to
        making defensible analytical claims, with privacy principles at every step.
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ── Back to app ──────────────────────────────────────────────────────────────
st.page_link(
    "app.py",
    label="← Back to App",
    icon="🏠",
    help="Return to the GA4 Insight Explorer",
)

st.divider()

# ── Side navigation (replaces old tabs) ─────────────────────────────────────
SECTIONS = [
    "🚀 Start here",
    "📊 Follow the data",
    "📈 Explore & analyze",
    "🤖 Ask AI well",
    "🔐 Privacy & safety",
    "🏗️ How it is built",
    "🧩 Guided challenges",
    "🗺️ Where next",
]

nav_col, content_col = st.columns([1, 3])

with nav_col:
    st.markdown("### 🧭 Sections")
    selection = st.radio(
        "Choose a section:",
        SECTIONS,
        label_visibility="collapsed",
    )

with content_col:
    # ═══════════════════════════════════════════════════════════════════════
    # 1. START HERE
    # ═══════════════════════════════════════════════════════════════════════
    if selection == SECTIONS[0]:
        st.markdown("## 🚀 Start here -- what you can do in 60 seconds")

        st.markdown(
            """
        The **GA4 Insight Explorer** helps you turn analytics data into
        defensible insights.  In any session you can:

        1. **Upload** a CSV or XLSX export from GA4 -- or connect live via Google sign-in
        2. **Inspect** your data with filters, custom metrics, and quality checks
        3. **Analyze** with AI-generated summaries, charts, forecasts, and funnel views
        4. **Verify** results before acting on them -- every chart and number comes from real data

        > **Your first goal:** load data, narrow it intentionally, ask a bounded
        > question, and verify the answer against the active data.
        """
        )

        st.markdown("### The interface at a glance")
        st.code(
            """# The app has a sidebar + main area.
#
#   ┌─────────── Sidebar ───────────┐  ┌──── Main area ────────────────────┐
#   │  📂 Upload file               │  │  📊 Data preview (table + stats)  │
#   │  🔗 Connect GA4 live          │  │  ✨ Generate AI summary           │
#   │  🔍 Filter Data               │  │  💬 Chat with your data           │
#   │  ➕ Custom metrics            │  │  📈 Charts, forecast, funnels    │
#   │  🗑️  Clear data               │  │  📋 Export to Google Sheets      │
#   └────────────────────────────────┘  └──────────────────────────────────┘""",
            language="text",
        )

        st.markdown("### Try it now")
        st.markdown(
            """
        1. Go back to the app (🏠 button above)
        2. Upload a GA4 CSV export in the sidebar
        3. Inspect the data preview -- note the row count and columns
        4. Apply a filter to narrow your scope
        5. Click **Generate Summary** to see an AI overview
        6. Verify: does the summary match what the active data shows?
        """
        )

        st.markdown(
            '<div class="tip-box"><strong>💡 Key insight:</strong> Streamlit reruns '
            "your entire Python script on every interaction (button click, text input, "
            "etc.). That's why the app uses <code>st.session_state</code> to persist "
            "data across reruns and <code>@st.cache_data</code> to skip expensive "
            "recomputation.</div>",
            unsafe_allow_html=True,
        )

        with st.expander("🔬 Go deeper: how Streamlit drives the app", expanded=False):
            st.code(
                """# app.py -- simplified entry point
st.set_page_config(page_title="GA4 Insight Explorer", layout="wide")
inject_custom_css(theme=st.session_state.get("theme", "dark"))

# Initialize session state
if "data_context" not in st.session_state:
    st.session_state.data_context = None

# Render all UI
render_all()""",
                language="python",
            )
            st.caption(
                "See also: `app.py` (entrypoint), `components/sidebar.py` (upload & GA4 connect)"
            )

    # ═══════════════════════════════════════════════════════════════════════
    # 2. FOLLOW THE DATA
    # ═══════════════════════════════════════════════════════════════════════
    elif selection == SECTIONS[1]:
        st.markdown("## 📊 Follow the data -- the `DataContext` lifecycle")

        st.markdown(
            """
        **Why this matters:** If you don't know which data is being analyzed,
        you can't trust the results.  The app uses a three-layer model to make
        data scope explicit and prevent accidental data loss.
        """
        )

        st.markdown("### See it in this app")
        st.markdown(
            """
        | Layer | What it holds | When it changes |
        |---|---|---|
        | `raw_df` | The original uploaded or GA4-pulled data | **Never** -- it's the immutable ground truth |
        | `base_df` | The unfiltered analytical dataset (includes custom metrics) | When you add or remove custom metrics |
        | `active_df` | The currently analyzed view | When you apply, change, or clear filters |

        **The rule:** charts, summaries, forecasts, funnels, exports, and chat
        all analyze `active_df`.  Clearing filters restores `active_df` from
        `base_df`, not `raw_df` -- so custom metrics survive.
        """
        )

        st.markdown("### Trace the flow")
        st.code(
            """# Simplified flow from upload through filter to analysis

# 1. Factory creates the context (version=0)
ctx = create_context_from_upload(df, file_bytes)
#    raw_df    = original data (immutable)
#    base_df   = copy of raw_df
#    active_df = same as base (no filters yet)

# 2. Filter creates a new context (version=1)
ctx = with_filtered_data(ctx, filtered_rows, ("date:2025-06",))
#    active_df = June-only rows from base_df

# 3. Clear filters restores from base (version=2)
ctx = with_filters_cleared(ctx)
#    active_df = base_df again (all rows, custom metrics intact)""",
            language="python",
        )

        # ── Challenge L2: sequence ordering ─────────────────────────
        render_learning_challenge(
            key="learn.follow_data.lifecycle_order.v1",
            kind="sequence",
            title="Order the DataContext frames",
            prompt="Put these frames in their normal lifecycle order, from immutable source data to the frame that charts and chat analyze.",
            options=[
                {
                    "label": "raw_df",
                    "correct": True,
                    "feedback": "Correct -- raw_df is the original upload or GA4 response and is never filtered or mutated in place.",
                },
                {
                    "label": "base_df",
                    "correct": True,
                    "feedback": "Correct -- base_df is the unfiltered analytical dataset including any custom metrics.",
                },
                {
                    "label": "active_df",
                    "correct": True,
                    "feedback": "Correct -- active_df is the current analysis surface: filtered base_df, or base_df when no filter is active.",
                },
            ],
            explanation=(
                "The lifecycle is always `raw_df → base_df → active_df`.  "
                "`raw_df` is the immutable ground truth.  `base_df` is the "
                "unfiltered working base (custom metrics modify it).  "
                "`active_df` is what the UI should analyze -- it is filtered "
                "base_df when filters are active, otherwise base_df."
            ),
            success_criterion="You correctly ordered the three frames.",
            see_also_url="utils/data_context.py",
        )

        # ── Challenge L3: clear-filter prediction ───────────────────
        render_learning_challenge(
            key="learn.follow_data.clear_filter.v1",
            kind="predict",
            title="What happens when you clear a filter?",
            prompt=(
                "You load 1,000 rows, add a custom metric named `conversion_rate`, "
                "then filter to mobile traffic.  You click **Clear filters**.  "
                "Which frame should become the new `active_df`?"
            ),
            options=[
                {
                    "label": "raw_df -- the original upload",
                    "correct": False,
                    "feedback": "No -- clearing to raw_df would lose the custom metric column.",
                },
                {
                    "label": "base_df -- preserves custom metrics and restores all unfiltered rows",
                    "correct": True,
                    "feedback": "Correct! Clearing filters restores from base_df, so custom metrics survive.",
                },
                {
                    "label": "The prior filtered active_df -- preserve the user's context",
                    "correct": False,
                    "feedback": "No -- 'clearing' means removing the filter, not keeping the filtered result.",
                },
                {
                    "label": "None -- because no filter is active",
                    "correct": False,
                    "feedback": "No -- None is never a valid active dataset. An empty result (0 rows) is valid, but clearing filters restores the full base.",
                },
            ],
            explanation=(
                "Clearing filters restores `active_df` from `base_df`, not "
                "`raw_df`; otherwise custom-metric columns would disappear.  "
                "An empty result is valid when a filter produces no rows, but "
                "`None` is never a valid active dataset."
            ),
            success_criterion="You correctly identified that clearing filters restores from base_df.",
            see_also_url="utils/data_context.py",
        )

        st.caption("See also: `utils/data_context.py` (full module), `tests/test_data_context.py`")

    # ═══════════════════════════════════════════════════════════════════════
    # 3. EXPLORE & ANALYZE
    # ═══════════════════════════════════════════════════════════════════════
    elif selection == SECTIONS[2]:
        st.markdown("## 📈 Explore & analyze -- choose the right tool for the question")

        st.markdown(
            """
        **Why this matters:** Different questions require different analysis
        surfaces.  Knowing which to use -- and what each *cannot* tell you --
        prevents misinterpretation.
        """
        )

        st.markdown("### Your analysis toolkit")
        st.markdown(
            """
        | Question type | Best surface | Limitation |
        |---|---|---|
        | "Did sessions rise or fall?" | Trend chart or table | Does not explain *why* |
        | "Which pages lose people?" | Page-path funnel | Correlational, not causal |
        | "Is the data clean?" | Quality preview | Does not fix data issues |
        | "What might happen next?" | Linear trend projection | Extrapolation, not prediction |
        """
        )

        st.markdown("### Filters and custom metrics")
        st.markdown(
            """
        - **Filters** are always computed from `base_df` -- never from a
          previously filtered `active_df` -- so changing a date range doesn't
          accidentally compound.
        - **Custom metrics** rebuild `base_df` from `raw_df` and clear any
          active filters.  This prevents row loss: if you filtered to June
          and then added a metric, the new analytical base must include *all*
          rows, not just June.
        """
        )

        # ── Challenge L4: metric rebuild reasoning ─────────────────
        render_learning_challenge(
            key="learn.explore.metric_rebuild.v1",
            kind="predict",
            title="Why rebuild from raw_df?",
            prompt=(
                "You filter the data to June, then add `revenue_per_user`.  "
                "Why must the app rebuild metric data from `raw_df` rather "
                "than deriving it from the current `active_df`?"
            ),
            options=[
                {
                    "label": "To make filters faster",
                    "correct": False,
                    "feedback": "No -- the rebuild is about correctness, not performance.",
                },
                {
                    "label": "To preserve every original row and prevent June-only data from becoming the new unfiltered base",
                    "correct": True,
                    "feedback": "Correct! If the app derived from the filtered active_df, the June-only slice would become the permanent analytical base -- rows from other months would be lost.",
                },
                {
                    "label": "To avoid creating a new DataContext",
                    "correct": False,
                    "feedback": "No -- custom metrics always create a new DataContext (version bump).",
                },
                {
                    "label": "Because custom metrics cannot be used with filters",
                    "correct": False,
                    "feedback": "No -- you can filter after adding metrics. The rebuild just ensures the metric is calculated from the full dataset.",
                },
            ],
            explanation=(
                "Rebuilding from `raw_df` prevents accidental row loss and "
                "deterministically removes a deleted custom-metric column.  "
                "Applying custom metrics replaces `base_df`, resets `active_df` "
                "to that rebuilt base, and clears prior filters because they "
                "may no longer be meaningful."
            ),
            success_criterion="You identified that rebuilding from raw_df preserves all rows.",
            see_also_url="utils/data_context.py",
        )

        # ── Before you conclude checklist ──────────────────────────
        render_before_you_conclude()

        # ── Challenge L6: evidence check ──────────────────────────
        render_learning_challenge(
            key="learn.explore.evidence_check.v1",
            kind="evidence_check",
            title="What should you check before acting on this claim?",
            prompt=(
                'A summary says: "Mobile users caused the June conversion '
                'decline: their conversion rate fell 18%."  '
                "Select the **two most important checks** before acting."
            ),
            options=[
                {
                    "label": "Confirm the active date range, filters, metric definition, and denominator",
                    "correct": True,
                    "feedback": "Yes -- scope and metric definition are foundational. What exactly is being measured?",
                },
                {
                    "label": "Compare like-for-like periods and inspect the underlying row/sample count",
                    "correct": True,
                    "feedback": "Yes -- a fair comparison and adequate sample size are essential for interpretation.",
                },
                {
                    "label": "Change the chart colors to make the trend more visible",
                    "correct": False,
                    "feedback": "No -- visual styling doesn't validate the underlying data or logic.",
                },
                {
                    "label": "Assume the model identified causation because it found a pattern",
                    "correct": False,
                    "feedback": "No -- correlation is not causation. A pattern needs evidence, not assumption.",
                },
                {
                    "label": "Export the conclusion immediately before reviewing the data",
                    "correct": False,
                    "feedback": "No -- always review active data and verify before sharing results.",
                },
            ],
            explanation=(
                "A chart or summary can support a descriptive pattern, not "
                "causation by itself.  First confirm scope and metric "
                "definitions; then check fair comparison, volume, data "
                "quality, and plausible changes in tracking or traffic mix."
            ),
            success_criterion="You identified the two essential evidence checks.",
        )

        st.caption(
            "See also: `utils/charts.py`, `utils/forecasting.py`, `utils/funnels.py`, `components/data_preview.py`"
        )

    # ═══════════════════════════════════════════════════════════════════════
    # 4. ASK AI WELL
    # ═══════════════════════════════════════════════════════════════════════
    elif selection == SECTIONS[3]:
        st.markdown("## 🤖 Ask AI well -- bounded, verifiable questions")

        st.markdown(
            """
        **Why this matters:** Gemini can accelerate analysis, but it is an
        assistive tool -- not an authority.  Vague questions produce vague
        answers.  Well-scoped questions with verification routes produce
        defensible insights.
        """
        )

        st.markdown("### See it in this app")
        st.markdown(
            """
        The app sends Gemini a structured prompt containing:
        - Dataset description (row count, columns, date range)
        - Statistical summary (describe() for numeric columns)
        - Quality report findings
        - Your question
        - Optionally: chart suggestions (opt-in)

        The model does **not** receive raw row data, credentials, or internal state.
        """
        )

        st.markdown("### Trace the flow")
        st.code(
            """# Simplified prompt construction
def build_chat_prompt(active_df, stats, quality, user_question):
    return f'''
You are an analytics assistant.
Dataset: {len(active_df)} rows, {list(active_df.columns)}
Statistics: {stats}
Quality: {quality}
---
Question: {user_question}
'''""",
            language="python",
        )

        # ── Challenge L7: prompt improvement ────────────────────
        render_learning_challenge(
            key="learn.ai.prompt_improve.v1",
            kind="prompt_rewrite",
            title="Improve this prompt",
            prompt=(
                'A user types: **"Why did performance drop?"**  ' "Select the strongest rewrite."
            ),
            options=[
                {
                    "label": '"Analyze everything and tell me the most important insight."',
                    "correct": False,
                    "feedback": "Too broad -- no metric, time period, or scope. The model has no guidance.",
                },
                {
                    "label": '"Why was June bad?"',
                    "correct": False,
                    "feedback": "Still vague -- assumes June was 'bad' and doesn't specify what to compare or measure.",
                },
                {
                    "label": '"For 1-30 June vs 1-31 May, compare mobile and desktop conversion rate and sessions. Summarize the largest change in a short table, cite the values used, and suggest one chart I can verify it with."',
                    "correct": True,
                    "feedback": "Strong -- specifies metric, period, segment, output format, and verification route.",
                },
                {
                    "label": '"Find the root cause of the decline and tell me what campaign to stop."',
                    "correct": False,
                    "feedback": "Unsafe -- asks the model to claim causation without evidence and make a business decision.",
                },
            ],
            explanation=(
                "A useful analytical prompt defines the **metric**, **period**, "
                "**segment/comparison**, and **desired output**.  It requests "
                "evidence the learner can verify; it does not ask the model to "
                "claim a root cause without supporting data."
            ),
            success_criterion="You selected the prompt that specifies metric, period, segment, output, and verification.",
            see_also_url="utils/prompt_templates.py",
        )

        st.markdown("### What reaches Gemini -- and what doesn't")
        st.markdown(
            """
        **Sent to Gemini:** Dataset description, statistical summary,
        quality report, your question, opt-in chart suggestions.

        **Never sent:** Raw rows, credentials, OAuth tokens, internal
        app configuration, or proprietary source data.

        The chat UI shows **provider-reported token counts** after each
        response (input, output, thought, total).  No percentages, gauges,
        or fictional "quota remaining" estimates.
        """
        )

        render_before_you_conclude()

        st.caption("See also: `utils/gemini_client.py`, `utils/prompt_templates.py`, `SECURITY.md`")

    # ═══════════════════════════════════════════════════════════════════════
    # 5. PRIVACY & SAFETY
    # ═══════════════════════════════════════════════════════════════════════
    elif selection == SECTIONS[4]:
        st.markdown("## 🔐 Privacy & safety -- know the boundaries")

        st.markdown(
            """
        **Why this matters:** The app handles real analytics data.  Knowing
        what is safe to do -- and what isn't -- protects you and your data.
        """
        )

        st.markdown("### Session-only processing")
        st.markdown(
            """
        - All uploaded data lives **only in `st.session_state`** -- no
          server-side database, no persistent files, no caching to disk.
        - `DataContext` is the single owner of loaded, filtered, and
          custom-metric state.
        - Clearing data from the sidebar immediately removes the
          `DataContext` and all derived analysis state from the session.
        """
        )

        st.markdown("### OAuth & scopes")
        st.markdown(
            """
        - GA4: `analytics.readonly` -- read your data, cannot modify properties.
        - Google Drive: `drive.file` -- only access files the app creates (exports).
        - OAuth state is session-only and never persisted to disk.
        - An AST-based static guard rejects reintroduction of broader scopes.
        """
        )

        st.markdown("### Export safety")
        st.markdown(
            """
        - Exports happen only on **explicit user action** (clicking a button).
        - PDF exports sanitize spreadsheet values and text before embedding.
        - Errors never expose file paths, stack traces, API keys, or tokens.
        """
        )

        # ── Challenge L9: privacy scenario ──────────────────────
        render_learning_challenge(
            key="learn.privacy.scenario.v1",
            kind="scenario_choice",
            title="Safe, needs review, or unsafe?",
            prompt="Classify each action:",
            options=[
                {
                    "label": "Download a checked aggregate chart for a presentation",
                    "correct": False,
                    "feedback": "⚠️ Needs review -- confirm export scope, audience, and data sensitivity before sharing.",
                },
                {
                    "label": "Paste an API key or OAuth token into chat to troubleshoot",
                    "correct": False,
                    "feedback": "🚫 Unsafe -- credentials never belong in prompts, logs, or source code.",
                },
                {
                    "label": "Inspect active filters and result rows before exporting",
                    "correct": True,
                    "feedback": "✅ Safe -- scope review is a prerequisite for responsible sharing.",
                },
            ],
            explanation=(
                "**Safe** actions follow the app's privacy boundaries.  "
                "**Needs review** actions require checking scope, audience, "
                "and data sensitivity before proceeding.  **Unsafe** actions "
                "expose credentials or bypass security controls."
            ),
            success_criterion="You correctly distinguished safe, review-needed, and unsafe actions.",
            see_also_url="SECURITY.md",
        )

        st.caption(
            "See also: `SECURITY.md` (full security model), `utils/error_boundary.py`, `utils/ga4_client.py`"
        )

    # ═══════════════════════════════════════════════════════════════════════
    # 6. HOW IT IS BUILT
    # ═══════════════════════════════════════════════════════════════════════
    elif selection == SECTIONS[5]:
        st.markdown("## 🏗️ How it is built -- optional builder depth")

        st.markdown(
            """
        **Who this is for:** People curious about how the Streamlit app works
        and where to look before making a change.  You do **not** need this
        section to use the product successfully.
        """
        )

        st.markdown("### Repository map")
        st.markdown(
            """
        | Area | Owns | Start here when… |
        |---|---|---|
        | `app.py` | App startup, top-level assembly, page flow | Understanding how the app starts |
        | `pages/` | Standalone pages (this Learn page) | Changing the Learn experience |
        | `components/` | UI surfaces -- sidebar, preview, chat, summary, hero, onboarding | Changing upload/filter controls or presentation |
        | `utils/` | Data lifecycle, charts, GA4/Gemini/Drive clients, exports, safety | Changing how a feature *behaves* |
        | `tests/` | Regression protection and integration checks | Any observable behavior change |
        """
        )

        st.markdown("### The data contract (one annotated excerpt)")
        st.code(
            """# utils/data_context.py -- the app's data owner
@dataclass(frozen=True)
class DataContext:
    source_id: str          # Content-derived identity
    version: int            # Increments on analysis transitions
    raw_df: pd.DataFrame    # Immutable ground truth
    base_df: pd.DataFrame   # Unfiltered analytical base (custom metrics)
    active_df: pd.DataFrame # Current analysis surface (filtered or base)
    filters: FilterState = FilterState()  # Active filter metadata""",
            language="python",
        )
        st.markdown(
            """
        - `frozen=True` prevents replacing fields on the dataclass, but
          DataFrames are still mutable objects.  The real rule is discipline:
          **no caller mutates any of the three frames in place.**
        - Transitions return a **new** DataContext and increment `version`.
        - **Renderers read state; transitions create state.**
        """
        )

        st.markdown("### Follow one feature: a filter change")
        st.code(
            """# 1. Learner chooses a filter in components/sidebar.py
# 2. UI produces filtered DataFrame + descriptions
# 3. utils/data_context.py creates a replacement DataContext
#    - active_df = filtered data
#    - filters = active descriptions + row count
#    - version = incremented cache namespace
# 4. Preview, charts, summary, chat receive the new context
# 5. tests/test_data_context.py protects the contract""",
            language="text",
        )

        # ── Where do I look? challenge ───────────────────────────
        render_learning_challenge(
            key="learn.build.where_look.v1",
            kind="predict",
            title="Where would you look?",
            prompt=(
                'A bug report says: "After I clear filters, my custom metric '
                'disappears."  Where should you investigate first?'
            ),
            options=[
                {
                    "label": "Edit app.py because it renders the whole app",
                    "correct": False,
                    "feedback": "No -- app.py assembles the UI, it doesn't own the data lifecycle.",
                },
                {
                    "label": "Inspect utils/data_context.py, then add or review a focused lifecycle regression test",
                    "correct": True,
                    "feedback": "Correct -- the defect is in the data lifecycle. with_filters_cleared() must restore from base_df, not raw_df. The test belongs alongside the state contract.",
                },
                {
                    "label": "Edit pages/learn.py because it explains metrics",
                    "correct": False,
                    "feedback": "No -- Learn page content can be updated for clarity, but the bug is in the runtime behavior.",
                },
                {
                    "label": "Clear browser localStorage because it tracks onboarding",
                    "correct": False,
                    "feedback": "No -- localStorage is for onboarding persistence, not the data lifecycle.",
                },
            ],
            explanation=(
                "When data behavior is wrong, start at the contract that "
                "owns it -- `utils/data_context.py` -- and add a regression "
                "test.  The test stays with the state contract because this "
                "behavior must remain correct even if the UI is rearranged."
            ),
            success_criterion="You identified the correct owner of data lifecycle behavior.",
            see_also_url="utils/data_context.py",
        )

        st.markdown("### Safe-change recipe")
        st.markdown(
            """
        1. **Name the behavior.** "Clearing filters must retain custom-metric columns."
        2. **Find the owner.** Use the table above.
        3. **Read the contract and existing tests.**
        4. **Make the smallest coherent change.** Preserve `raw_df → base_df → active_df`.
        5. **Add or adjust a focused regression test.**
        6. **Run the focused test, then the full suite.**
        7. **Review privacy and security implications.**
        """
        )

        st.markdown("### Go deeper")
        st.markdown(
            """
        - `README.md` -- quick-start, features, API key setup
        - `ARCHITECTURE.md` -- module map, data flow, design rationale
        - `SECURITY.md` -- complete security model and threat model
        - `DOCUMENTATION_INDEX.md` -- index of every doc and spec
        - `utils/data_context.py` -- the data lifecycle implementation
        - `tests/test_data_context.py` -- regression coverage
        """
        )

    # ═══════════════════════════════════════════════════════════════════════
    # 7. GUIDED CHALLENGES
    # ═══════════════════════════════════════════════════════════════════════
    elif selection == SECTIONS[6]:
        st.markdown("## 🧩 Guided challenges -- put it all together")

        st.markdown(
            """
        Each mini-mission asks you to complete a realistic workflow in the app.
        There are no grades -- the goal is to practice the verification habit.
        """
        )

        st.markdown("### 🟢 Mission A -- First verified insight")
        st.markdown(
            """
        **Level:** Beginner

        Using an uploaded dataset:
        1. State the active date range and any filters
        2. Identify one metric and its unit
        3. Generate a chart or table that supports your observation
        4. Write one caveat or next validation step

        > **Completion:** You have an observation with context and evidence --
        > not merely a generated conclusion.
        """
        )

        st.markdown("### 🟡 Mission B -- Filter and metric integrity")
        st.markdown(
            """
        **Level:** Intermediate

        1. Add a custom metric (e.g. `sessions / users`)
        2. Filter to a segment of your data
        3. Clear the filter
        4. Confirm that the custom-metric column remains available on the
           restored unfiltered dataset

        > **Completion:** You've verified the `base_df → active_df` lifecycle
        > and confirmed that custom metrics survive filter operations.
        """
        )

        st.markdown("### 🔴 Mission C -- AI answer audit")
        st.markdown(
            """
        **Level:** Advanced

        1. Ask a bounded question in the chat
        2. Write an "evidence audit" with:
           - The active scope (date range, filters)
           - The chart or table you used to verify
           - One alternate explanation for the result
           - One follow-up question to investigate further

        > **Completion:** You used AI as an analytical assistant and retained
        > responsibility for validation.
        """
        )

        st.caption(
            "These missions use only your own data and the app -- no external grading or data collection."
        )

    # ═══════════════════════════════════════════════════════════════════════
    # 8. WHERE NEXT
    # ═══════════════════════════════════════════════════════════════════════
    elif selection == SECTIONS[7]:
        st.markdown("## 🗺️ Where next -- resources and roadmap")

        st.markdown("### Project docs")
        st.markdown(
            """
        | Document | What it covers |
        |---|---|
        | `README.md` | Quick-start guide, features, getting your API key |
        | `ARCHITECTURE.md` | Module map, data flow, design rationale |
        | `SECURITY.md` | Complete security model, scope justification, threat model |
        | `DOCUMENTATION_INDEX.md` | Index of every doc, plan, and spec in the repo |
        | `CHANGELOG.md` | Release history with key changes |
        | `IDEAS.md` | Feature backlog and future concepts |
        """
        )

        st.markdown("### Current plan")
        st.markdown(
            """
        - **🔵 v0.2.0 plan** -- architecture, accessibility, documentation, UX
        - **🔵 v0.2.0 implementation spec** -- detailed design decisions
        - **🔵 v0.2.0 release checklist** -- binary gates for the release
        """
        )

        st.markdown("### Test suite")
        st.code(
            """$ python -m pytest tests/ -q
... all tests passed

$ python -m pytest tests/ --cov=utils --cov=components --cov=pages --cov-report=term-missing""",
            language="bash",
        )

        st.markdown("### Contributing")
        st.markdown(
            """
        1. Create a branch from `main`
        2. Make your change and write tests
        3. Run `python -m pytest tests/ -q` -- all tests must pass
        4. Run `pre-commit run --all-files` -- linting must be clean
        5. Open a PR against `main`
        """
        )

        st.markdown(
            '<div class="tip-box"><strong>🎯 Ready?</strong> '
            "Go back to the app and try uploading your own GA4 data.  Every "
            "line of code is a lesson -- and the test suite has your back.</div>",
            unsafe_allow_html=True,
        )

# ── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Learn page -- analyst-first interactive experience.  "
    "Reflects v0.2.0 architecture.  No account, grading, or telemetry."
)
