"""Token-safety source scans — v0.3.0 Phase 1 (§1.4).

Guards against credential leakage at the source level: OAuth tokens,
API keys, and developer keys must never be passed to Streamlit display
calls, logger calls, or exception messages, and Drive download error
handlers must never use ``exc_info=True`` (tracebacks can reproduce raw
``HttpError`` payloads including request URLs and file IDs).

Scans runtime source only (utils/, components/, pages/, app.py) —
test fixtures and historical docs are excluded by design.
"""

import ast
import os
import re

ROOT = os.path.dirname(os.path.dirname(__file__))

_RUNTIME_DIRS = ["utils", "components", "pages"]
_RUNTIME_FILES = ["app.py"]

# Credential-like variable names that must never reach display/log/raise.
_CREDENTIAL_NAMES = {
    "token",
    "oauth_token",
    "access_token",
    "developer_key",
    "api_key",
}

# Word-boundary matcher so `api_key_error` / `token_uri` don't false-positive.
_CRED_RE = re.compile(r"\b(" + "|".join(sorted(_CREDENTIAL_NAMES)) + r")\b")

# All Streamlit calls that render content to the UI. `st.exception`,
# `st.json`, `st.code`, and `st.dataframe` are included so a credential
# variable can never reach the UI through a less-common display path.
_DISPLAY_CALLS = (
    "st.write(",
    "st.error(",
    "st.warning(",
    "st.info(",
    "st.success(",
    "st.exception(",
    "st.json(",
    "st.code(",
    "st.dataframe(",
)
_LOG_CALLS = ("logger.info(", "logger.warning(", "logger.error(", "logger.debug(")


def _iter_runtime_files():
    for dir_name in _RUNTIME_DIRS:
        dir_path = os.path.join(ROOT, dir_name)
        if not os.path.isdir(dir_path):
            continue
        for root, _dirs, files in os.walk(dir_path):
            for fname in files:
                if fname.endswith(".py") and not fname.startswith("test_"):
                    yield os.path.join(root, fname)
    for fname in _RUNTIME_FILES:
        fpath = os.path.join(ROOT, fname)
        if os.path.isfile(fpath):
            yield fpath


class TestTokenSafety:
    """Source-level credential-leak scans (v0.3.0 Phase 1 §1.4)."""

    def test_no_credential_vars_in_streamlit_display(self):
        """st.write/st.error/st.warning/st.info/st.success never receive
        token- or key-containing variables."""
        violations: list[str] = []
        for fpath in _iter_runtime_files():
            with open(fpath) as f:
                for lineno, line in enumerate(f, 1):
                    if any(call in line for call in _DISPLAY_CALLS):
                        if _CRED_RE.search(line):
                            violations.append(f"{os.path.relpath(fpath, ROOT)}:{lineno}")
        assert not violations, (
            "Credential variables passed to Streamlit display calls:\n  "
            + "\n  ".join(violations)
            + "\n\nTokens/API keys must never be rendered to the UI."
        )

    def test_no_token_in_logging_calls(self):
        """logger.info/warning/error/debug never receive token- or
        key-containing variables."""
        violations: list[str] = []
        for fpath in _iter_runtime_files():
            with open(fpath) as f:
                for lineno, line in enumerate(f, 1):
                    if any(call in line for call in _LOG_CALLS):
                        if _CRED_RE.search(line):
                            violations.append(f"{os.path.relpath(fpath, ROOT)}:{lineno}")
        assert not violations, (
            "Credential variables passed to logger calls:\n  "
            + "\n  ".join(violations)
            + "\n\nTokens/API keys must never be written to logs."
        )

    def test_no_token_in_exception_messages(self):
        """raise statements never interpolate token/key values."""
        violations: list[str] = []
        for fpath in _iter_runtime_files():
            with open(fpath) as f:
                for lineno, line in enumerate(f, 1):
                    if line.lstrip().startswith("raise ") or "raise " in line:
                        if _CRED_RE.search(line):
                            violations.append(f"{os.path.relpath(fpath, ROOT)}:{lineno}")
        assert not violations, (
            "Credential variables interpolated into exception messages:\n  "
            + "\n  ".join(violations)
            + "\n\nException messages must never include token/key values."
        )

    def test_no_exc_info_on_drive_errors(self):
        """Drive download error handlers must not use ``exc_info=True``.

        A traceback can reproduce the raw ``HttpError`` payload — request
        URLs and file IDs. Scans ``utils/drive_client.py`` for any call
        with ``exc_info=True``.
        """
        fpath = os.path.join(ROOT, "utils", "drive_client.py")
        with open(fpath) as f:
            tree = ast.parse(f.read(), filename=fpath)

        violations: list[int] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for kw in node.keywords:
                if kw.arg == "exc_info" and isinstance(kw.value, ast.Constant):
                    if kw.value.value is True:
                        violations.append(node.lineno)
        assert not violations, (
            "drive_client.py uses exc_info=True at lines "
            f"{violations}. Drive error handlers must log an allowlisted "
            "category only — never the raw HttpError/traceback."
        )

    # ── Synthetic negative/positive fixtures ──────────────────────────────

    def test_display_scan_flags_credential_var(self):
        """Prove the display scanner catches a token variable."""
        source = 'st.error(f"Oops {oauth_token}")'
        assert _CRED_RE.search(source)

    def test_display_scan_allows_similar_identifiers(self):
        """Similar identifiers (api_key_error, token_uri) are not flagged."""
        assert not _CRED_RE.search("st.error(api_key_error)")
        assert not _CRED_RE.search("st.error(token_uri)")
        assert not _CRED_RE.search("st.write('Token refresh failed')")
