"""Tests for components/sidebar.py — 5-test pattern."""

import ast

MODULE = "components/sidebar.py"


def _parse() -> ast.Module:
    with open(MODULE) as f:
        return ast.parse(f.read(), filename=MODULE)


class TestSidebarSyntax:
    def test_parses_without_syntax_error(self):
        tree = _parse()
        assert isinstance(tree, ast.Module)


class TestSidebarImport:
    def test_module_imports_without_error(self):
        from components.sidebar import render_sidebar

        assert callable(render_sidebar)


class TestSidebarStructure:
    def test_has_render_function(self):
        source = open(MODULE).read()
        assert "def render_sidebar()" in source

    def test_has_theme_toggle_function(self):
        """Theme toggle: _render_theme_toggle must exist in sidebar."""
        source = open(MODULE).read()
        assert "def _render_theme_toggle()" in source

    def test_clear_button_no_on_click_anti_pattern(self):
        """BUG-005: _render_clear_button uses `if st.button`, not `on_click=`."""
        import re

        source = open(MODULE).read()
        # Extract the _render_clear_button function body
        idx = source.find("def _render_clear_button")
        assert idx > 0, "Missing _render_clear_button function"
        next_def = source.find("\ndef ", idx + 1)
        func_source = source[idx : next_def if next_def > 0 else len(source)]
        # Strip docstrings and comments before checking for on_click=
        code = re.sub(r'""".*?"""', "", func_source, flags=re.DOTALL)
        code = re.sub(r"#.*$", "", code, flags=re.MULTILINE)
        assert "on_click=" not in code, "BUG-005: on_click= anti-pattern in _render_clear_button"

    def test_has_drive_picker_function(self):
        """v0.3.0 Phase 3.0: _render_drive_picker must exist in sidebar."""
        source = open(MODULE).read()
        assert "def _render_drive_picker()" in source

    def test_clear_data_uses_button_if_pattern(self):
        """Clear Data must use `if st.button(...)` pattern per BUG-005."""
        source = open(MODULE).read()
        assert "if st.button" in source
        assert "clear_data()" in source


# ── Interstitial PR-L2 (Workstream B): theme-token refactor ───────────────
# B2b section-header helper, B2c OAuth caption vars, B2d .privacy-card.
# Guard rail: sidebar must not re-introduce inline theme-branched colors.


class TestInterstitialLightTokens:
    """B2b/B2c/B2d: sidebar uses CSS vars — no inline theme-branched colors."""

    def test_section_header_helper_exists(self):
        source = open(MODULE).read()
        assert "def _section_header" in source

    def test_section_headers_use_helper(self):
        """All four section headers call _section_header (no inline color)."""
        source = open(MODULE).read()
        assert '_section_header("🔗 Google Analytics 4 (Live)")' in source
        assert '_section_header("📂 Google Drive Import")' in source
        assert '_section_header("🤖 AI Model")' in source
        assert '_section_header("🧮 Custom Metrics")' in source

    def test_no_theme_branch_color_variables(self):
        """The old theme-branched inline color variables are gone."""
        source = open(MODULE).read()
        for var in (
            "title_color =",
            "subtitle_color =",
            "section_color =",
            "metrics_color =",
            "footer_color =",
            "privacy_bg =",
            "privacy_border =",
            "privacy_text =",
        ):
            assert var not in source, f"{var} theme-branch still present"

    def test_no_raw_theme_hex_text_colors(self):
        """No dark-optimized raw hexes remain in text styles (B2c/B2d).

        Intentional hexes deliberately excluded (keep this list updated):
        #6366f1/#8b5cf6 (logo gradient, static brand) and
        #059669/#d97706 (tier badge — tier-based, not theme-based).
        """
        source = open(MODULE).read()
        for hex_code in (
            "#1f2937",
            "#f0f0f5",
            "#6b7280",
            "#9898b0",
            "#686880",
            "#818cf8",
            "#9ca3af",
        ):
            assert hex_code not in source, f"{hex_code} hard-coded text color"

    def test_oauth_redirect_uses_vars(self):
        source = open(MODULE).read()
        assert "color:var(--text-secondary)" in source
        assert "color:var(--text-muted)" in source
        assert "color:var(--accent-hover)" in source

    def test_privacy_card_uses_class(self):
        source = open(MODULE).read()
        assert 'class="privacy-card"' in source
        assert 'class="privacy-card-text"' in source


