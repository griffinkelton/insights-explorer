"""Smoke tests for export functions and error classification."""

import pandas as pd
import pytest

from utils.gemini_client import _classify_api_error
from utils.report_exporter import build_excel_report, build_pdf_report


class TestClassifyApiError:
    """Unit tests for the pure error classification function."""

    def test_rate_limit_429(self):
        """429 errors should classify as rate limit."""
        e = Exception("429 RESOURCE_EXHAUSTED")
        result = _classify_api_error(e)
        assert "Rate limit" in result

    def test_auth_403(self):
        """403 errors should classify as API key issue."""
        e = Exception("403 PERMISSION_DENIED")
        result = _classify_api_error(e)
        assert "API key" in result

    def test_server_500(self):
        """500 errors should classify as service error."""
        e = Exception("500 INTERNAL")
        result = _classify_api_error(e)
        assert "service error" in result

    def test_unknown_error_fallback(self):
        """Unknown errors should return a generic message without raw internals."""
        e = Exception("something completely unexpected")
        result = _classify_api_error(e)
        assert "Gemini could not complete" in result
        assert "something completely unexpected" not in result


class TestExcelExport:
    def test_valid_input_returns_bytes(self):
        """build_excel_report with valid DataFrame returns bytes."""
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = build_excel_report(df=df)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_missing_openpyxl_raises(self, monkeypatch):
        """build_excel_report raises RuntimeError when openpyxl not installed."""
        monkeypatch.setattr("utils.report_exporter.HAS_OPENPYXL", False)
        with pytest.raises(RuntimeError, match="openpyxl"):
            build_excel_report()


class TestPdfExport:
    def test_valid_input_returns_bytes(self):
        """build_pdf_report with valid input returns bytes."""
        result = build_pdf_report(
            summary="Test summary",
            stats={"row_count": 100, "column_count": 5},
            chat_history=[{"question": "Q1", "response": "A1"}],
        )
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_missing_reportlab_raises(self, monkeypatch):
        """build_pdf_report raises RuntimeError when reportlab not installed."""
        monkeypatch.setattr("utils.report_exporter.HAS_REPORTLAB", False)
        with pytest.raises(RuntimeError, match="reportlab"):
            build_pdf_report()
