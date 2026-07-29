"""Chat command palette — /command shortcuts for pre-built query templates."""

from typing import Any

DEFAULT_COMMANDS: dict[str, dict[str, Any]] = {
    "/top-pages": {
        "label": "Top Pages",
        "icon": "📊",
        "template": "Show me the top 10 pages by sessions with a bar chart.",
        "description": "Rank pages by traffic",
    },
    "/trend": {
        "label": "Trend",
        "icon": "📈",
        "template": "Show me the daily sessions trend over time with a line chart.",
        "description": "Time-series analysis",
    },
    "/anomalies": {
        "label": "Anomalies",
        "icon": "⚠️",
        "template": "Are there any anomalies, sudden spikes, or unusual patterns in the data?",
        "description": "Detect outliers",
    },
    "/compare": {
        "label": "Compare",
        "icon": "🔬",
        "template": "Compare the top two categories by sessions side by side.",
        "description": "Side-by-side analysis",
    },
    "/funnel": {
        "label": "Funnel",
        "icon": "🔻",
        "template": "Build a conversion funnel from the most common page paths showing drop-off at each step.",
        "description": "Conversion path",
    },
    "/summary": {
        "label": "Summary",
        "icon": "📋",
        "template": "Give me a complete executive summary of this dataset with key metrics and insights.",
        "description": "Executive overview",
    },
    "/forecast": {
        "label": "Forecast",
        "icon": "🔮",
        "template": "What is the projected trend for sessions over the next 30 days based on historical data?",
        "description": "Trend projection",
    },
    "/quality": {
        "label": "Quality",
        "icon": "✅",
        "template": "What is the data quality assessment? Show completeness, duplicates, and any issues in the data.",
        "description": "Data health check",
    },
}


def resolve_command(text: str | None) -> str:
    """Resolve a /command prefix to its full template, or return the original text.

    Strips leading whitespace, checks if the first word matches a known
    command key, and returns the template if found. Case-insensitive.
    """
    if not text or not text.strip().startswith("/"):
        return text

    word = text.strip().split()[0].lower()
    if word in DEFAULT_COMMANDS:
        return DEFAULT_COMMANDS[word]["template"]
    return text


def get_command_pills() -> list[dict[str, Any]]:
    """Return the command list as a list of pill-friendly dicts.

    Each dict has: key, label, icon, template, description.
    """
    return [
        {
            "key": key,
            "label": cmd["label"],
            "icon": cmd["icon"],
            "template": cmd["template"],
            "description": cmd["description"],
        }
        for key, cmd in DEFAULT_COMMANDS.items()
    ]