# ── v0.3.0 Phase 2.3: Drive ingestion unit tests ──────────────────────────


class TestNamedBytesIO:
    """_NamedBytesIO adapter must satisfy load_file()'s interface."""

    def test_provides_name_and_read(self):
        """_NamedBytesIO has .name and .read() — the two things load_file() uses."""
        from components.sidebar import _NamedBytesIO

        bio = _NamedBytesIO(b"a,b\n1,2", "test.csv")
        assert bio.name == "test.csv"
        assert bio.read() == b"a,b\n1,2"

    def test_name_lower_works_for_extension_detection(self):
        """load_file() calls file.name.lower() for extension detection."""
        from components.sidebar import _NamedBytesIO

        bio = _NamedBytesIO(b"x", "Report.CSV")
        assert bio.name.lower() == "report.csv"

    def test_passes_through_load_file_csv(self):
        """_NamedBytesIO with CSV bytes → load_file() → DataFrame."""
        from components.sidebar import _NamedBytesIO
        from utils.data_loader import load_file

        bio = _NamedBytesIO(b"date,sessions\n2025-01-01,100", "data.csv")
        df, error, warning = load_file(bio)
        assert error is None
        assert df is not None
        assert list(df.columns) == ["date", "sessions"]
        assert len(df) == 1

    def test_passes_through_load_file_xlsx(self):
        """_NamedBytesIO with XLSX bytes → load_file() → DataFrame."""
        import pandas as pd
        from io import BytesIO
        from components.sidebar import _NamedBytesIO
        from utils.data_loader import load_file

        src = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        buf = BytesIO()
        src.to_excel(buf, index=False, engine="openpyxl")

        bio = _NamedBytesIO(buf.getvalue(), "data.xlsx")
        df, error, warning = load_file(bio)
        assert error is None
        assert df is not None
        assert list(df.columns) == ["a", "b"]

    def test_size_attribute_is_set_but_irrelevant(self):
        """load_file() uses len(file.read()), not .size — .size is harmless baggage."""
        from components.sidebar import _NamedBytesIO

        bio = _NamedBytesIO(b"hello", "data.csv")
        assert bio.size == 5  # set for completeness
        # Proves .size is irrelevant: load_file uses len(file.read()).
        assert len(bio.read()) == 5


