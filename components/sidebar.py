from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import pandas as pd
import streamlit as st

if TYPE_CHECKING:
    from utils.data_context import GA4RequestMetadata

from utils.data_loader import (
    ColumnType,
    assess_data_quality,
    detect_column_types,
    get_dataset_stats,
    load_file,
    validate_columns,
)
from utils.ga4_client import (
    credentials_from_dict,
    get_auth_url,
    needs_scope_migration,
    pull_ga4_report,
)
from utils.data_context import (
    create_context_from_ga4,
    create_context_from_upload,
    rebuild_metrics_context,
)
from utils.session import clear_data

REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8501")
logger = logging.getLogger(__name__)


def _populate_data_state(
    df: pd.DataFrame,
    source: str,
    missing: list[str],
    file_bytes: bytes | None = None,
    ga4_start_date: str | None = None,
    ga4_metadata: GA4RequestMetadata | None = None,
    display_name: str = "",
) -> None:
    """Populate session state with loaded data — shared by upload and GA4 paths.

    v0.2.0: Creates a DataContext — the sole owner of loaded, filtered, and
    custom-metric state.

    Args:
        df: The loaded DataFrame.
        source: "file" or "ga4".
        missing: List of expected-but-missing column names.
        file_bytes: Raw file bytes for content-derived source_id (upload only).
        ga4_start_date: GA4 date range start e.g. "7daysAgo" (GA4 only).
        display_name: Human-readable filename for provenance (upload only).
    """
    # Reset custom metrics when loading new data (columns may differ)
    st.session_state.custom_metrics = {}

    date_cols = [c for c in df.columns if "date" in c.lower()]
    if date_cols:
        try:
            df[date_cols[0]] = pd.to_datetime(df[date_cols[0]], errors="coerce")
        except Exception:
            pass  # Mixed-format or invalid dates are expected — coerce handles them gracefully
    st.session_state.missing_columns = missing
    st.session_state.stats = get_dataset_stats(df)
    st.session_state.stats["missing_columns"] = missing
    st.session_state.quality_report = assess_data_quality(df, missing)
    st.session_state.summary = None
    st.session_state.chat_history = []
    st.session_state.data_source = source
    st.session_state.data_cleared = False
    # Auto-dismiss onboarding tour when data is loaded

    # v0.2.0: Create DataContext — sole owner of data state
    if source == "ga4":
        if ga4_metadata is not None:
            st.session_state.data_context = create_context_from_ga4(
                df, property_id="", metadata=ga4_metadata
            )
        else:
            st.session_state.data_context = create_context_from_ga4(
                df,
                st.session_state.get("ga4_property_id", "unknown"),
                date_range=(ga4_start_date, "today") if ga4_start_date else None,
            )
    else:
        st.session_state.data_context = create_context_from_upload(
            df, file_bytes, display_name=display_name
        )


def render_sidebar() -> None:
    """Render the full sidebar and return the uploaded file (if any)."""
    with st.sidebar:
        _render_logo()
        st.divider()
        uploaded_file = _render_file_uploader()
        st.divider()
        _render_ga4_connect()
        st.divider()
        _render_privacy_notice()
        _render_clear_button()
        _render_compare_controls()
        _render_custom_metrics()
        _render_model_selector()
        _render_api_counter()
        _render_learn_link()
        _render_theme_toggle()
        _render_footer()

    # Process uploaded file (after sidebar renders so errors show in main area)
    if uploaded_file is not None:
        _process_uploaded_file(uploaded_file)


