# ⚡ Streaming Token-by-Token Responses — Phase 5 Implementation Plan

> **Roadmap ref:** IMPLEMENTATION_PLAN.md #19, ENHANCEMENTS.md #21
> **Effort:** High (3-5 days) | **Risk:** High (fundamentally changes the response pipeline)
> **Status:** 🔲 Planned — no code written

---

## 🎯 Goal

Replace the current "wait 3-5 seconds, then show full response" behavior with a real-time, token-by-token streaming experience — like ChatGPT. Gemini's API supports streaming natively; the challenge is restructuring our response pipeline to handle it.

---

## 🧠 Why This Is Hard

Our current architecture is synchronous and sequential:

```
build_chat_prompt() → generate_response() → detect_chart_request() → render chat + chart
                     └── blocks UI ──┘
```

`generate_response()` returns the complete text. `detect_chart_request()` scans the complete text for keywords. The chart is rendered below the response.

With streaming, the text arrives token-by-token. We can't run chart detection until the stream completes. This means:

1. The streaming text must be rendered *during* the API call (non-blocking)
2. The full text must be captured for chart detection *after* the stream ends
3. The chart must be rendered *below* the streamed text, in the same message bubble
4. Error handling must account for mid-stream failures (network drop, quota exhaustion)

---

## 🗂️ Files & Changes

### 1. `utils/gemini_client.py` — Streaming Generator

#### New function: `generate_response_stream()`

```python
from collections.abc import Generator


def generate_response_stream(
    prompt: str,
    model: str = DEFAULT_MODEL,
) -> Generator[str, None, None]:
    """Stream Gemini response tokens one at a time.

    Yields text chunks as they arrive from the API.
    After the stream completes, the caller is responsible for
    collecting the full text and running chart detection.

    Raises:
        ValueError: Missing API key
        RuntimeError: API failure (rate limit, quota, etc.)
    """
    try:
        response = _get_client().models.generate_content_stream(
            model=model,
            contents=prompt,
            config={
                "temperature": DEFAULT_TEMPERATURE,
                "max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
            },
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except ValueError:
        raise  # API key errors propagate as-is
    except Exception as e:
        error_msg = str(e).lower()
        if "rate" in error_msg and "limit" in error_msg:
            raise RuntimeError(
                "Rate limit hit. Please wait a moment and try again."
            ) from e
        elif "quota" in error_msg:
            raise RuntimeError(
                "API quota exceeded. Check your Google Cloud quota or try again later."
            ) from e
        else:
            raise RuntimeError(
                f"Gemini API error: {str(e)}"
            ) from e
```

**Design decision — generator vs async:** `Generator` keeps things synchronous and Streamlit-compatible. `st.write_stream()` accepts any iterable. Async (`async for`) would require `asyncio.run()` in Streamlit's synchronous execution model, adding complexity for no benefit — the stream renders progressively in the browser via Streamlit's built-in streaming support.

**Keep the original `generate_response()`:** Don't delete it. The summary generation (one-click button) doesn't benefit from streaming — it's a single response, not a conversation. Keep both: `generate_response()` for summary, `generate_response_stream()` for chat.

### 2. `app.py` — Streaming Chat Rendering

#### Current chat handler (simplified):

```python
if prompt := st.chat_input(...):
    st.session_state.chat_history.append({"question": prompt, "response": None, "chart": None})

    with st.spinner("Thinking..."):
        chat_prompt = build_chat_prompt(prompt, df, stats)
        response = generate_response(chat_prompt)           # BLOCKS for 3-5s

        chart_config = detect_chart_request(response)
        chart_data = _generate_chart(df, chart_config, ...)

        st.session_state.chat_history[-1]["response"] = response
        st.session_state.chat_history[-1]["chart"] = chart_data

    st.rerun()
```

#### New streaming chat handler:

```python
if prompt := st.chat_input(...):
    st.session_state.chat_history.append({"question": prompt, "response": "", "chart": None})
    st.rerun()  # Rerun to show the user message immediately, then stream the response

# ── Streaming section (runs on rerun after appending question) ──

# Find the latest unanswered entry
if st.session_state.chat_history and st.session_state.chat_history[-1]["response"] == "":
    entry = st.session_state.chat_history[-1]

    # Render the user message
    with st.chat_message("user"):
        st.markdown(entry["question"])

    # Render the assistant message with streaming
    with st.chat_message("assistant"):
        try:
            chat_prompt = build_chat_prompt(
                entry["question"],
                df,
                stats,
                conversation_history=st.session_state.chat_history[:-1],
            )
            # st.write_stream handles the progressive rendering
            full_response = st.write_stream(
                generate_response_stream(chat_prompt)
            )

            # After stream completes, detect and render chart
            chart_config = detect_chart_request(full_response)
            if chart_config:
                chart_data = _generate_chart(df, chart_config, full_response, entry["question"])
                if chart_data:
                    with st.container(border=True):
                        st.plotly_chart(
                            chart_data["fig"],
                            use_container_width=True,
                            key=f"chart_stream_{len(st.session_state.chat_history)}"
                        )
                    entry["chart"] = chart_data

            entry["response"] = full_response
            st.session_state.last_api_call = time.time()
            st.session_state.api_call_count += 1

        except ValueError as e:
            entry["response"] = f"🔑 Configuration error: {e}"
        except RuntimeError as e:
            entry["response"] = f"⚠️ API error: {e}"
```

