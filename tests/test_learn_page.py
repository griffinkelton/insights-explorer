"""Unit tests for pages/learn.py — v0.2.0 interactive learning experience.

Validates the new side-navigation structure, the 6 priority learning challenges,
progressive disclosure, and content rules from the pedagogical spec.
"""

import ast
import re

LEARN_PAGE = "pages/learn.py"


def _read_source() -> str:
    with open(LEARN_PAGE) as f:
        return f.read()


def _parse_ast() -> ast.Module:
    return ast.parse(_read_source(), filename=LEARN_PAGE)


# ── Syntax & import tests ────────────────────────────────────────────────────


class TestSyntax:
    def test_parses_without_syntax_error(self):
        tree = _parse_ast()
        assert isinstance(tree, ast.Module)

    def test_imports_streamlit(self):
        source = _read_source()
        assert "import streamlit as st" in source

    def test_imports_learning_challenge(self):
        source = _read_source()
        assert "from components.learning_challenge import" in source


# ── Navigation structure ─────────────────────────────────────────────────────


class TestNavigationStructure:
    """Verify the new side-navigation layout (not the old tabs)."""

    def test_has_side_navigation_columns(self):
        """Page must use column layout for side navigation, not flat tabs."""
        source = _read_source()
        assert "nav_col, content_col" in source
        assert "st.columns([1, 3])" in source

    def test_has_radio_section_selector(self):
        source = _read_source()
        assert "st.radio" in source
        assert "SECTIONS" in source

    def test_has_correct_8_sections(self):
        source = _read_source()
        expected = [
            "Start here",
            "Follow the data",
            "Explore & analyze",
            "Ask AI well",
            "Privacy & safety",
            "How it is built",
            "Guided challenges",
            "Where next",
        ]
        for exp in expected:
            assert exp in source, f"Section '{exp}' not found"

    def test_has_hero_section(self):
        source = _read_source()
        assert "Learn How Insight Explorer Works" in source

    def test_has_back_link(self):
        source = _read_source()
        assert "← Back to App" in source


# ── Challenge integration tests ──────────────────────────────────────────────


class TestChallengeIntegration:
    """Verify the 6 priority challenges are present and correctly configured."""

    def test_has_6_learning_challenges(self):
        source = _read_source()
        challenge_calls = re.findall(r"render_learning_challenge\(", source)
        assert (
            len(challenge_calls) >= 6
        ), f"Expected 6+ challenge calls, found {len(challenge_calls)}"

    def test_L2_lifecycle_ordering_challenge_exists(self):
        source = _read_source()
        assert "learn.follow_data.lifecycle_order.v1" in source
        assert '"sequence"' in source
        assert "raw_df" in source

    def test_L3_clear_filter_challenge_exists(self):
        source = _read_source()
        assert "learn.follow_data.clear_filter.v1" in source
        assert "conversion_rate" in source

    def test_L4_metric_rebuild_challenge_exists(self):
        source = _read_source()
        assert "learn.explore.metric_rebuild.v1" in source
        assert "revenue_per_user" in source or "June" in source

    def test_L6_evidence_check_challenge_exists(self):
        source = _read_source()
        assert "learn.explore.evidence_check.v1" in source
        assert '"evidence_check"' in source

    def test_L7_prompt_improve_challenge_exists(self):
        source = _read_source()
        assert "learn.ai.prompt_improve.v1" in source
        assert '"prompt_rewrite"' in source

    def test_L9_privacy_scenario_challenge_exists(self):
        source = _read_source()
        assert "learn.privacy.scenario.v1" in source
        assert '"scenario_choice"' in source

    def test_where_look_challenge_exists(self):
        """The builder section has its own 'Where do I look?' challenge."""
        source = _read_source()
        assert "learn.build.where_look.v1" in source

    def test_challenges_use_namespaced_keys(self):
        """Challenge keys must use the learn.* namespace."""
        source = _read_source()
        keys = re.findall(r'key="(learn\.[^"]+)"', source)
        assert len(keys) >= 7, f"Expected 7+ namespaced keys, found {len(keys)}"
        for k in keys:
            assert k.startswith("learn."), f"Key '{k}' doesn't use learn.* namespace"


