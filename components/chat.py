"""Chat interface — message history, chat input, streaming, chart rendering, export."""

import logging
import re
import time
from typing import Any

import pandas as pd
import streamlit as st

from utils.charts import generate_chart
from utils.commands import get_command_pills, resolve_command
from utils.gemini_client import DEFAULT_MODEL, generate_response, generate_response_stream
from utils.prompt_templates import build_chat_prompt, detect_chart_request
from utils.session import streamlit_usage_sink

logger = logging.getLogger(__name__)


def render_chat_section() -> None:
    """Render the full chat interface."""
    ctx = st.session_state.get("data_context")
    df = ctx.active_df if ctx else None

    # ── Chat header + New Chat button ─────────────────────────────────────
    col_chat_header, col_new_chat = st.columns([4, 1])
    with col_chat_header:
        st.markdown("### 💬 Ask Questions")

    with col_new_chat:
        if st.button(
            "🆕 New Chat",
            use_container_width=True,
            help="Clear chat history but keep your data",
        ):
            st.session_state.chat_history = []
            st.rerun()

    # ── Render all messages ──────────────────────────────────────────────
    for i, entry in enumerate(st.session_state.chat_history):
        with st.chat_message("user"):
            st.markdown(entry["question"])

        with st.chat_message("assistant"):
            if entry["response"] == "":
                # Stream new message
                _stream_chat_response(entry, df, i)
            elif entry.get("error"):
                # Error entry — render as error, skip in history
                st.error(entry["error"])
            else:
                # Render historical message
                st.markdown(entry["response"])
                if i == len(st.session_state.chat_history) - 1:
                    _render_per_request_usage(entry)
                if entry.get("chart") and entry["chart"].get("fig"):
                    with st.container(border=True):
                        st.plotly_chart(
                            entry["chart"]["fig"],
                            use_container_width=True,
                            key=f"chart_{i}_{st.session_state.get('theme', 'dark')}",
                        )

    # ── Command pills ───────────────────────────────────────────────────
    _render_command_pills()

    # ── Chat input ───────────────────────────────────────────────────────
    if prompt := st.chat_input("e.g., which pages have the highest drop-off?"):
        # Resolve /command shortcuts to full templates
        resolved = resolve_command(prompt)
        # Rate limiting guard
        now = time.time()
        if now - st.session_state.last_api_call < 2.0:
            st.warning("⏳ Please wait a moment between questions...")
            st.stop()
        st.session_state.last_api_call = now
        st.session_state.api_attempt_count += 1

        st.session_state.chat_history.append(
            {
                "question": resolved,
                "response": "",
                "chart": None,
            }
        )
        st.rerun()

    # ── Chart extraction opt-in toggle ─────────────────────────────────
    st.caption("Chart suggestions are optional and use an additional API call.")
    st.checkbox(
        "📊 Suggest chart when useful",
        value=False,
        key="chart_opt_in",
        help="When enabled, a second Gemini call will attempt to extract chart data from responses.",
    )

    # ── Usage stats below chat ───────────────────────────────────────────
    _render_usage_stats()

    # ── Export button ────────────────────────────────────────────────────
    if any(e.get("response") and e["response"] != "" for e in st.session_state.chat_history):
        st.divider()
        col_md, col_xl, col_pdf = st.columns(3)
        with col_md:
            if st.button("📄 Markdown", use_container_width=True):
                from utils.report_exporter import build_markdown_report

                report = build_markdown_report(
                    summary=st.session_state.summary,
                    chat_history=st.session_state.chat_history,
                    stats=st.session_state.stats or {},
                    data_source=st.session_state.data_source,
                )
                st.download_button(
                    label="⬇️ Download .md",
                    data=report,
                    file_name=f"ga4_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.md",
                    mime="text/markdown",
                    key="dl_markdown",
                )
        with col_xl:
            if st.button("📊 Excel", use_container_width=True):
                from utils.report_exporter import build_excel_report

                excel_bytes = build_excel_report(
                    df=df,
                    summary=st.session_state.summary,
                    stats=st.session_state.stats or {},
                    data_source=st.session_state.data_source,
                )
                st.download_button(
                    label="⬇️ Download .xlsx",
                    data=excel_bytes,
                    file_name=f"ga4_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_excel",
                )
        with col_pdf:
            if st.button("📑 PDF", use_container_width=True):
                from utils.report_exporter import build_pdf_report

                pdf_bytes = build_pdf_report(
                    summary=st.session_state.summary,
                    stats=st.session_state.stats or {},
                    chat_history=st.session_state.chat_history,
                    data_source=st.session_state.data_source,
                )
                st.download_button(
                    label="⬇️ Download .pdf",
                    data=pdf_bytes,
                    file_name=f"ga4_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    key="dl_pdf",
                )


