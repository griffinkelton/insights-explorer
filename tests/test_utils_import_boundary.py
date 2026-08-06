"""Phase 2 guard: shared utils/ modules must never import streamlit (spec Task 1).

Also enforces the quarantine boundary (Task 6): api/** and framework-neutral
utils/** must not import utils.styles / utils.error_boundary / utils.session
in ANY import form (review fix 2026-08-06 — the module, not the symbol, is
the boundary).

Run forever (incl. CI): `pytest tests/test_utils_import_boundary.py -q`.
"""

import ast
from pathlib import Path

SHARED_MODULES = [
    "data_loader",
    "data_context",
    "forecasting",
    "prompt_templates",
    "gemini_client",
    "ga4_client",
    "drive_client",
    "charts",
    "funnels",
    "commands",
    "sanitize",
    "report_exporter",
]

# Streamlit-only modules that MAY import streamlit (quarantined, Task 6).
QUARANTINED = {"styles", "error_boundary", "session"}

QUARANTINED_NAMES = {"styles", "error_boundary", "session"}
QUARANTINED_PATHS = {"utils.styles", "utils.error_boundary", "utils.session"}


def _imports_streamlit(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            a.name.split(".")[0] == "streamlit" for a in node.names
        ):
            return True
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.split(".")[0] == "streamlit"
        ):
            return True
    return False


def _imports_quarantined(tree: ast.AST) -> bool:
    """True if the tree imports a quarantined module in any form.

    Review fix (2026-08-06): the module, not the imported symbol, is the
    boundary. ``from utils.styles import inject_global_styles`` must be caught
    even though the symbol name is not ``styles``.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            # ``import utils.styles`` — module path is the boundary.
            if any(alias.name in QUARANTINED_PATHS for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom):
            # ``from utils.styles import foo`` is ALWAYS quarantined.
            if node.module in QUARANTINED_PATHS:
                return True
            # ``from utils import styles`` is quarantined (symbol name = module).
            if node.module == "utils":
                if any(alias.name in QUARANTINED_NAMES for alias in node.names):
                    return True
    return False


def _api_and_shared_paths():
    yield from Path("api").rglob("*.py")
    for name in SHARED_MODULES:
        yield Path("utils") / f"{name}.py"


def _uses_dynamic_imports(tree: ast.AST) -> bool:
    """Dynamic-import forms bypass AST import scanning — prohibited (2026-08-06).

    Catches ``importlib.import_module(...)`` / ``importlib.__import__(...)``,
    the builtin ``__import__(...)``, ``import importlib``, and
    ``from importlib import ...``. ``pd.eval()`` / ``df.eval()`` are NOT
    dynamic imports (Pandas arithmetic evaluation) and are deliberately not
    flagged.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                return True
            if isinstance(node.func, ast.Attribute) and node.func.attr in {
                "import_module",
                "__import__",
            }:
                return True
        if isinstance(node, ast.Import) and any(
            alias.name == "importlib" or alias.name.startswith("importlib.") for alias in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and node.module == "importlib":
            return True
    return False


def test_no_streamlit_in_shared_utils() -> None:
    for name in SHARED_MODULES:
        path = Path("utils") / f"{name}.py"
        assert path.exists(), f"module list drift: {path}"
        tree = ast.parse(path.read_text())
        assert not _imports_streamlit(tree), f"{name}.py must not import streamlit"


def test_no_streamlit_in_api() -> None:
    for path in Path("api").rglob("*.py"):
        tree = ast.parse(path.read_text())
        assert not _imports_streamlit(tree), f"{path} must not import streamlit"


def test_no_quarantined_imports_in_api_or_shared() -> None:
    """api/** and framework-neutral utils/** must not import the quarantined trio.
    Streamlit may import them; the API boundary may not (refined 2026-08-06)."""
    for path in _api_and_shared_paths():
        tree = ast.parse(path.read_text())
        assert not _imports_quarantined(tree), f"{path} must not import a STREAMLIT-ONLY module"


def test_no_dynamic_imports_in_api_or_shared() -> None:
    """api/** and shared utils/** must not use dynamic imports (2026-08-06).
    Static AST scanning cannot see ``importlib.import_module`` / ``__import__``
    — they are prohibited outright; only an explicit, reviewed allowlist (none
    currently) may relax this."""
    for path in _api_and_shared_paths():
        tree = ast.parse(path.read_text())
        assert not _uses_dynamic_imports(
            tree
        ), f"{path} uses a dynamic import — prohibited (bypasses the import boundary)"


def test_dynamic_import_forms_flagged() -> None:
    """The bypass forms must be caught; pandas eval and normal imports are not."""
    assert _uses_dynamic_imports(ast.parse('importlib.import_module("utils.styles")'))
    assert _uses_dynamic_imports(ast.parse('importlib.__import__("utils.session")'))
    assert _uses_dynamic_imports(ast.parse('__import__("utils.error_boundary")'))
    assert _uses_dynamic_imports(ast.parse("import importlib"))
    assert _uses_dynamic_imports(ast.parse("from importlib import import_module"))
    # Sanity: legitimate forms are NOT flagged.
    assert not _uses_dynamic_imports(ast.parse("import utils.data_loader"))
    assert not _uses_dynamic_imports(ast.parse('df.eval("a + b")'))
    assert not _uses_dynamic_imports(ast.parse("import pandas as pd"))


def _is_quarantined_source(source: str) -> bool:
    return _imports_quarantined(ast.parse(source))


def test_import_forms_all_caught() -> None:
    """Every import form of a quarantined module must be caught (review fix)."""
    assert _is_quarantined_source("import utils.styles")
    assert _is_quarantined_source("from utils import styles")
    assert _is_quarantined_source("from utils.styles import inject_global_styles")
    assert _is_quarantined_source("from utils.session import initialize_session_state")
    assert _is_quarantined_source("from utils.error_boundary import render_error")
    # Sanity: legit imports are NOT flagged.
    assert not _is_quarantined_source("from utils import data_loader")
    assert not _is_quarantined_source("from utils.data_loader import load_file")
    assert not _is_quarantined_source("import streamlit as st")
    assert not _is_quarantined_source("import pandas as pd")


def test_quarantine_banners_present() -> None:
    for name in QUARANTINED:
        path = Path("utils") / f"{name}.py"
        assert (
            "STREAMLIT-ONLY" in path.read_text()
        ), f"{name}.py missing STREAMLIT-ONLY banner (Task 6)"