class TestIngestDriveFile:
    """_ingest_drive_file integration: downloader → parser → populate."""

    @staticmethod
    def _fake_downloader(creds, file_id):
        """Synthetic downloader returning fixture CSV bytes + server name."""
        return b"date,sessions\n2025-01-01,100", "server-report.csv"

    @staticmethod
    def _failing_downloader(creds, file_id):
        """Downloader that raises DriveImportError (simulates not_found)."""
        from utils.drive_client import DriveImportError

        raise DriveImportError("not_found", "File not found or access denied.")

    def test_drive_bytes_use_existing_load_file_interface(self, monkeypatch):
        """Drive ingestion routes through load_file(), not a separate parser."""
        from unittest.mock import MagicMock
        from components.sidebar import _ingest_drive_file

        mock_creds = MagicMock()
        fake_st = MagicMock()
        monkeypatch.setattr("components.sidebar.st", fake_st)
        monkeypatch.setattr("components.sidebar.validate_columns", lambda df: [])
        monkeypatch.setattr("components.sidebar._populate_data_state", MagicMock())

        _ingest_drive_file(self._fake_downloader, mock_creds, "file123")

        # Must have called _populate_data_state with source="drive".
        from components.sidebar import _populate_data_state

        _populate_data_state.assert_called_once()
        call_kwargs = _populate_data_state.call_args[1]
        assert call_kwargs["source"] == "drive"
        assert call_kwargs["display_name"] == "server-report.csv"
        assert call_kwargs["file_bytes"] == b"date,sessions\n2025-01-01,100"

    def test_download_failure_preserves_existing_state(self, monkeypatch):
        """DriveImportError on download → error shown, no state mutated."""
        from unittest.mock import MagicMock
        from components.sidebar import _ingest_drive_file

        mock_creds = MagicMock()
        fake_st = MagicMock()
        monkeypatch.setattr("components.sidebar.st", fake_st)
        monkeypatch.setattr("components.sidebar._populate_data_state", MagicMock())

        _ingest_drive_file(self._failing_downloader, mock_creds, "file123")

        # Must show an error and NOT call _populate_data_state.
        fake_st.error.assert_called()
        from components.sidebar import _populate_data_state

        _populate_data_state.assert_not_called()

    def test_loader_failure_does_not_call_populate_data_state(self, monkeypatch):
        """Parse failure → error shown, _populate_data_state not called."""
        from unittest.mock import MagicMock
        from components.sidebar import _ingest_drive_file

        def _bad_bytes_downloader(creds, file_id):
            return b"", "empty.csv"

        mock_creds = MagicMock()
        fake_st = MagicMock()
        monkeypatch.setattr("components.sidebar.st", fake_st)
        monkeypatch.setattr("components.sidebar._populate_data_state", MagicMock())

        _ingest_drive_file(_bad_bytes_downloader, mock_creds, "file123")

        fake_st.error.assert_called()
        from components.sidebar import _populate_data_state

        _populate_data_state.assert_not_called()

    def test_drive_ingestion_shows_truncation_warning(self, monkeypatch):
        """load_file() returns a warning (e.g., truncated data) → st.warning called."""
        from unittest.mock import MagicMock
        from components.sidebar import _ingest_drive_file

        # Build >50k rows of CSV to trigger truncation warning.
        header = b"date,sessions\n"
        row = b"2025-01-01,100\n"
        big_csv = header + row * 50_001

        def _big_downloader(creds, file_id):
            return big_csv, "big.csv"

        mock_creds = MagicMock()
        fake_st = MagicMock()
        monkeypatch.setattr("components.sidebar.st", fake_st)
        monkeypatch.setattr("components.sidebar.validate_columns", lambda df: [])
        monkeypatch.setattr("components.sidebar._populate_data_state", MagicMock())

        _ingest_drive_file(_big_downloader, mock_creds, "file123")

        fake_st.warning.assert_called()
        # Truncation warning is the first call; missing-columns may be a second.
        first_warning = fake_st.warning.call_args_list[0][0][0]
        assert "50,000" in first_warning
        assert "truncated" in first_warning.lower() or "showing" in first_warning.lower()


# ── v0.3.0 Phase 2.4: failure-preservation tests ──────────────────────────


