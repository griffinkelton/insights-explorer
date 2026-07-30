"""pytest configuration — shared fixtures, warning filters, and markers."""


def pytest_configure(config):
    """Register warning filters before test collection."""
    # google.genai uses a deprecated stdlib type; suppress until upstream fixes it.
    config.addinivalue_line(
        "filterwarnings",
        "ignore::DeprecationWarning:google.genai.*",
    )