def _render_usage_stats() -> None:
    """Render cumulative session token usage below the chat input.

    Informational only — no gauges, traffic lights, or quota estimates.
    """
    total_input = st.session_state.get("total_input_tokens", 0)
    total_output = st.session_state.get("total_output_tokens", 0)
    total_tokens = st.session_state.get("total_tokens_used", 0)
    total_thought = st.session_state.get("total_thought_tokens", 0)

    if total_tokens == 0:
        return

    model = st.session_state.get("selected_model", "gemini-2.5-flash")
    success_count = st.session_state.get("api_success_count", 0)
    parts = [
        f"🤖 {model}",
        f"📞 {success_count} calls",
        f"⬅️ {total_input:,} in",
        f"➡️ {total_output:,} out",
        f"Σ {total_tokens:,} total",
    ]
    if total_thought > 0:
        parts.append(f"💭 {total_thought:,} thoughts")
    st.caption(" · ".join(parts))


def _render_per_request_usage(entry: dict[str, Any]) -> None:
    """Render per-request token counts for the most recent chat response.

    Shown in a collapsed expander — informational only, no gauges or warnings.
    """
    usage = entry.get("usage")
    if not usage:
        return

    fields = [
        ("prompt_tokens", "⬅️"),
        ("output_tokens", "➡️"),
        ("total_tokens", "Σ"),
        ("thought_tokens", "💭"),
        ("cached_tokens", "📦"),
        ("tool_tokens", "🔧"),
    ]
    parts = []
    for key, icon in fields:
        val = usage.get(key, 0)
        if val > 0:
            parts.append(f"{icon} {val:,} {_token_label(key)}")
    if parts:
        with st.expander(f"📊 Usage ({usage.get('total_tokens', 0):,} tokens)", expanded=False):
            st.caption(" · ".join(parts))


def _token_label(key: str) -> str:
    """Short label for each token field."""
    return {
        "prompt_tokens": "in",
        "output_tokens": "out",
        "thought_tokens": "thoughts",
        "cached_tokens": "cached",
        "tool_tokens": "tools",
        "total_tokens": "total",
    }.get(key, key)


def _render_command_pills() -> None:
    """Render a row of clickable command shortcut pills above the chat input.

    Each pill sends the command template directly to the chat — no /prefix needed.
    Uses the BUG-005 pattern: `if st.button` instead of `on_click`.
    """
    pills = get_command_pills()
    cols = st.columns(len(pills))
    for i, (pill, col) in enumerate(zip(pills, cols)):
        with col:
            label = f"{pill['icon']} {pill['label']}"
            if st.button(
                label,
                key=f"cmd_pill_{i}",
                use_container_width=True,
                help=pill["description"],
            ):
                # Rate limiting guard
                now = time.time()
                if now - st.session_state.last_api_call < 2.0:
                    st.warning("⏳ Please wait a moment…")
                    st.stop()
                st.session_state.last_api_call = now
                st.session_state.api_attempt_count += 1

                st.session_state.chat_history.append(
                    {
                        "question": pill["template"],
                        "response": "",
                        "chart": None,
                    }
                )
                st.rerun()


