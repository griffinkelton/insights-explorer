"""Unit tests for pages/learn.py — v0.2.0 8-section learner's journey.

Validates structure, content, and the absence of stale patterns from the
pre-v0.2.0 technology-centric 8-tab layout.
"""

import ast
import re

LEARN_PAGE = "pages/learn.py"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _read_source() -> str:
    with open(LEARN_PAGE) as f:
        return f.read()


def _parse_ast() -> ast.Module:
    return ast.parse(_read_source(), filename=LEARN_PAGE)


# ── Syntax & import tests ────────────────────────────────────────────────────


class TestSyntax:
    """Verify the file parses without syntax errors."""

    def test_parses_without_syntax_error(self):
        tree = _parse_ast()
        assert isinstance(tree, ast.Module)

    def test_imports_streamlit(self):
        source = _read_source()
        assert "import streamlit as st" in source


# ── Content structure tests ──────────────────────────────────────────────────


class TestContentStructure:
    """Verify the page has the required v0.2.0 sections."""

    def test_has_page_config(self):
        source = _read_source()
        assert "st.set_page_config" in source
        assert "Learn" in source
        assert "📚" in source

    def test_has_hero_section(self):
        source = _read_source()
        assert "Learn How Insight Explorer Works" in source

    def test_has_eight_tabs(self):
        """st.tabs() must have exactly 8 tab labels (learner-journey sections)."""
        source = _read_source()

        # Verify 8 tab variables are assigned
        assert (
            "tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8" in source
        ), "st.tabs() should assign to 8 tab variables"

        # Verify all 8 'with tabN:' content blocks exist
        tab_blocks = re.findall(r"with tab\d:", source)
        assert len(tab_blocks) == 8, f"Expected 8 'with tabN:' blocks, found {len(tab_blocks)}"

    def test_has_correct_tab_labels(self):
        """Tab labels must match the v0.2.0 learner-journey structure."""
        source = _read_source()
        expected_sections = [
            "Start here",
            "Follow the data",
            "Explore & analyze",
            "Ask AI well",
            "Privacy & safety",
            "Build it in Python",
            "Guided challenges",
            "Where next",
        ]
        for expected in expected_sections:
            assert expected in source, f"Section '{expected}' not found in tab labels"

    def test_has_footer(self):
        source = _read_source()
        assert "content reflects v0.2.0 architecture" in source

    def test_has_css_injection(self):
        source = _read_source()
        assert "inject_custom_css" in source
        assert "inject_favicon_meta" in source

    def test_has_back_link(self):
        source = _read_source()
        assert "← Back to App" in source

    def test_each_tab_has_code_examples(self):
        """Every section should include at least one st.code() call."""
        source = _read_source()
        code_blocks = re.findall(r"st\.code\(", source)
        assert len(code_blocks) >= 8, f"Expected 8+ st.code() calls, found {len(code_blocks)}"


# ── Section-specific content tests ───────────────────────────────────────────


class TestSectionContent:
    """Verify each section covers its intended topic."""

    def test_start_here_has_quick_tasks(self):
        source = _read_source()
        assert "what you can do" in source.lower()
        assert "Upload" in source
        assert "Generate Summary" in source

    def test_follow_the_data_has_datacontext(self):
        source = _read_source()
        assert "DataContext" in source
        assert "raw_df" in source
        assert "base_df" in source
        assert "active_df" in source

    def test_explore_and_analyze_has_charts(self):
        source = _read_source()
        assert "Plotly" in source or "plotly" in source.lower()
        assert "forecasting" in source.lower() or "forecast" in source.lower()
        assert "funnel" in source.lower()

    def test_ask_ai_well_has_gemini(self):
        source = _read_source()
        assert "Gemini" in source
        assert "prompt" in source.lower()
        assert "token" in source.lower()

    def test_privacy_and_safety_has_security(self):
        source = _read_source()
        assert "session" in source.lower()
        assert "OAuth" in source
        assert "scope" in source.lower()
        assert "SECURITY.md" in source

    def test_build_in_python_has_step_by_step(self):
        source = _read_source()
        assert "Step 1" in source
        assert "Step 2" in source
        assert "pytest" in source

    def test_guided_challenges_has_three_levels(self):
        source = _read_source()
        assert "Beginner" in source
        assert "Intermediate" in source
        assert "Advanced" in source

    def test_where_next_has_docs(self):
        source = _read_source()
        assert "ARCHITECTURE.md" in source
        assert "README.md" in source
        assert "contributing" in source.lower() or "Contributing" in source

    def test_has_see_also_references(self):
        """Most sections should have 'See also' footer links."""
        source = _read_source()
        # Count "See also:" occurrences
        see_alsos = re.findall(r"See also:", source)
        assert len(see_alsos) >= 6, f"Expected 6+ 'See also' references, found {len(see_alsos)}"

    def test_has_tip_boxes(self):
        """Sections should include tip-box divs with key insights."""
        source = _read_source()
        tip_boxes = re.findall(r"tip-box", source)
        assert len(tip_boxes) >= 5, f"Expected 5+ tip-box divs, found {len(tip_boxes)}"


# ── Stale content tests (negative checks) ────────────────────────────────────


class TestNoStaleContent:
    """Verify the v0.2.0 Learn page does NOT contain outdated material."""

    def test_no_old_tab_labels(self):
        """No references to the old technology-centric tab names as primary labels."""
        source = _read_source()
        old_labels = [
            "🏗️ Streamlit",
            "🐼 Pandas",
            "📈 Plotly",
            "🤖 Gemini API",
            "🔐 OAuth + GA4",
            "🏷️ Type Hints",
            "⚡ Caching",
            "🧪 Testing",
        ]
        # Only check that the OLD labels aren't in the current tabs declaration
        # (they may still appear in code excerpts as library names)
        tabs_match = re.search(r"st\.tabs\(\s*\[(.*?)\]", source, re.DOTALL)
        if tabs_match:
            tabs_block = tabs_match.group(1)
            for old in old_labels:
                assert old not in tabs_block, f"Old tab label '{old}' found in tabs declaration"

    def test_no_hardcoded_test_count(self):
        """The Learn page should not hardcode a specific test count."""
        source = _read_source()
        # The old page had "171 unit tests" — the new page uses "over 500" or similar
        # No exact test counts should appear
        exact_count = re.search(r'"\d+\s+unit tests"', source)
        assert exact_count is None, f"Hardcoded test count found: {exact_count.group(0)}"

    def test_no_in_memory_only_claim(self):
        """The privacy section should not use the vague 'in-memory only' phrase."""
        source = _read_source()
        assert "in‑memory only" not in source
        assert "in-memory only" not in source

    def test_no_line_number_references(self):
        """Code excerpts should not reference line numbers (brittle)."""
        source = _read_source()
        # The old page had patterns like `<span class="file-badge">app.py:29</span>`
        file_badge_refs = re.findall(r"file-badge.*\.py:\d+", source)
        assert (
            len(file_badge_refs) == 0
        ), f"Found {len(file_badge_refs)} line-number references in file badges"

    def test_no_prompt_injection_hack(self):
        """No references to prompt-injection techniques."""
        source = _read_source()
        assert "prompt injection" not in source.lower()
        assert "prompt-injection" not in source.lower()