class _FakeSessionState(dict):
    """A dict that also supports Streamlit's attribute-style access.

    ``_populate_data_state()`` and ``_process_uploaded_file()`` use both
    ``st.session_state.key`` and ``st.session_state["key"]`` access patterns.
    A plain dict only supports the latter.
    """

    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name: str, value) -> None:
        self[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            del self[name]
        except KeyError:
            raise AttributeError(name)


def _snap_state(state_dict: dict) -> dict:
    """Return a snapshot of all derived-state keys the ingestion paths own.

    Does not deep-copy — callers that mutate values must do their own copy.
    """
    keys = [
        "data_context",
        "custom_metrics",
        "stats",
        "missing_columns",
        "quality_report",
        "summary",
        "chat_history",
        "data_source",
        "data_cleared",
        "funnel_steps",
        "funnel_data",
    ]
    snap = {k: state_dict.get(k) for k in keys}
    # Capture forecast_* keys (dynamically named).
    for k in sorted(state_dict):
        if k.startswith("forecast_"):
            snap[k] = state_dict[k]
    return snap


def _make_pre_existing_state() -> dict:
    """Build a realistic pre-existing session state snapshot.

    Every value is a sentinel that is clearly distinguishable from the
    empty / reset values that _populate_data_state assigns on success.
    """
    return {
        "data_context": "PRIOR_CONTEXT",
        "custom_metrics": {"old_metric": "a + b"},
        "stats": {"rows": 999},
        "missing_columns": ["old_missing"],
        "quality_report": {"score": 95},
        "summary": "Old summary text.",
        "chat_history": [{"role": "user", "content": "prior question"}],
        "data_source": "old_source",
        "data_cleared": False,
        "funnel_steps": ["/step-1", "/step-2"],
        "funnel_data": "old_funnel_df",
        "forecast_session_abc": "old_forecast_data",
        "last_file_id": "old_file.csv-2048",
        # Extra key that ingestion should never touch.
        "theme": "dark",
        "selected_model": "gemini-2.5-flash",
    }


class TestPhase24FailurePreservation:
    """All ingestion paths must preserve prior state on any failure.

    The contract: a failing download, parse, or DataContext construction
    leaves every derived-state field identical to its pre-attempt value.

    These tests use a real dict as st.session_state (monkeypatched) so
    we can snapshot all 12+ fields and assert bit-for-bit preservation.
    """

    # ── upload path ───────────────────────────────────────────────────

    def test_upload_replacement_parse_failure_preserves_existing_state(self, monkeypatch):
        """_process_uploaded_file: load_file error → state unchanged."""
        import copy
        from unittest.mock import MagicMock
        from components.sidebar import _process_uploaded_file

        prior = _make_pre_existing_state()
        session = _FakeSessionState(copy.deepcopy(prior))
        monkeypatch.setattr("components.sidebar.st.session_state", session)
        monkeypatch.setattr("components.sidebar.st.error", MagicMock())

        def _fail_load(file_obj):
            return None, "Malformed CSV", None

        monkeypatch.setattr("components.sidebar.load_file", _fail_load)

        mock_file = MagicMock()
        mock_file.name = "broken.csv"
        mock_file.size = 512

        _process_uploaded_file(mock_file)

        # last_file_id is intentionally updated on error (prevents re-processing
        # loop) — everything else must be identical.
        expected = _FakeSessionState(copy.deepcopy(prior))
        expected["last_file_id"] = "broken.csv-512"

        # Snapshot the derived keys only (ignore theme, selected_model, etc.).
        assert _snap_state(session) == _snap_state(expected)
        # Also verify the untouched extras.
        assert session["theme"] == "dark"
        assert session["selected_model"] == "gemini-2.5-flash"

    # ── GA4 path ──────────────────────────────────────────────────────

    def test_ga4_context_factory_failure_preserves_existing_state(self, monkeypatch):
        """_populate_data_state(ga4): factory raises → state unchanged."""
        import copy
        import pandas as pd
        import pytest
        from components.sidebar import _populate_data_state

        prior = _make_pre_existing_state()
        session = _FakeSessionState(copy.deepcopy(prior))
        monkeypatch.setattr("components.sidebar.st.session_state", session)

        def _raise_factory(*args, **kwargs):
            raise RuntimeError("GA4 factory crash")

        monkeypatch.setattr("components.sidebar.create_context_from_ga4", _raise_factory)

        with pytest.raises(RuntimeError, match="GA4 factory crash"):
            _populate_data_state(
                pd.DataFrame({"a": [1]}),
                source="ga4",
                missing=[],
                ga4_start_date="7daysAgo",
            )

        # Exception propagated — zero state mutation occurred.
        assert _snap_state(session) == _snap_state(prior)

    # ── Drive path ────────────────────────────────────────────────────

    def test_drive_context_factory_failure_preserves_existing_state(self, monkeypatch):
        """_populate_data_state(drive): factory raises → state unchanged."""
        import copy
        import pandas as pd
        import pytest
        from components.sidebar import _populate_data_state

        prior = _make_pre_existing_state()
        session = _FakeSessionState(copy.deepcopy(prior))
        monkeypatch.setattr("components.sidebar.st.session_state", session)

        def _raise_factory(*args, **kwargs):
            raise ValueError("Drive factory crash")

        monkeypatch.setattr("components.sidebar.create_context_from_drive", _raise_factory)

        with pytest.raises(ValueError, match="Drive factory crash"):
            _populate_data_state(
                pd.DataFrame({"b": [2]}),
                source="drive",
                missing=[],
                file_bytes=b"test",
                display_name="test.csv",
            )

        assert _snap_state(session) == _snap_state(prior)

    # ── successful commit ─────────────────────────────────────────────

    def test_successful_import_replaces_existing_state_only_after_commit(self, monkeypatch):
        """_populate_data_state(file): success → all state fields replaced."""
        import pandas as pd
        from components.sidebar import _populate_data_state

        prior = _FakeSessionState(_make_pre_existing_state())
        monkeypatch.setattr("components.sidebar.st.session_state", prior)

        # Supply deterministic factories so the test doesn't depend on
        # real implementations.
        monkeypatch.setattr(
            "components.sidebar.create_context_from_upload",
            lambda df, fb, display_name="": "NEW_CONTEXT",
        )
        monkeypatch.setattr(
            "components.sidebar.get_dataset_stats",
            lambda df: {"new": "stats"},
        )
        monkeypatch.setattr(
            "components.sidebar.assess_data_quality",
            lambda df, m: {"new": "quality"},
        )

        _populate_data_state(
            pd.DataFrame({"x": [1, 2]}),
            source="file",
            missing=["col-a"],
        )

        # Every derived-state field must now reflect the new import.
        assert prior["data_context"] == "NEW_CONTEXT"
        assert prior["custom_metrics"] == {}
        assert prior["missing_columns"] == ["col-a"]
        assert prior["stats"] == {"new": "stats", "missing_columns": ["col-a"]}
        assert prior["quality_report"] == {"new": "quality"}
        assert prior["summary"] is None
        assert prior["chat_history"] == []
        assert prior["data_source"] == "file"
        assert prior["data_cleared"] is False
        assert prior["funnel_steps"] == []
        assert prior["funnel_data"] is None
        assert "forecast_session_abc" not in prior
        # Extra keys survive untouched.
        assert prior["theme"] == "dark"


class TestDriveIngestionEnhanced:
    """Full-state-snapshot versions of the existing Drive ingestion tests.

    These complement the Phase 2.3 TestIngestDriveFile tests (which
    verified that _populate_data_state is not called) by also proving
    that every derived-state key is unaltered.
    """

    def test_drive_download_failure_preserves_all_derived_state(self, monkeypatch):
        """DriveImportError → error shown, every derived-state key unchanged."""
        import copy
        from unittest.mock import MagicMock
        from components.sidebar import _ingest_drive_file
        from utils.drive_client import DriveImportError

        prior = _make_pre_existing_state()
        session = _FakeSessionState(copy.deepcopy(prior))
        monkeypatch.setattr("components.sidebar.st.session_state", session)
        monkeypatch.setattr("components.sidebar.st.error", MagicMock())

        def _fail_dl(creds, file_id):
            raise DriveImportError("not_found", "File not found.")

        _ingest_drive_file(_fail_dl, MagicMock(), "file123")

        assert _snap_state(session) == _snap_state(prior)

    def test_drive_loader_failure_preserves_all_derived_state(self, monkeypatch):
        """load_file error → error shown, every derived-state key unchanged."""
        import copy
        from unittest.mock import MagicMock
        from components.sidebar import _ingest_drive_file

        prior = _make_pre_existing_state()
        session = _FakeSessionState(copy.deepcopy(prior))
        monkeypatch.setattr("components.sidebar.st.session_state", session)
        monkeypatch.setattr("components.sidebar.st.error", MagicMock())

        # Download succeeds but the bytes are unparseable.
        def _empty_dl(creds, file_id):
            return b"garbage", "junk.csv"

        # Override load_file so the raw bytes don't accidentally parse.
        monkeypatch.setattr(
            "components.sidebar.load_file",
            lambda f: (None, "Unparseable file", None),
        )

        _ingest_drive_file(_empty_dl, MagicMock(), "file123")

        assert _snap_state(session) == _snap_state(prior)


# ── Interstitial PR 2: Drive Picker dialog state model ────────────────────
# Reuses _FakeSessionState from the Phase 2.4 section above (dict with
# Streamlit-style attribute access).


def _rerun_abort():
    """Simulate st.rerun() aborting the script run."""
    raise SystemExit("st.rerun")


class TestDrivePickerDialogState:
    """Interstitial PR 2: dialog gating, state model, and test-mode seams."""

    def test_drive_import_ready_false_without_auth(self, monkeypatch):
        from components.sidebar import drive_import_ready

        monkeypatch.setattr("components.sidebar._DRIVE_PICKER_TEST_MODE", False)
        ss = _FakeSessionState(ga4_creds=None)
        monkeypatch.setattr("components.sidebar.st.session_state", ss)
        assert drive_import_ready() is False

    def test_drive_import_ready_true_in_test_mode(self, monkeypatch):
        from components.sidebar import drive_import_ready

        monkeypatch.setattr("components.sidebar._DRIVE_PICKER_TEST_MODE", True)
        assert drive_import_ready() is True

    def test_activate_drive_picker_sets_flags(self, monkeypatch):
        from components.sidebar import activate_drive_picker

        ss = _FakeSessionState()
        monkeypatch.setattr("components.sidebar.st.session_state", ss)

        activate_drive_picker()

        assert ss["drive_picker_active"] is True
        assert ss["drive_picker_importing"] is False
        assert len(ss["drive_picker_request_id"]) == 36  # fresh UUID

    def test_dialog_not_created_when_inactive(self, monkeypatch):
        from components.sidebar import _maybe_show_drive_picker_dialog

        ss = _FakeSessionState(drive_picker_active=False)
        monkeypatch.setattr("components.sidebar.st.session_state", ss)
        created = []
        monkeypatch.setattr(
            "components.sidebar.st.dialog",
            lambda *a, **k: created.append((a, k)) or (lambda fn: lambda: None),
        )

        _maybe_show_drive_picker_dialog()

        assert created == [], "Dialog must not be created while inactive"

    def test_dialog_dismissible_tracks_importing(self, monkeypatch):
        from components.sidebar import _maybe_show_drive_picker_dialog

        captured = {}

        def _fake_dialog(*args, **kwargs):
            captured["kwargs"] = kwargs
            return lambda fn: lambda: None  # don't run the dialog body

        monkeypatch.setattr("components.sidebar.st.dialog", _fake_dialog)

        ss = _FakeSessionState(drive_picker_active=True, drive_picker_importing=False)
        monkeypatch.setattr("components.sidebar.st.session_state", ss)
        _maybe_show_drive_picker_dialog()
        assert captured["kwargs"]["width"] == "large"
        assert captured["kwargs"]["dismissible"] is True

        ss2 = _FakeSessionState(drive_picker_active=True, drive_picker_importing=True)
        monkeypatch.setattr("components.sidebar.st.session_state", ss2)
        _maybe_show_drive_picker_dialog()
        assert captured["kwargs"]["dismissible"] is False, "Locked while importing (D7)"

    def test_on_dismiss_resets_dialog_state(self, monkeypatch):
        from components.sidebar import _maybe_show_drive_picker_dialog

        captured = {}

        def _fake_dialog(*args, **kwargs):
            captured["on_dismiss"] = kwargs.get("on_dismiss")
            return lambda fn: lambda: None

        monkeypatch.setattr("components.sidebar.st.dialog", _fake_dialog)
        ss = _FakeSessionState(drive_picker_active=True, drive_picker_importing=True)
        monkeypatch.setattr("components.sidebar.st.session_state", ss)

        _maybe_show_drive_picker_dialog()
        assert callable(captured["on_dismiss"])
        captured["on_dismiss"]()
        assert ss["drive_picker_active"] is False
        assert ss["drive_picker_importing"] is False

    def test_dialog_theme_toggle_flips_theme(self, monkeypatch):
        from components.sidebar import _render_dialog_theme_control

        ss = _FakeSessionState(theme="dark", drive_picker_importing=False)
        monkeypatch.setattr("components.sidebar.st.session_state", ss)
        monkeypatch.setattr("components.sidebar.st.button", lambda *a, **k: True)  # clicked
        monkeypatch.setattr("components.sidebar.st.rerun", lambda: None)

        _render_dialog_theme_control()

        assert ss["theme"] == "light"

    def test_cancel_seam_closes_dialog(self, monkeypatch):
        import pytest
        from components.sidebar import _render_and_process_picker_test_mode

        class _Q:
            def get(self, key, default=""):
                return "cancel"

        ss = _FakeSessionState(
            drive_picker_active=True,
            drive_picker_importing=True,
            drive_picker_request_id="r1",
        )
        monkeypatch.setattr("components.sidebar.st.query_params", _Q())
        monkeypatch.setattr("components.sidebar.st.session_state", ss)
        monkeypatch.setattr("components.sidebar.st.rerun", _rerun_abort)

        with pytest.raises(SystemExit):
            _render_and_process_picker_test_mode()
        assert ss["drive_picker_active"] is False
        assert ss["drive_picker_importing"] is False

    def test_error_seam_keeps_dialog_open(self, monkeypatch):
        from unittest.mock import MagicMock
        from components.sidebar import _render_and_process_picker_test_mode

        class _Q:
            def get(self, key, default=""):
                return "error"

        ss = _FakeSessionState(
            drive_picker_active=True,
            drive_picker_importing=True,
            drive_picker_request_id="r1",
        )
        monkeypatch.setattr("components.sidebar.st.query_params", _Q())
        monkeypatch.setattr("components.sidebar.st.session_state", ss)
        mock_error = MagicMock()
        monkeypatch.setattr("components.sidebar.st.error", mock_error)

        _render_and_process_picker_test_mode()

        assert ss["drive_picker_active"] is True, "Dialog must stay open on error (D5)"
        assert ss["drive_picker_importing"] is False
        mock_error.assert_called_once()
        msg = mock_error.call_args[0][0]
        assert "failed" in msg.lower()

    def test_picked_seam_closes_dialog(self, monkeypatch):
        import pytest
        from components.sidebar import _render_and_process_picker_test_mode

        class _Q:
            def get(self, key, default=""):
                return "picked"

        ss = _FakeSessionState(
            drive_picker_active=True,
            drive_picker_importing=True,
            drive_picker_request_id="r1",
        )
        monkeypatch.setattr("components.sidebar.st.query_params", _Q())
        monkeypatch.setattr("components.sidebar.st.session_state", ss)
        monkeypatch.setattr("components.sidebar.st.rerun", _rerun_abort)

        with pytest.raises(SystemExit):
            _render_and_process_picker_test_mode()
        assert ss["drive_picker_active"] is False
        assert ss["drive_picker_importing"] is False

    def test_importing_lifecycle_around_ingest(self, monkeypatch):
        """drive_picker_importing is True during ingest and reset after."""
        from components.sidebar import _render_and_process_picker_production
        import components.sidebar as sidebar_mod

        ss = _FakeSessionState(
            drive_picker_active=True,
            drive_picker_request_id="r1",
            ga4_creds={"access_token": "tok", "token": "tok"},
        )
        monkeypatch.setattr("components.sidebar.st.session_state", ss)
        monkeypatch.setattr("components.sidebar.st.rerun", lambda: None)

        class _Secrets:
            def get(self, key, default=""):
                return "x"

        monkeypatch.setattr("components.sidebar.st.secrets", _Secrets())
        monkeypatch.setattr(
            "components.drive_picker_component.drive_picker_transport",
            lambda **kwargs: {"kind": "picked", "requestId": "r1", "fileId": "f1"},
        )
        monkeypatch.setattr("components.sidebar.credentials_from_dict", lambda d: "creds")

        seen = []

        def _ingest(downloader, creds, file_id):
            seen.append(ss["drive_picker_importing"])
            return True

        monkeypatch.setattr(sidebar_mod, "_ingest_drive_file", _ingest)

        _render_and_process_picker_production()

        assert seen == [True], "importing flag must be True during ingest"
        assert ss["drive_picker_importing"] is False
        assert ss["drive_picker_active"] is False, "Dialog closes after successful import"
