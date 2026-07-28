"""Static analysis linters — catches structural bugs that AST parsing alone misses.

Pattern 4 (BUG-002): Verifies function definitions appear BEFORE their
    first call site at the module level in app.py. Streamlit scripts
    execute top-to-bottom, so `def _render_main()` after `_render_main()`
    is a NameError at runtime. ast.parse doesn't catch this.

Pattern 3 (BUG-006): Verifies that file-I/O functions like
    `load_file()` don't mix `file.read()` with `pd.read_csv(file)` on
    the same file object (which consumes the buffer). Checks that
    BytesIO is used as a wrapper when both operations exist.
"""

import ast
import os
import textwrap


ROOT = os.path.dirname(os.path.dirname(__file__))


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _parse(path: str) -> ast.Module:
    """Parse a Python file into an AST."""
    with open(path) as f:
        return ast.parse(f.read(), filename=path)


def _find_module_level_calls(tree: ast.Module) -> list[tuple[str, int]]:
    """Return [(function_name, line_number)] for Call nodes at module level only.

    Only walks top-level statements that are NOT function/class definitions.
    Calls inside function bodies are fine — they only run at invocation time,
    not at module load time. The bug (BUG-002) only triggers for module-level
    calls that execute during the Streamlit script's top-to-bottom execution.

    Recurses into compound statements (Try, If, With, For, While) at module
    level — e.g., `try: _render_main()` is detected because ast.walk(stmt)
    descends into the Try body.
    """
    calls: list[tuple[str, int]] = []
    for stmt in tree.body:
        # Skip function/class definitions entirely — their bodies don't
        # execute at module load time
        if isinstance(stmt, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            continue
        # Walk the statement for Call nodes (handles try/except, if/else,
        # expression statements, etc.)
        for node in ast.walk(stmt):
            if isinstance(node, ast.Call):
                name = _call_target_name(node)
                if name:
                    calls.append((name, node.lineno))
    return calls


def _find_defs(tree: ast.Module) -> dict[str, int]:
    """Return {function_name: line_number} for all FunctionDef nodes.

    If a function is defined multiple times (shouldn't happen), takes the first.
    """
    defs: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name not in defs:
                defs[node.name] = node.lineno
    return defs


def _call_target_name(node: ast.Call) -> str | None:
    """Extract the function name from a Call node.

    Handles: foo(), obj.foo(), module.foo()
    Returns None for: foo()[0](), lambda calls, etc.
    """
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


# ═══════════════════════════════════════════════════════════════════════════
# Pattern 4: def-before-call (BUG-002)
# ═══════════════════════════════════════════════════════════════════════════

class TestDefBeforeCall:
    """Verify every function definition appears before its first call site.

    Streamlit executes scripts top-to-bottom. A function called before
    its `def` statement is a NameError at runtime. ast.parse alone
    won't catch this — it only checks syntax, not execution order.
    """

    APP_PATH = os.path.join(ROOT, "app.py")

    def test_all_defs_before_module_level_calls(self):
        """Every function defined in app.py must be defined before any
        module-level call to it. Calls inside function bodies are fine —
        they only execute at invocation time, not at script load."""
        tree = _parse(self.APP_PATH)
        defs = _find_defs(tree)
        calls = _find_module_level_calls(tree)

        violations: list[str] = []
        for func_name, call_line in calls:
            if func_name in defs and call_line < defs[func_name]:
                violations.append(
                    f"{func_name}() called at line {call_line} "
                    f"but defined at line {defs[func_name]}"
                )

        if violations:
            msg = (
                "Functions called before their definitions in app.py "
                "(will cause NameError at runtime):\n  "
                + "\n  ".join(violations)
                + "\n\nMove the function definition above the call site."
            )
            raise AssertionError(msg)

    def test_synthetic_try_block_call_detected(self):
        """Prove the linter catches calls inside try: blocks at module level.

        This is the exact BUG-002 pattern: `try: _render_main()` where
        `def _render_main()` appears later in the file. The linter must
        recurse into Try nodes (and If, With, etc.) to find these calls.
        """
        source = textwrap.dedent("""\
            import streamlit as st

            try:
                _render_main()
            except Exception:
                st.error("Something went wrong")

            def _render_main():
                st.write("Hello")
        """)
        tree = ast.parse(source)
        defs = _find_defs(tree)
        calls = _find_module_level_calls(tree)

        # _render_main() inside try: must be detected
        assert ("_render_main", 4) in calls, (
            "BUG-002 linter failed to detect a call inside a try: block. "
            "Module-level compound statements (try/if/with/for/while) must "
            "be recursed into to find calls."
        )
        # And it's called before its definition
        assert "_render_main" in defs
        assert calls[0][1] < defs["_render_main"], (
            f"Expected _render_main() call (line {calls[0][1]}) before "
            f"definition (line {defs['_render_main']})"
        )

    def test_synthetic_correct_order_passes(self):
        """Def-before-call (the normal case) should produce no violations."""
        source = textwrap.dedent("""\
            import streamlit as st

            def _render_main():
                st.write("Hello")

            try:
                _render_main()
            except Exception:
                st.error("Something went wrong")
        """)
        tree = ast.parse(source)
        defs = _find_defs(tree)
        calls = _find_module_level_calls(tree)

        violations = [
            (name, line) for name, line in calls
            if name in defs and line < defs[name]
        ]
        assert not violations, (
            f"Correctly-ordered code flagged as violation: {violations}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Pattern 3: file I/O guard (BUG-006)
# ═══════════════════════════════════════════════════════════════════════════

class TestFileIOGuard:
    """Verify file-I/O patterns don't consume buffers before pandas reads.

    BUG-006: Reading a file with file.read() then passing the same file
    object to pd.read_csv() consumes the buffer — pandas gets zero bytes.
    The fix: read into bytes, wrap in BytesIO, pass to pandas.

    Note: These checks use simple string matching on the source code,
    which is fragile — renaming variables (file → uploaded_file) or
    using indirect calls won't be caught. This is acceptable for a
    lightweight forward-looking CI guard. For comprehensive detection,
    a proper AST-based taint analysis would be needed.
    """

    DATA_LOADER_PATH = os.path.join(ROOT, "utils", "data_loader.py")

    def test_data_loader_does_not_reuse_file_object(self):
        """load_file() must not call both file.read() AND pd.read_csv(file)
        on the same file object without a BytesIO wrapper."""
        source = self._read()

        has_file_read = "file.read()" in source or "file.getvalue()" in source
        has_pandas_read = "pd.read_csv(" in source or "pd.read_excel(" in source
        has_bytesio = "BytesIO" in source

        if has_file_read and has_pandas_read:
            # If both operations exist, BytesIO must be used as a wrapper
            assert has_bytesio, (
                "data_loader.py calls both file.read()/file.getvalue() and "
                "pd.read_csv()/pd.read_excel() on the same file object, "
                "but BytesIO is not used. The file buffer will be consumed "
                "by the first read and pandas will get zero bytes. "
                "Fix: from io import BytesIO; "
                "file_bytes = file.read(); "
                "df = pd.read_csv(BytesIO(file_bytes))"
            )

    def test_bytesio_imported_when_needed(self):
        """If load_file reads file bytes, BytesIO should be imported from io.

        This is a forward-looking guard — the current code doesn't call
        file.read(), so the test passes trivially. When file.read() is
        added (e.g., for size checking in IMPL #4), this will enforce
        the BytesIO import.
        """
        source = self._read()

        has_file_read = "file.read()" in source or "file.getvalue()" in source
        has_bytesio_import = "from io import BytesIO" in source or "import BytesIO" in source
        has_bytesio_usage = "BytesIO(" in source

        if has_file_read and not has_bytesio_import and not has_bytesio_usage:
            raise AssertionError(
                "data_loader.py reads file bytes but BytesIO is not imported. "
                "If you're adding file.read() for size checking, also add: "
                "from io import BytesIO"
            )

    def _read(self) -> str:
        with open(self.DATA_LOADER_PATH) as f:
            return f.read()