def _render_logo() -> None:
    """Render the app logo and title in the sidebar."""
    theme = st.session_state.get("theme", "dark")
    title_color = "#1f2937" if theme == "light" else "#f0f0f5"
    subtitle_color = "#6b7280" if theme == "light" else "#9898b0"
    st.markdown(
        f"""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.5rem;">
        <div style="width:38px;height:38px;border-radius:12px;background:linear-gradient(135deg,#6366f1,#8b5cf6);
                    display:flex;align-items:center;justify-content:center;font-size:1.2rem;">📊</div>
        <div>
            <div style="font-weight:700;font-size:1.1rem;color:{title_color};line-height:1.3;">Insight Explorer</div>
            <div style="font-size:0.75rem;color:{subtitle_color};">GA4 Analytics + AI</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def _render_file_uploader():
    """Render the file uploader widget. Returns the uploaded file or None."""
    return st.file_uploader(
        "Upload GA4 Export",
        type=["csv", "xlsx"],
        help="De-identified Google Analytics 4 export file (CSV or XLSX).",
    )


def _render_ga4_connect() -> None:
    """Render the GA4 live connection: sign-in, property ID, pull data, disconnect."""
    theme = st.session_state.get("theme", "dark")
    section_color = "#1f2937" if theme == "light" else "#f0f0f5"
    st.markdown(
        f'<p style="font-size:0.8rem;font-weight:600;color:{section_color};margin-bottom:0.3rem;">'
        f"🔗 Google Analytics 4 (Live)</p>",
        unsafe_allow_html=True,
    )

    if st.session_state.ga4_creds is None:
        # Not connected — show sign-in
        if st.button("🔐 Sign in with Google", use_container_width=True, type="primary"):
            try:
                auth_url, _ = get_auth_url(REDIRECT_URI)
                st.markdown(
                    f'<meta http-equiv="refresh" content="0;url={auth_url}">'
                    f'<p style="color:#9898b0;font-size:0.85rem;">Redirecting to Google...</p>'
                    f'<p style="color:#686880;font-size:0.75rem;">'
                    f'If not redirected, <a href="{auth_url}" style="color:#818cf8;">click here</a></p>',
                    unsafe_allow_html=True,
                )
                st.stop()
            except FileNotFoundError:
                st.error("Configuration file not found. Please check your OAuth setup.")
                logger.warning("OAuth configuration file missing", exc_info=True)

        st.caption(
            "Connect live to your GA4 property. "
            "Requires a [GCP OAuth client](https://console.cloud.google.com/apis/credentials) "
            "with `http://localhost:8501` as an authorized redirect URI."
        )
    else:
        # ── Scope migration banner ──
        creds = credentials_from_dict(st.session_state.ga4_creds)
        if needs_scope_migration(creds):
            from utils.ga4_client import _revoke_token

            st.warning(
                "🔐 We've updated OAuth permissions for v0.1.0. "
                "Please reconnect your Google account to continue."
            )
            if st.button("🔄 Reconnect Google Account", use_container_width=True):
                _revoke_token(creds)
                st.session_state.ga4_creds = None
                st.rerun()
            # Return early — don't show connected controls until migration done
            return

        # Connected — show controls
        st.success("✅ Connected to Google")

        property_id = st.text_input(
            "GA4 Property ID",
            value=st.session_state.ga4_property_id,
            placeholder="e.g., 123456789",
            help="Numeric property ID from GA4 Admin > Property Settings",
        )
        st.session_state.ga4_property_id = property_id

        # Validate property ID before allowing pull
        if property_id and not property_id.strip().isdigit():
            st.error("GA4 Property ID must contain only digits.")

        date_range = st.selectbox(
            "Date range",
            options=["7 days", "30 days", "90 days"],
            index=2,
            key="ga4_date_range",
            help="How far back to pull data from GA4.",
        )
        start_date_map = {"7 days": "7daysAgo", "30 days": "30daysAgo", "90 days": "90daysAgo"}
        start_date = start_date_map[date_range]

        col_pull, col_disc = st.columns(2)
        with col_pull:
            if st.button("📥 Pull Data", use_container_width=True, type="primary"):
                if not property_id:
                    st.error("Please enter your GA4 Property ID first.")
                elif not property_id.strip().isdigit():
                    st.error("GA4 Property ID must contain only digits.")
                else:
                    with st.spinner(f"Fetching {date_range} of data from Google Analytics..."):
                        try:
                            creds = credentials_from_dict(st.session_state.ga4_creds)
                            df, ga4_metadata = pull_ga4_report(
                                creds, property_id, start_date=start_date
                            )
                            if df.empty:
                                st.error("No data returned. Check your Property ID and date range.")
                            else:
                                missing = validate_columns(df)
                                if missing:
                                    st.warning(f"⚠️ Missing columns: {', '.join(missing)}")

                                _populate_data_state(
                                    df,
                                    "ga4",
                                    missing,
                                    ga4_start_date=start_date,
                                    ga4_metadata=ga4_metadata,
                                )
                                st.rerun()
                        except Exception:
                            st.error(
                                "Failed to pull GA4 data. Check your Property ID and try again."
                            )
                            logger.warning("GA4 pull error", exc_info=True)

        with col_disc:
            if st.button("✕ Disconnect", use_container_width=True):
                st.session_state.ga4_creds = None
                st.session_state.ga4_property_id = ""
                if st.session_state.data_source == "ga4":
                    clear_data()
                st.rerun()


def _render_privacy_notice() -> None:
    """Render the privacy disclaimer card."""
    theme = st.session_state.get("theme", "dark")
    privacy_bg = "rgba(79,70,229,0.04)" if theme == "light" else "rgba(99,102,241,0.06)"
    privacy_border = "rgba(79,70,229,0.1)" if theme == "light" else "rgba(99,102,241,0.12)"
    privacy_text = "#6b7280" if theme == "light" else "#9898b0"
    st.markdown(
        f"""
    <div style="background:{privacy_bg};border:1px solid {privacy_border};
                border-radius:12px;padding:0.9rem 1rem;margin:0.5rem 0;">
        <div style="font-size:0.78rem;color:{privacy_text};line-height:1.5;">
            🔒 <b>Privacy</b><br>
            Uploaded analytics data is processed in the active session. When you use AI
            features, the app sends the relevant prompt and selected data context to
            Google's Gemini API. Processing is subject to the applicable Google terms
            for this application's Gemini configuration. OAuth uses temporary
            authorization state stored briefly to complete sign-in. Exports and Drive
            actions occur only when you choose them.
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def _render_clear_button() -> None:
    """Render the Clear Data button. Only shown when data is loaded.

    v0.2.0: DataContext is the sole data-state owner.

    FIX (BUG-005): Uses `if st.button` pattern instead of `on_click=clear_data`
    to comply with the anti-pattern guard.
    """
    if st.session_state.data_context is not None:
        if st.button(
            "🗑️ Clear Data",
            use_container_width=True,
            type="secondary",
        ):
            clear_data()
            st.rerun()


def _render_model_selector() -> None:
    """Render the AI model selector with tooltips."""
    from utils.gemini_client import AVAILABLE_MODELS, DEFAULT_MODEL

    st.divider()
    theme = st.session_state.get("theme", "dark")
    section_color = "#1f2937" if theme == "light" else "#f0f0f5"
    st.markdown(
        f'<p style="font-size:0.8rem;font-weight:600;color:{section_color};margin-bottom:0.3rem;">'
        f"🤖 AI Model</p>",
        unsafe_allow_html=True,
    )

    model_keys = list(AVAILABLE_MODELS.keys())
    model_labels = [AVAILABLE_MODELS[k]["label"] for k in model_keys]

    # Default to gemini-2.5-flash index
    current_model = st.session_state.get("selected_model", DEFAULT_MODEL)
    try:
        current_idx = model_keys.index(current_model)
    except ValueError:
        current_idx = 0

    selected_label = st.selectbox(
        "Model",
        options=model_labels,
        index=current_idx,
        key="model_selector",
        label_visibility="collapsed",
    )

    # Map back to model key
    selected_key = model_keys[model_labels.index(selected_label)]
    st.session_state.selected_model = selected_key

    # Show tooltip/info for selected model
    model_info = AVAILABLE_MODELS[selected_key]
    tier_color = "#059669" if model_info["tier"] == "Free" else "#d97706"
    st.markdown(
        f'<div style="background:var(--bg-card);border:1px solid var(--border);'
        f'border-radius:8px;padding:0.6rem 0.8rem;margin-top:0.3rem;">'
        f'<div style="font-size:0.72rem;color:var(--text-secondary);line-height:1.5;">'
        f'{model_info["tooltip"]}</div>'
        f'<div style="display:flex;gap:0.8rem;margin-top:0.4rem;">'
        f'<span style="font-size:0.65rem;color:{tier_color};font-weight:600;">'
        f'{model_info["tier"]}</span>'
        f'<span style="font-size:0.65rem;color:var(--text-muted);">'
        f'{model_info["context_window"]} context</span>'
        f"</div></div>",
        unsafe_allow_html=True,
    )


def _render_api_counter() -> None:
    """Render API call counter (only when calls have been made)."""
    success_count = st.session_state.get("api_success_count", 0)
    if success_count > 0:
        st.caption(f"🔢 API calls this session: {success_count}")


def _render_footer() -> None:
    """Render the sidebar footer."""
    st.divider()
    theme = st.session_state.get("theme", "dark")
    footer_color = "#9ca3af" if theme == "light" else "#686880"
    st.markdown(
        f'<div style="font-size:0.72rem;color:{footer_color};">Built with ❤️ using Streamlit + Gemini</div>',
        unsafe_allow_html=True,
    )


def _render_theme_toggle() -> None:
    """Render the theme toggle button at the bottom of the sidebar."""
    current = st.session_state.get("theme", "dark")
    new_theme = "light" if current == "dark" else "dark"
    label = "☀️ Light Mode" if current == "dark" else "🌙 Dark Mode"

    st.divider()
    if st.button(label, use_container_width=True, key="theme_toggle"):
        st.session_state.theme = new_theme
        st.rerun()


def _render_custom_metrics() -> None:
    """Render custom metric builder — formula bar for derived columns.

    v0.2.0: DataContext is the sole data-state owner. Custom metrics derive
    from raw_df (via rebuild_metrics_context), never from active_df.
    """
    if st.session_state.data_context is None:
        return

    st.divider()
    theme = st.session_state.get("theme", "dark")
    metrics_color = "#1f2937" if theme == "light" else "#f0f0f5"
    st.markdown(
        f'<p style="font-size:0.8rem;font-weight:600;color:{metrics_color};margin-bottom:0.3rem;">'
        f"🧮 Custom Metrics</p>",
        unsafe_allow_html=True,
    )

    # List existing custom metrics with delete buttons
    metrics = st.session_state.custom_metrics
    if metrics:
        for name in list(metrics.keys()):
            col_name, col_del = st.columns([5, 1])
            with col_name:
                st.caption(f"**{name}** = `{metrics[name]}`")
            with col_del:
                if st.button("✕", key=f"del_metric_{name}", help=f"Remove {name}"):
                    del st.session_state.custom_metrics[name]
                    st.session_state.data_context = rebuild_metrics_context(
                        st.session_state.data_context,
                        st.session_state.custom_metrics,
                    )
                    st.rerun()

    # Add new metric form
    with st.expander("➕ Add Metric", expanded=not metrics):
        new_name = st.text_input(
            "Metric name",
            placeholder="e.g., Sessions per User",
            key="new_metric_name",
        )
        new_formula = st.text_input(
            "Formula (use column names)",
            placeholder="e.g., sessions / users",
            key="new_metric_formula",
        )
        ctx = st.session_state.data_context
        numeric_hint = ", ".join(ctx.base_df.select_dtypes(include=["number"]).columns.tolist()[:5])
        if numeric_hint:
            st.caption(f"Available numeric columns: {numeric_hint}")

        if st.button("Add", use_container_width=True, key="add_metric_btn"):
            if not new_name.strip():
                st.warning("Please enter a metric name.")
            elif not new_formula.strip():
                st.warning("Please enter a formula.")
            elif new_name in st.session_state.custom_metrics:
                st.warning(f"Metric '{new_name}' already exists. Delete it first.")
            else:
                # Validate formula by trying it on a small sample
                try:
                    ctx = st.session_state.data_context
                    test_df = ctx.base_df.head(5).copy()
                    test_df[new_name] = test_df.eval(new_formula)
                    # Register formula and rebuild from raw_df
                    st.session_state.custom_metrics[new_name] = new_formula
                    st.session_state.data_context = rebuild_metrics_context(
                        ctx, st.session_state.custom_metrics
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Invalid formula: {e}")


def _render_learn_link() -> None:
    """Render the navigation link to the Learn page."""
    st.divider()
    st.page_link(
        "pages/learn.py",
        label="📚 Learn Python",
        icon="📚",
        help="Interactive tutorials on Streamlit, Pandas, Plotly, Gemini, and more",
    )


def _render_compare_controls() -> None:
    """Render the Compare mode toggle + dimension/value selectors.

    v0.2.0: DataContext is the sole data-state owner.
    """
    if st.session_state.data_context is None:
        return

    st.divider()
    compare_mode = st.toggle("🔬 Compare Mode", value=False, key="compare_mode")

    if compare_mode:
        col_types = detect_column_types(st.session_state.data_context.active_df)
        categorical_cols = [
            c for c, t in col_types.items() if t in (ColumnType.CATEGORICAL, ColumnType.TEXT)
        ]
        if categorical_cols:
            dimension = st.selectbox("Split by", categorical_cols, key="compare_dimension")
            unique_vals = sorted(
                st.session_state.data_context.active_df[dimension].dropna().unique().tolist()
            )
            if len(unique_vals) >= 2:
                val_a = st.selectbox("Value A", unique_vals, key="compare_val_a")
                st.selectbox(
                    "Value B",
                    [v for v in unique_vals if v != val_a],
                    key="compare_val_b",
                )
            else:
                st.caption("Need ≥2 unique values in the selected dimension.")
        else:
            st.caption("No categorical columns available for comparison.")


def _process_uploaded_file(uploaded_file) -> None:
    """Parse uploaded file and populate session state."""
    file_id = f"{uploaded_file.name}-{uploaded_file.size}"
    is_new_file = file_id != st.session_state.last_file_id
    should_process = (
        st.session_state.data_context is None and not st.session_state.data_cleared
    ) or is_new_file

    if not should_process:
        return

    if is_new_file and st.session_state.data_context is not None:
        clear_data()
        st.session_state.data_cleared = False

    df, error, warning = load_file(uploaded_file)

    if error:
        st.error(f"❌ {error}")
        st.session_state.last_file_id = file_id
    else:
        if warning:
            st.warning(f"⚠️ {warning}")
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"📥 Download truncated data ({len(df):,} rows)",
                data=csv_data,
                file_name=f"truncated_{uploaded_file.name}",
                mime="text/csv",
            )
        missing = validate_columns(df)
        if missing:
            st.warning(
                f"⚠️ Missing expected columns: {', '.join(missing)}. "
                "Some features may be limited."
            )

        _populate_data_state(
            df,
            "file",
            missing,
            file_bytes=uploaded_file.getvalue(),
            display_name=uploaded_file.name,
        )
        st.session_state.last_file_id = file_id