def _stream_chat_response(entry: dict[str, Any], df: pd.DataFrame, i: int) -> None:
    """Stream a Gemini response with st.write_stream, then detect and render chart.

    ⚠️ SIDE EFFECT: Mutates `entry["response"]` and `entry["chart"]` in place
    on `st.session_state.chat_history[-1]` during streaming. After the refactor,
    a follow-up commit should make this function accept parameters and return
    values for full testability.
    """
    chat_prompt = build_chat_prompt(
        entry["question"],
        df,
        st.session_state.stats,
        conversation_history=st.session_state.chat_history[:-1],
    )

    _model = st.session_state.get("selected_model", DEFAULT_MODEL)
    try:
        full_text = st.write_stream(
            generate_response_stream(
                chat_prompt, model=_model, request_type="chat", usage_sink=streamlit_usage_sink
            )
        )
        entry["response"] = full_text

        # Detect chart config from ORIGINAL response (before cleaning)
        chart_config = detect_chart_request(full_text)

        # Clean [CHART:...] token from displayed response
        cleaned_response = re.sub(r"\[CHART:.*?\]", "", full_text).strip()
        if cleaned_response:
            full_text = cleaned_response
            entry["response"] = cleaned_response
        # Chart extraction (only when user opted in via checkbox)
        if (
            not chart_config
            and len(full_text) > 100
            and st.session_state.get("chart_opt_in", False)
        ):
            try:
                retry_prompt = (
                    "Extract a chart suggestion from this analysis. "
                    "Output ONLY a JSON block like "
                    '{"type":"bar","x":"page","y":"sessions","title":"..."}. '
                    'If no chart applies, output {"type":"none"}.\n\n'
                    f"Analysis:\n{full_text[:2000]}"
                )
                retry_response = generate_response(
                    retry_prompt,
                    model=_model,
                    request_type="chart",
                    usage_sink=streamlit_usage_sink,
                )
                chart_config = detect_chart_request(retry_response)
                # api_success_count is handled by streamlit_usage_sink via usage_sink
                st.session_state.last_api_call = time.time()
            except Exception:
                logger.debug("Chart extraction failed", exc_info=True)
                st.caption("Chart suggestion unavailable — try a more specific question.")

        if chart_config:
            # Comparative mode: split data and render dual charts
            if st.session_state.get("compare_mode") and st.session_state.get("compare_dimension"):
                dimension = st.session_state.compare_dimension
                val_a = st.session_state.compare_val_a
                val_b = st.session_state.compare_val_b
                mask_a = df[dimension] == val_a
                mask_b = df[dimension] == val_b
                df_a = df[mask_a]
                df_b = df[mask_b]

                if not df_a.empty and not df_b.empty:
                    col_a, col_b = st.columns(2)
                    theme = st.session_state.get("theme", "dark")
                    with col_a:
                        chart_a = generate_chart(
                            df_a,
                            chart_config,
                            full_text,
                            entry["question"],
                            theme=theme,
                        )
                        if chart_a:
                            st.plotly_chart(
                                chart_a["fig"],
                                use_container_width=True,
                                key=f"comp_a_{i}_{theme}",
                            )
                    with col_b:
                        chart_b = generate_chart(
                            df_b,
                            chart_config,
                            full_text,
                            entry["question"],
                            theme=theme,
                        )
                        if chart_b:
                            st.plotly_chart(
                                chart_b["fig"],
                                use_container_width=True,
                                key=f"comp_b_{i}_{theme}",
                            )
                    entry["chart"] = {"fig": None, "type": "compare"}
                elif df_a.empty:
                    st.warning(f"No data for {dimension}={val_a}")
                else:
                    st.warning(f"No data for {dimension}={val_b}")
            else:
                chart_data = generate_chart(
                    df,
                    chart_config,
                    full_text,
                    entry["question"],
                    theme=st.session_state.get("theme", "dark"),
                )
                if chart_data:
                    entry["chart"] = chart_data
                    with st.container(border=True):
                        st.plotly_chart(
                            chart_data["fig"],
                            use_container_width=True,
                            key=f"chart_{i}_{st.session_state.get('theme', 'dark')}",
                        )

    except ValueError as e:
        entry["error"] = f"🔑 Configuration error: {e}"
        entry["response"] = ""
        if "api_failure_count" not in st.session_state:
            st.session_state.api_failure_count = 0
        st.session_state.api_failure_count += 1
    except RuntimeError as e:
        entry["error"] = f"⚠️ API error: {e}"
        entry["response"] = ""
        if "api_failure_count" not in st.session_state:
            st.session_state.api_failure_count = 0
        st.session_state.api_failure_count += 1
    except Exception as e:
        entry["error"] = f"⚠️ An unexpected error occurred: {e}"
        entry["response"] = ""
        if "api_failure_count" not in st.session_state:
            st.session_state.api_failure_count = 0
        st.session_state.api_failure_count += 1
        logger.warning("Chat streaming error", exc_info=True)
