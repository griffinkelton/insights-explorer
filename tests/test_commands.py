"""Tests for utils/commands.py — command palette templates and resolution."""

import ast
from utils.commands import (
    resolve_command,
    get_command_pills,
    DEFAULT_COMMANDS,
)

MODULE = "utils/commands.py"
CHAT = "components/chat.py"


def _parse(path: str) -> ast.Module:
    with open(path) as f:
        return ast.parse(f.read(), filename=path)


# ── Structural tests ────────────────────────────────────────────────────────


class TestCommandsSyntax:
    def test_module_parses(self):
        tree = _parse(MODULE)
        assert isinstance(tree, ast.Module)

    def test_chat_parses(self):
        tree = _parse(CHAT)
        assert isinstance(tree, ast.Module)


class TestCommandsStructure:
    def test_has_default_commands(self):
        source = open(MODULE).read()
        assert "DEFAULT_COMMANDS" in source

    def test_has_resolve_command(self):
        source = open(MODULE).read()
        assert "def resolve_command(" in source

    def test_has_get_command_pills(self):
        source = open(MODULE).read()
        assert "def get_command_pills(" in source

    def test_chat_imports_commands(self):
        source = open(CHAT).read()
        assert "from utils.commands import" in source

    def test_chat_has_command_pills(self):
        source = open(CHAT).read()
        assert "def _render_command_pills()" in source

    def test_chat_calls_resolve_command(self):
        source = open(CHAT).read()
        assert "resolve_command(prompt)" in source

    def test_has_eight_default_commands(self):
        assert len(DEFAULT_COMMANDS) == 8

    def test_all_commands_have_required_keys(self):
        for key, cmd in DEFAULT_COMMANDS.items():
            assert "label" in cmd, f"{key} missing label"
            assert "icon" in cmd, f"{key} missing icon"
            assert "template" in cmd, f"{key} missing template"
            assert "description" in cmd, f"{key} missing description"

    def test_all_keys_start_with_slash(self):
        for key in DEFAULT_COMMANDS:
            assert key.startswith("/"), f"{key} doesn't start with /"


# ── Unit tests: resolve_command ─────────────────────────────────────────────


class TestResolveCommand:
    def test_resolves_known_command(self):
        result = resolve_command("/top-pages")
        assert "top 10 pages" in result.lower()
        assert "bar chart" in result.lower()

    def test_resolves_case_insensitive(self):
        result = resolve_command("  /TREND  ")
        assert "trend" in result.lower()
        assert "line chart" in result.lower()

    def test_passes_through_non_command(self):
        text = "what are the top pages?"
        result = resolve_command(text)
        assert result == text

    def test_passes_through_empty(self):
        assert resolve_command("") == ""
        assert resolve_command("   ") == "   "

    def test_passes_through_none(self):
        # Should handle falsy input gracefully
        assert resolve_command(None) is None  # type: ignore[arg-type]

    def test_unknown_slash_command_passes_through(self):
        text = "/unknown-command extra text"
        result = resolve_command(text)
        assert result == text

    def test_each_command_resolves(self):
        for key, cmd in DEFAULT_COMMANDS.items():
            result = resolve_command(key)
            assert result == cmd["template"], f"{key} didn't resolve correctly"
            assert len(result) > 10


# ── Unit tests: get_command_pills ───────────────────────────────────────────


class TestGetCommandPills:
    def test_returns_list_of_dicts(self):
        pills = get_command_pills()
        assert isinstance(pills, list)
        assert len(pills) == len(DEFAULT_COMMANDS)

    def test_each_pill_has_required_keys(self):
        for pill in get_command_pills():
            for k in ("key", "label", "icon", "template", "description"):
                assert k in pill, f"pill missing {k}"


# ── Imports smoke test ───────────────────────────────────────────────────────


class TestCommandsImports:
    def test_resolve_command_importable(self):
        assert callable(resolve_command)

    def test_get_command_pills_importable(self):
        assert callable(get_command_pills)