**Why the `st.rerun()` after appending the question:** The streaming response must be rendered inside `st.chat_message("assistant")`, which must be placed *after* the user's `st.chat_message("user")`. By appending the question, rerunning, and then detecting the unanswered entry, we guarantee correct message ordering.

**Why full_response is a string, not a generator:** `st.write_stream()` returns the complete text after the stream finishes. This is Streamlit 1.37+ behavior. We store this string in `entry["response"]`.

#### Chat history rendering (for past messages):

The existing rendering loop needs a small tweak — past messages with streaming responses have a complete `response` string, so they render normally. The stream only happens for the *latest* unanswered entry:

```python
for i, entry in enumerate(st.session_state.chat_history):
    # Skip the latest entry if it's being streamed (rendered above)
    if i == len(st.session_state.chat_history) - 1 and entry["response"] == "":
        continue

    with st.chat_message("user"):
        st.markdown(entry["question"])
    with st.chat_message("assistant"):
        st.markdown(entry["response"])
        if entry.get("chart") and entry["chart"].get("fig"):
            with st.container(border=True):
                st.plotly_chart(entry["chart"]["fig"], use_container_width=True, key=f"chart_{i}")
```

### 3. `utils/gemini_client.py` — Error Handling in Streams

Mid-stream errors are tricky. If the API fails on token 47 of 200, we've already rendered 47 tokens to the user. `st.write_stream()` would raise an exception, which we catch:

```python
try:
    full_response = st.write_stream(generate_response_stream(chat_prompt))
except RuntimeError as e:
    # Partial response was already shown via streaming.
    # Append the error message so the user knows it was truncated.
    st.error(f"{e}")
    entry["response"] = f"{partial or ''}\n\n*[Response truncated: {e}]*"
```

This requires capturing partial output. Unfortunately, `st.write_stream()` doesn't expose partial output on error — the stream is consumed. Workaround: wrap the generator to accumulate chunks manually:

```python
def _accumulating_stream(stream):
    """Wrap a generator to accumulate chunks while yielding them."""
    full = []
    for chunk in stream:
        full.append(chunk)
        yield chunk
    return full  # Not accessible from st.write_stream, but we can use a list wrapper
```

A cleaner approach: use a mutable container:

```python
accumulated = []
try:
    def _wrapper():
        for chunk in generate_response_stream(chat_prompt):
            accumulated.append(chunk)
            yield chunk

    st.write_stream(_wrapper())
    full_response = "".join(accumulated)
except RuntimeError as e:
    full_response = "".join(accumulated)
    st.error(f"⚠️ Response truncated: {e}")
```

---

## 🔍 Edge Cases

| Edge Case | Handling |
|---|---|
| **Mid-stream network failure** | `_wrapper()` catches the error, accumulated text is saved, error appended to response |
| **Mid-stream quota exhaustion** | Same as network failure — partial response + error message |
| **Empty stream (no tokens returned)** | Gemini always returns at least one token for valid prompts. If somehow empty, `full_response` is `""`, chart detection returns `None`, and an empty message bubble shows (acceptable edge case) |
| **Very long response (10k+ tokens)** | `max_output_tokens=2048` caps it. Streaming handles 2k tokens smoothly (sub-second rendering) |
| **User sends another message while streaming** | Streamlit's synchronous model means the new message won't process until the current stream completes. The chat input is disabled during streaming (Streamlit's default behavior for `st.chat_input`) |
| **Multiple browser tabs** | Each tab has its own session state. Streaming works independently in each tab |
| **Streamlit version < 1.37** | `st.write_stream` added in 1.37. Fallback: detect the version at startup, use `generate_response()` (non-streaming) for older versions. Add a warning: "Streaming requires Streamlit 1.37+." |
| **Summary generation (non-chat)** | Keep using `generate_response()` (non-streaming) for the summary button. It's a single response, not a conversation, and streaming doesn't add value there |

---

## 🧪 Test Impact

- **`test_gemini_client.py`:** Add 2-3 tests:
  - `test_generate_response_stream_yields_tokens` — mock `generate_content_stream` to return chunks, verify generator yields them
  - `test_generate_response_stream_handles_rate_limit` — mock stream raises rate limit error, verify RuntimeError
  - `test_generate_response_stream_handles_quota_exceeded` — same for quota
- **Smoke test:** Send a chat message, verify text appears progressively (not all at once), verify chart renders after text completes

---

## 📐 Implementation Order

1. **Phase 5a (gemini_client):** Add `generate_response_stream()` generator. Write tests. Commit.
2. **Phase 5b (app.py streaming):** Rewrite chat handler to use `st.write_stream`. The message ordering (append → rerun → stream) is the trickiest part. Commit.
3. **Phase 5c (error recovery):** Add `_wrapper()` for partial-output capture. Test with a mock that raises mid-stream. Commit.
4. **Phase 5d (version compatibility):** Add Streamlit version check and fallback. Commit.

---

## 💭 Why This Matters

Streaming is the single most transformative UX improvement in the plan. It changes the perception of the app from "batch processor" to "real-time AI assistant." Users tolerate 5-second waits for summary generation, but for conversation, the expectation is instant feedback — even if the *full* response takes 5 seconds, seeing the first tokens appear in 200ms creates a completely different experience.

The technical challenge is worth it because once streaming works, it enables future features: stop-generation button, streaming to multiple targets (sidebar insights + chat simultaneously), and progressive chart rendering (show a chart as soon as enough data arrives, then refine it).

---

*Plan created from review of `utils/gemini_client.py` (generate_response), `app.py` (chat handler, message rendering loop), and Streamlit 1.37+ `st.write_stream` docs.*
