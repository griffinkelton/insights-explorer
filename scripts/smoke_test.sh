#!/usr/bin/env bash
# ── Headless Smoke Test ──────────────────────────────────────────────────────
# Starts Streamlit without a browser, verifies it boots cleanly (HTTP 200),
# checks for import errors in the log, and shuts down.
#
# Usage:
#   bash scripts/smoke_test.sh
#
# Prerequisites:
#   - Python venv at ./venv
#   - Streamlit installed

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="/tmp/insights_explorer_smoke.log"
PORT=8501
MAX_WAIT=25

cd "$PROJECT_ROOT"

# ── Clean up any leftover process ────────────────────────────────────────────
pkill -f "streamlit run" 2>/dev/null || true
sleep 1

# ── Activate venv and start Streamlit in background ──────────────────────────
echo "=== Starting Streamlit (headless) ==="
source venv/bin/activate
streamlit run app.py --server.port "$PORT" --server.headless true \
    > "$LOG_FILE" 2>&1 &
STREAMLIT_PID=$!
echo "   PID: $STREAMLIT_PID"

# Ensure cleanup on any exit (Ctrl+C, error, normal completion)
trap 'kill $STREAMLIT_PID 2>/dev/null; pkill -f "streamlit run" 2>/dev/null' EXIT

# ── Wait for server to respond with HTTP 200 ─────────────────────────────────
echo "=== Waiting for server (timeout: ${MAX_WAIT}s) ==="
ELAPSED=0
while [ "$ELAPSED" -lt "$MAX_WAIT" ]; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "   Server ready after ${ELAPSED}s (HTTP $HTTP_CODE)"
        break
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
done

if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ Server failed to start within ${MAX_WAIT}s."
    echo "--- Last 30 lines of server log ---"
    tail -30 "$LOG_FILE"
    kill "$STREAMLIT_PID" 2>/dev/null || true
    exit 1
fi

# ── Check for import errors or tracebacks in log ─────────────────────────────
echo "=== Checking log for errors ==="
if grep -Eiq "traceback|ImportError|ModuleNotFoundError|SyntaxError|NameError" "$LOG_FILE"; then
    echo "❌ Errors found in server log:"
    grep -Ei "traceback|ImportError|ModuleNotFoundError|SyntaxError|NameError" "$LOG_FILE"
    kill "$STREAMLIT_PID" 2>/dev/null || true
    exit 1
fi
echo "   No import errors or tracebacks found."

# ── Quick verification: the page contains expected content ───────────────────
echo "=== Verifying page content ==="
PAGE=$(curl -s "http://localhost:$PORT")
if echo "$PAGE" | grep -q "GA4 Insight Explorer"; then
    echo "   ✅ Page title found."
else
    echo "   ⚠️  Page title not found (may be JS-rendered)."
fi

# ── Shutdown ─────────────────────────────────────────────────────────────────
echo "=== Shutting down ==="
kill "$STREAMLIT_PID" 2>/dev/null || true
sleep 1
# Ensure child processes are also killed
pkill -f "streamlit run" 2>/dev/null || true

echo ""
echo "✅ Smoke test PASSED — app boots cleanly with no import errors."
exit 0
