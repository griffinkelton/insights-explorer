"""Chat interface — message history, chat input, streaming, chart rendering, export."""

import re
import time
from typing import Any
import pandas as pd
import streamlit as st
from utils.prompt_templates import build_chat_prompt, detect_chart_request, build_comparison_prompt
from utils.gemini_client import generate_response_stream, generate_response
from utils.charts import generate_chart


def render_chat_section() -> None:
    """Render the full chat interface."""
    df = st.session_state.df

    # ── Chat header + New Chat button ─────────────────────────────────────
    col_chat_header, col_new_chat = st.columns([4, 1])
    with col_chat_header:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.5rem;">'
            '<h3 style="margin:0;">💬 Ask Questions</h3>'
            '<span class="kb-shortcut">⌘K</span> <span style="color:#686880;font-size:0.7rem;">focus chat</span>'
            '</div>',
            unsafe_allow_html=True,
        )
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
            else:
                # Render historical message
                st.markdown(entry["response"])
                if entry.get("chart") and entry["chart"].get("fig"):
                    with st.container(border=True):
                        st.plotly_chart(
                            entry["chart"]["fig"],
                            use_container_width=True,
                            key=f"chart_{i}_{st.session_state.get('theme', 'dark')}",
                        )

    # ── Chat input ───────────────────────────────────────────────────────
    if prompt := st.chat_input("e.g., which pages have the highest drop-off?"):
        # Rate limiting guard
        now = time.time()
        if now - st.session_state.last_api_call < 2.0:
            st.warning("⏳ Please wait a moment between questions...")
            st.stop()
        st.session_state.last_api_call = now
        st.session_state.api_call_count += 1

        st.session_state.chat_history.append({
            "question": prompt,
            "response": "",
            "chart": None,
        })
        st.rerun()

    # ── Export button ────────────────────────────────────────────────────
    if any(
        e.get("response") and e["response"] != ""
        for e in st.session_state.chat_history
    ):
        st.divider()
        if st.button("📥 Export Report", use_container_width=True):
            # Lazy import — kaleido may not be installed; error handled below
            from utils.report_exporter import build_markdown_report

            report = build_markdown_report(
                summary=st.session_state.summary,
                chat_history=st.session_state.chat_history,
                stats=st.session_state.stats or {},
                data_source=st.session_state.data_source,
            )
            st.download_button(
                label="⬇️ Download Markdown Report",
                data=report,
                file_name=f"ga4_insight_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
            )
            st.caption(
                "⚠️ Charts missing from the report? "
                "Install kaleido: `pip install kaleido`"
            )


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

    try:
        full_text = st.write_stream(generate_response_stream(chat_prompt))
        entry["response"] = full_text

        # Detect chart config from ORIGINAL response (before cleaning)
        chart_config = detect_chart_request(full_text)

        # Clean [CHART:...] token from displayed response
        cleaned_response = re.sub(r'\[CHART:.*?\]', '', full_text).strip()
        if cleaned_response:
            full_text = cleaned_response
            entry["response"] = cleaned_response
        # Retry: if no chart config, make a second lightweight call
        if not chart_config and len(full_text) > 100:
            try:
                retry_prompt = (
                    "Extract a chart suggestion from this analysis. "
                    "Output ONLY a JSON block like "
                    '{"type":"bar","x":"page","y":"sessions","title":"..."}. '
                    "If no chart applies, output {\"type\":\"none\"}.\n\n"
                    f"Analysis:\n{full_text[:2000]}"
                )
                retry_response = generate_response(retry_prompt)
                chart_config = detect_chart_request(retry_response)
                st.session_state.api_call_count += 1
                st.session_state.last_api_call = time.time()
            except Exception:
                pass  # Silent skip — chart is optional

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
                            df_a, chart_config, full_text, entry["question"],
                            theme=theme,
                        )
                        if chart_a:
                            st.plotly_chart(
                                chart_a["fig"], use_container_width=True,
                                key=f"comp_a_{i}_{theme}",
                            )
                    with col_b:
                        chart_b = generate_chart(
                            df_b, chart_config, full_text, entry["question"],
                            theme=theme,
                        )
                        if chart_b:
                            st.plotly_chart(
                                chart_b["fig"], use_container_width=True,
                                key=f"comp_b_{i}_{theme}",
                            )
                    entry["chart"] = {"fig": None, "type": "compare"}
                elif df_a.empty:
                    st.warning(f"No data for {dimension}={val_a}")
                else:
                    st.warning(f"No data for {dimension}={val_b}")
            else:
                chart_data = generate_chart(
                    df, chart_config, full_text, entry["question"],
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
        entry["response"] = f"🔑 Configuration error: {e}"
    except RuntimeError as e:
        entry["response"] = f"⚠️ API error: {e}"
    except Exception as e:
        entry["response"] = f"⚠️ An unexpected error occurred: {e}"
