# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in GA4 Insight Explorer, please
report it privately by creating a [GitHub security advisory](https://github.com/griffinkelton/insights-explorer/security/advisories/new).

Please do not open a public issue.

## Supported Versions

| Version | Supported |
|---------|-----------|
| v0.1.0  | ✅ |

## Security Model

GA4 Insight Explorer is a local analytics assistant that runs on your machine.
It connects to two Google services:

- **Google Gemini API** — for AI-powered analysis (requires `GEMINI_API_KEY`)
- **Google Analytics Data API** — for live GA4 data pulls (requires OAuth)

### What the app does NOT do

- Does not store, log, or retain your data beyond the active browser session
- Does not send data to third-party servers (only to the configured Google APIs)
- Does not collect analytics, telemetry, or usage data
- Does not read or list arbitrary files from Google Drive (exports only, via `drive.file` scope)

### Security boundaries in v0.1.0

- **OAuth**: PKCE flow with atomic state-file writes, redirect-URI binding, bounded state cleanup
- **Error redaction**: Raw exceptions and tracebacks are logged server-side only; users see generic error messages with incident IDs
- **Export safety**: All spreadsheet cell values are sanitized against formula injection; PDF text is XML-escaped
- **HTML safety**: Dynamic values are not interpolated into `unsafe_allow_html` Markdown blocks
- **API key**: Stored in `.env` (gitignored); validated on startup with persistent error banner
- **Least-privilege scopes**: `analytics.readonly` for GA4 pulls, `drive.file` for user-initiated exports only

### Post-v0.1.0

See [plans/audit/✅ v0.1.0-hardening-spec.md](plans/audit/✅ v0.1.0-hardening-spec.md) for deferred items and the roadmap.
