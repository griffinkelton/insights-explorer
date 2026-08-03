"""Tests for components/hero.py — 5-test pattern."""

import ast

HERO = "components/hero.py"


def _parse() -> ast.Module:
    with open(HERO) as f:
        return ast.parse(f.read(), filename=HERO)


class TestHeroSyntax:
    def test_parses_without_syntax_error(self):
        tree = _parse()
        assert isinstance(tree, ast.Module)


class TestHeroImport:
    def test_module_imports_without_error(self):
        from components.hero import render_hero

        assert callable(render_hero)


class TestHeroStructure:
    def test_has_render_hero_function(self):
        source = open(HERO).read()
        assert "def render_hero()" in source

    def test_no_on_click_anti_pattern(self):
        source = open(HERO).read()
        assert "on_click=" not in source

    def test_no_bare_except_exception(self):
        source = open(HERO).read()
        # Allow only if there's a comment explaining it
        lines = source.split("\n")
        for i, line in enumerate(lines):
            if "except Exception" in line and "pass" in line:
                # Check nearby lines for a comment explaining the reason
                context = "\n".join(lines[max(0, i - 1) : i + 1])
                assert "#" in context, f"except Exception: pass without comment at line {i + 1}"


# ── Interstitial PR-L3 (Workstream B): A1 hero light-mode classes ─────────


class TestHeroLightTokens:
    """A1: hero uses the .hero-* class set — no inline theme colors remain."""

    def test_hero_uses_class_set(self):
        source = open(HERO).read()
        for cls in (
            'class="hero-section"',
            'class="hero-emoji"',
            'class="hero-title"',
            'class="hero-subtitle"',
            'class="hero-cards"',
            'class="hero-card"',
            'class="hero-card-icon"',
            'class="hero-card-title"',
            'class="hero-card-caption"',
            'class="hero-hint"',
        ):
            assert cls in source, f"{cls} missing from hero markup"

    def test_no_raw_hexes_in_hero(self):
        """All former inline dark-palette values moved to CSS classes."""
        source = open(HERO).read()
        for hex_code in (
            "#9898b0",  # subtitle (was --text-secondary)
            "#1a1a26",  # cards (was --bg-card)
            "#f0f0f5",  # card titles (was --text-primary)
            "#686880",  # captions/hint (was --text-muted)
            "#c4b5fd",  # hero-title gradient
            "#818cf8",
            "#6366f1",
        ):
            assert hex_code not in source, f"{hex_code} hard-coded in hero"
        assert "rgba(255,255,255,0.06)" not in source, "dark border still inline"
