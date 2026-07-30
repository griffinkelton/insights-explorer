"""Unit tests for pages/learn.py — structural validation and content checks."""

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
        """AST parsing should succeed."""
        tree = _parse_ast()
        assert isinstance(tree, ast.Module)

    def test_no_raw_string_double_quote_collisions(self):
        """No st.code blocks should use r\"\"\" (raw double-quote) delimiters.

        These cause syntax errors when the code content contains \"\"\".
        All blocks should use ''' (single-quote triple) delimiters.
        """
        source = _read_source()
        # st.code(r""" ... """) would have been converted to st.code(''' ... ''')
        # Check that no raw double-quote triple delimiters remain in st.code calls
        double_raw = re.findall(r'st\.code\(r"""', source)
        assert len(double_raw) == 0, (
            f'Found {len(double_raw)} st.code(r""") calls — '
            "use st.code(''' instead to avoid quote collisions"
        )

    def test_imports_streamlit(self):
        """Must import streamlit at the top."""
        source = _read_source()
        assert "import streamlit as st" in source


# ── Content structure tests ──────────────────────────────────────────────────


class TestContentStructure:
    """Verify the page has the required sections and content."""

    def test_has_page_config(self):
        """Must call st.set_page_config with learn page title."""
        source = _read_source()
        assert "st.set_page_config" in source
        assert "Learn" in source
        assert "📚" in source

    def test_has_hero_section(self):
        """Hero section must have the title and description."""
        source = _read_source()
        assert "Learn Python by Exploring This App" in source
        assert "GA4 Insight Explorer" in source

    def test_has_eight_tabs(self):
        """The st.tabs() call must have exactly 8 tab labels."""
        source = _read_source()

        # Verify 8 tab variables are assigned from st.tabs()
        assert (
            "tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8" in source
        ), "st.tabs() should assign to 8 tab variables"

        # Verify all 8 'with tabN:' content blocks exist
        tab_blocks = re.findall(r"with tab\d:", source)
        assert (
            len(tab_blocks) == 8
        ), f"Expected 8 'with tabN:' content blocks, found {len(tab_blocks)}"

    def test_has_eight_concept_cards(self):
        """The quick-nav section must have exactly 8 concept cards."""
        source = _read_source()

        # Find the topics list between 'topics = [' and the next ']' at top level
        topics_match = re.search(
            r"topics\s*=\s*\[(.*?)\n\]",
            source,
            re.DOTALL,
        )
        assert topics_match is not None, "topics = [...] block not found"

        topics_block = topics_match.group(1)
        card_entries = re.findall(
            r'\("([^"]*?)",\s*"([^"]+)",\s*"([^"]+)"\)',
            topics_block,
        )
        assert len(card_entries) == 8, f"Expected 8 concept cards, found {len(card_entries)}"

        titles = [t[1] for t in card_entries]
        expected_titles = [
            "Streamlit",
            "Pandas",
            "Plotly",
            "Gemini API",
            "OAuth + GA4",
            "Type Hints",
            "Caching",
            "Testing",
        ]
        for expected in expected_titles:
            assert expected in titles, f"'{expected}' card not found in {titles}"

    def test_has_footer(self):
        """Page must have a footer with closing message."""
        source = _read_source()
        assert "Learn by exploring" in source

    def test_has_css_injection(self):
        """Learn page must call theme-aware inject_custom_css (styles now in utils/styles.py)."""
        source = _read_source()
        assert "inject_custom_css" in source
        assert "inject_favicon_meta" in source


# ── Tab content tests ────────────────────────────────────────────────────────


class TestTabContent:
    """Verify each tab contains the expected teaching content."""

    def test_each_tab_has_code_examples(self):
        """Every tab should include at least one st.code() call."""
        source = _read_source()
        code_blocks = re.findall(r"st\.code\(", source)
        assert (
            len(code_blocks) >= 16
        ), f"Expected 16+ st.code() calls (2+ per tab), found {len(code_blocks)}"

    def test_streamlit_tab_has_session_state(self):
        """Streamlit tab should teach about st.session_state."""
        source = _read_source()
        assert "st.session_state" in source

    def test_pandas_tab_has_read_csv(self):
        """Pandas tab should teach about pd.read_csv."""
        source = _read_source()
        assert "pd.read_csv" in source

    def test_plotly_tab_has_px_line(self):
        """Plotly tab should teach about px.line charts."""
        source = _read_source()
        assert "px.line" in source

    def test_gemini_tab_has_generate_content(self):
        """Gemini API tab should teach about generate_content."""
        source = _read_source()
        assert "generate_content" in source

    def test_oauth_tab_has_flow(self):
        """OAuth tab should teach about Flow.from_client_secrets_file."""
        source = _read_source()
        assert "Flow" in source
        assert "client_secrets" in source

    def test_type_hints_tab_has_union_syntax(self):
        """Type hints tab should teach about Python 3.10+ union syntax."""
        source = _read_source()
        assert "X | None" in source or "int | None" in source

    def test_caching_tab_has_cache_data(self):
        """Caching tab should teach about @st.cache_data."""
        source = _read_source()
        assert "@st.cache_data" in source

    def test_testing_tab_has_pytest(self):
        """Testing tab should teach about pytest and mocks."""
        source = _read_source()
        assert "pytest" in source
        assert "unittest.mock" in source or "patch" in source


# ── Stale content tests ──────────────────────────────────────────────────────


class TestStaleContent:
    """Verify numbers and references in the learn page match the current codebase."""

    def test_test_count_in_testing_tab_is_current(self):
        """The testing tab mentions the test count — should be >= 171.

        Note: this is intentionally a floor check, not an exact match, since
        the learn page text says '171 unit tests' and actual count is 171.
        The text will be slightly behind as tests grow.
        """
        source = _read_source()
        # The testing tab says "171 unit tests" (updated July 2026).
        # We verify it hasn't regressed below the updated count.
        match = re.search(r"(\d+)\s+unit tests", source)
        assert match is not None, "Test count not found in testing tab"
        count = int(match.group(1))
        assert count >= 171, f"Stale test count: {count} (should be >= 171)"