# ── Before-you-conclude checklist ────────────────────────────────────────────


class TestBeforeYouConclude:
    def test_checklist_present(self):
        source = _read_source()
        assert "render_before_you_conclude" in source

    def test_checklist_in_explore_section(self):
        """The 'Before you conclude' checklist should appear in Explore & analyze."""
        source = _read_source()
        # It appears only once, in the Explore & analyze section
        assert source.count("render_before_you_conclude()") >= 1


# ── Progressive disclosure ───────────────────────────────────────────────────


class TestProgressiveDisclosure:
    def test_has_go_deeper_expander(self):
        source = _read_source()
        assert "Go deeper" in source

    def test_has_show_answer_expander(self):
        """Learning challenge component must support 'Show answer' for accessibility."""
        # This is in components/learning_challenge.py, not pages/learn.py
        with open("components/learning_challenge.py") as f:
            component_source = f.read()
        assert "Show answer" in component_source
        assert "st.expander" in component_source


# ── Repository architecture section ─────────────────────────────────────────


class TestArchitectureSection:
    def test_has_repository_map(self):
        source = _read_source()
        assert "Repository map" in source
        assert "app.py" in source
        assert "components/" in source
        assert "utils/" in source
        assert "tests/" in source

    def test_has_data_contract_excerpt(self):
        source = _read_source()
        assert "frozen=True" in source
        assert "DataContext" in source

    def test_has_safe_change_recipe(self):
        source = _read_source()
        assert "Safe-change recipe" in source
        assert "Name the behavior" in source or "Name the" in source

    def test_has_go_deeper_links(self):
        source = _read_source()
        assert "README.md" in source
        assert "ARCHITECTURE.md" in source
        assert "SECURITY.md" in source


# ── Content safety ───────────────────────────────────────────────────────────


class TestNoStaleContent:
    def test_no_old_tab_patterns(self):
        """No references to the old 8-tab assignment pattern."""
        source = _read_source()
        # Old pattern: tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
        assert "tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8" not in source

    def test_no_hardcoded_test_count(self):
        source = _read_source()
        exact_count = re.search(r'"\d+\s+(unit )?tests"', source)
        assert exact_count is None, f"Hardcoded test count: {exact_count.group(0)}"

    def test_no_in_memory_only_claim(self):
        source = _read_source()
        assert "in‑memory only" not in source
        assert "in-memory only" not in source

    def test_no_line_number_references(self):
        source = _read_source()
        file_badge_refs = re.findall(r"file-badge.*\.py:\d+", source)
        assert (
            len(file_badge_refs) == 0
        ), f"Found {len(file_badge_refs)} line-number references in file badges"

    def test_no_prompt_injection_hack(self):
        source = _read_source()
        assert "prompt injection" not in source.lower()
        assert "prompt-injection" not in source.lower()

    def test_no_credentials_in_source(self):
        """Learn page must not contain credential patterns."""
        source = _read_source()
        assert "api_key" not in source.lower() or "api key" in source.lower()


# ── Section-specific content ─────────────────────────────────────────────────


class TestSectionContent:
    def test_start_here_has_first_goal(self):
        source = _read_source()
        assert "first goal" in source.lower() or "load data" in source.lower()

    def test_follow_data_has_three_layer_table(self):
        source = _read_source()
        assert "raw_df" in source
        assert "base_df" in source
        assert "active_df" in source

    def test_explore_has_toolkit_table(self):
        source = _read_source()
        assert "analysis toolkit" in source.lower() or "trend chart" in source.lower()

    def test_ask_ai_has_what_reaches_gemini(self):
        source = _read_source()
        assert "Gemini" in source
        assert "token" in source.lower()

    def test_privacy_has_scope_info(self):
        source = _read_source()
        assert "analytics.readonly" in source
        assert "drive.file" in source

    def test_how_built_says_optional(self):
        source = _read_source()
        assert "optional" in source.lower() or "do not need" in source.lower()

    def test_guided_has_three_missions(self):
        source = _read_source()
        assert "Beginner" in source
        assert "Intermediate" in source
        assert "Advanced" in source

    def test_where_next_has_docs(self):
        source = _read_source()
        assert "ARCHITECTURE.md" in source
        assert "README.md" in source
