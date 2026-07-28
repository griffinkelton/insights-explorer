"""Chat interface — message history, chat input, streaming, chart rendering, export."""

import time
from typing import Any
import pandas as pd
import streamlit as st
from utils.prompt_templates import build_chat_prompt, detect_chart_request
from utils.gemini_client import generate_response_stream
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
                            key=f"chart_{i}",
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

        # Detect and render chart from the full response
        chart_config = detect_chart_request(full_text)
        if chart_config:
            chart_data = generate_chart(df, chart_config, full_text, entry["question"])
            if chart_data:
                entry["chart"] = chart_data
                with st.container(border=True):
                    st.plotly_chart(
                        chart_data["fig"],
                        use_container_width=True,
                        key=f"chart_{i}",
                    )

    except ValueError as e:
        entry["response"] = f"🔑 Configuration error: {e}"
    except RuntimeError as e:
        entry["response"] = f"⚠️ API error: {e}"
    except Exception as e:
        entry["response"] = f"⚠️ An unexpected error occurred: {e}"
