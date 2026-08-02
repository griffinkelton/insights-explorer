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

    def test_no_drive_picker_function(self):
        """v0.1.0: _render_drive_picker was removed (Drive import removed)."""
        source = open(MODULE).read()
        assert "def _render_drive_picker()" not in source

    def test_clear_data_uses_button_if_pattern(self):
        """Clear Data must use `if st.button(...)` pattern per BUG-005."""
        source = open(MODULE).read()
        assert "if st.button" in source
        assert "clear_data()" in source


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
