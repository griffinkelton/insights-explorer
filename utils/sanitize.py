"""Shared sanitization helpers for export safety.

Prevents formula injection in spreadsheets (Excel/Sheets/CSV) and
XML/markup injection in PDF reports.
"""

from xml.sax.saxutils import escape as _xml_escape

FORMULA_PREFIXES = ("=", "+", "-", "@")


def safe_spreadsheet_value(value: object) -> object:
    """Escape values that would be interpreted as formulas by Excel/Sheets.

    Spreadsheet programs interpret cells starting with =, +, -, or @ as
    formulas. This prefixes a single quote to render them as literal text
    without changing the displayed value. Also handles leading whitespace
    and control characters that may be trimmed before formula evaluation.
    """
    if not isinstance(value, str):
        return value
    stripped = value.lstrip("\t\r\n ")
    if stripped.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def safe_pdf_text(value: object) -> str:
    """Escape text for safe use in ReportLab Paragraph markup.

    ReportLab's Paragraph class interprets XML/HTML markup. Untrusted
    text containing ``&``, ``<``, ``>`` can break formatting or be
    interpreted as markup. This escapes those characters.
    """
    return _xml_escape(str(value))
