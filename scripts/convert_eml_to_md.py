"""Convert .eml email files to readable Markdown files.

Usage: python scripts/convert_eml_to_md.py
Reads all .eml files from email/ and writes .md files to the same directory.
"""

import email
import email.policy
import re
import html
from pathlib import Path

EMAIL_DIR = Path("email")

# Characters that should not appear in the decoded text after proper decoding
QUOTED_PRINTABLE_FLAGS = re.compile(r"=\r?\n")  # soft line breaks
QUOTED_PRINTABLE_CHARS = re.compile(r"=([0-9A-Fa-f]{2})")


def decode_quoted_printable(text: str) -> str:
    """Decode quoted-printable encoded text."""
    # Remove soft line breaks
    text = QUOTED_PRINTABLE_FLAGS.sub("", text)

    # Decode =XX hex sequences
    def hex_replace(m):
        return chr(int(m.group(1), 16))

    return QUOTED_PRINTABLE_CHARS.sub(hex_replace, text)


def strip_html(text: str) -> str:
    """Strip HTML tags and convert to plain text."""
    # Remove style/script tags and their content
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Replace <br> and <br/> with newlines
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    # Replace </p> <p> boundaries with double newline
    text = re.sub(r"</p>\s*<p[^>]*>", "\n\n", text, flags=re.IGNORECASE)
    # Replace closing block tags with newline
    text = re.sub(r"</(div|p|tr|h\d|li|td|th)>", "\n", text, flags=re.IGNORECASE)
    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode HTML entities
    text = html.unescape(text)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Trim leading/trailing whitespace per line
    lines = [line.strip() for line in text.split("\n")]
    # Remove empty lines at start/end
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def extract_headers(msg) -> dict:
    """Extract key headers from an email message."""
    return {
        "From": msg.get("From", ""),
        "To": msg.get("To", ""),
        "Date": msg.get("Date", ""),
        "Subject": msg.get("Subject", "(No Subject)"),
    }


def get_body_text(msg) -> str:
    """Extract the body text from an email message.

    Prefers plain text; falls back to stripped HTML.
    """
    if msg.is_multipart():
        plain_parts = []
        html_parts = []
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        text = payload.decode(charset)
                    except (UnicodeDecodeError, LookupError):
                        text = payload.decode("utf-8", errors="replace")
                    plain_parts.append(text)
            elif content_type == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        text = payload.decode(charset)
                    except (UnicodeDecodeError, LookupError):
                        text = payload.decode("utf-8", errors="replace")
                    html_parts.append(text)

        # Prefer plain text, use HTML as fallback
        if plain_parts:
            return plain_parts[0]  # First plain text part
        elif html_parts:
            return strip_html(html_parts[0])  # First HTML part
        return ""
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            try:
                return payload.decode(charset)
            except (UnicodeDecodeError, LookupError):
                return payload.decode("utf-8", errors="replace")
    return ""


def deduplicate_signatures(text: str) -> str:
    """Remove repeated email signature blocks from forwarded threads."""
    # Split on common forwarded-message/thread boundary markers
    # We look for repeated patterns like "Vivian Vasallo" blocks
    lines = text.split("\n")
    result = []
    skip_until_blank = False

    for i, line in enumerate(lines):
        # Detect signature markers (email signatures that repeat in threads)
        stripped = line.strip()

        # Skip Outlook "Book time to meet with me" link blocks
        if "Book time to meet with me" in stripped:
            skip_until_blank = True
            continue

        if skip_until_blank:
            if not stripped:
                skip_until_blank = False
            continue

        # Skip image removed placeholders
        if stripped == "[image: Image removed by sender.]":
            continue

        # Skip empty signature table remnants
        if stripped.startswith("Book time") or stripped.startswith("<https://outlook"):
            continue

        result.append(line)

    return "\n".join(result)


def build_markdown_headers(headers: dict) -> str:
    """Build Markdown header block."""
    lines = []
    lines.append(f"# {headers['Subject']}")
    lines.append("")
    if headers.get("From"):
        lines.append(f"**From:** {headers['From']}")
    if headers.get("To"):
        lines.append(f"**To:** {headers['To']}")
    if headers.get("Date"):
        lines.append(f"**Date:** {headers['Date']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def convert_eml_to_md(eml_path: Path) -> Path:
    """Convert a single .eml file to .md."""
    raw = eml_path.read_bytes()
    msg = email.message_from_bytes(raw, policy=email.policy.default)

    headers = extract_headers(msg)
    body = get_body_text(msg)
    body = deduplicate_signatures(body)

    md_content = build_markdown_headers(headers) + body.strip() + "\n"

    md_path = eml_path.with_suffix(".md")
    md_path.write_text(md_content, encoding="utf-8")
    return md_path


def main():
    eml_files = sorted(EMAIL_DIR.glob("*.eml"))
    if not eml_files:
        print(f"No .eml files found in {EMAIL_DIR}/")
        return

    print(f"Found {len(eml_files)} .eml file(s):\n")
    for eml_path in eml_files:
        md_path = convert_eml_to_md(eml_path)
        print(f"  ✅ {eml_path.name}  →  {md_path.name}")

    print(f"\nDone! {len(eml_files)} file(s) converted.")


if __name__ == "__main__":
    main()
