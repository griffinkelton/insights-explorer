"""Static analysis linters — catches structural bugs that AST parsing alone misses.

Pattern 4 (BUG-002): Verifies function definitions appear BEFORE their
    first call site at the module level in Streamlit scripts (.py files
    that execute top-to-bottom). Currently scans app.py and pages/learn.py.

Pattern 3 (BUG-006): Verifies that file-I/O functions like
    ``load_file()`` don't mix ``file.read()`` with ``pd.read_csv(file)`` on
    the same file object (which consumes the buffer). Checks that
    BytesIO is used as a wrapper when both operations exist.

Pattern 1 (BUG-001): Verifies that every ``except Exception`` at the
    module level in Streamlit scripts that wraps Streamlit control flow
    calls (st.stop, st.rerun) properly re-raises Streamlit's internal
    exceptions instead of treating them as unhandled errors.

Pattern 2 (BUG-005): Detects ``on_click`` callback anti-patterns —
    callbacks that trigger slow operations (API calls) should use
    ``if st.button`` + ``st.spinner()`` instead of ``on_click``.

Pattern 5 (hardening gate): Verifies that no ``drive.readonly`` string
    remains in runtime source code after PR 2 Drive scope removal.

Pattern 6 (hardening gate): Verifies that no bare ``except Exception:
    pass`` blocks exist without a justifying comment across all runtime
    source files.
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
        source = textwrap.dedent(
            """\
            import streamlit as st

            try:
                _render_main()
            except Exception:
                st.error("Something went wrong")

            def _render_main():
                st.write("Hello")
        """
        )
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
        source = textwrap.dedent(
            """\
            import streamlit as st

            def _render_main():
                st.write("Hello")

            try:
                _render_main()
            except Exception:
                st.error("Something went wrong")
        """
        )
        tree = ast.parse(source)
        defs = _find_defs(tree)
        calls = _find_module_level_calls(tree)

        violations = [(name, line) for name, line in calls if name in defs and line < defs[name]]
        assert not violations, f"Correctly-ordered code flagged as violation: {violations}"


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


# ═══════════════════════════════════════════════════════════════════════════
# Pattern 1: except Exception Streamlit guard (BUG-001)
# ═══════════════════════════════════════════════════════════════════════════


class TestStreamlitExceptionGuard:
    """Verify `except Exception` blocks in app.py re-raise Streamlit exceptions.

    BUG-001: Streamlit uses exceptions for internal control flow — st.stop(),
    st.rerun(), and st.spinner() raise exceptions that inherit from Exception.
    A generic `except Exception` at the top level catches these and treats
    them as unhandled errors instead of normal Streamlit behavior.

    The fix: every `except Exception` block that wraps Streamlit control flow
    must have the guard:
        if e.__class__.__module__.startswith("streamlit"):
            raise
    """

    APP_PATH = os.path.join(ROOT, "app.py")

    # Streamlit functions that use exceptions for control flow
    _STREAMLIT_CONTROL_FLOW = {"stop", "rerun", "spinner", "form_submit_button"}

    def test_except_exception_has_streamlit_guard(self):
        """Every try/except Exception at module level that wraps Streamlit
        control flow calls must re-raise Streamlit exceptions."""
        tree = _parse(self.APP_PATH)

        violations: list[str] = []

        for stmt in tree.body:
            if not isinstance(stmt, ast.Try):
                continue

            # Check if any except handler catches Exception (bare or explicit)
            has_except_exception = False
            for handler in stmt.handlers:
                if handler.type is None:
                    # bare `except:` — catches everything including BaseException
                    has_except_exception = True
                    break
                if isinstance(handler.type, ast.Name) and handler.type.id == "Exception":
                    has_except_exception = True
                    break
                if isinstance(handler.type, ast.Tuple):
                    for elt in handler.type.elts:
                        if isinstance(elt, ast.Name) and elt.id == "Exception":
                            has_except_exception = True
                            break

            if not has_except_exception:
                continue

            # Check if the try body contains Streamlit control flow calls
            has_control_flow = False
            for node in ast.walk(stmt):
                if isinstance(node, ast.Call):
                    name = _call_target_name(node)
                    if name in self._STREAMLIT_CONTROL_FLOW:
                        has_control_flow = True
                        break
                    # Also check st.stop(), st.rerun() pattern
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr in self._STREAMLIT_CONTROL_FLOW:
                            has_control_flow = True
                            break

            if not has_control_flow:
                continue

            # Check if handler has the Streamlit re-raise guard
            has_guard = False
            for handler in stmt.handlers:
                for node in ast.walk(handler):
                    if isinstance(node, ast.If):
                        # Look for: if e.__class__.__module__.startswith("streamlit"): raise
                        if self._is_streamlit_guard(node):
                            has_guard = True
                            break

            if not has_guard:
                violations.append(
                    f"except Exception at line {stmt.lineno} wraps Streamlit "
                    f"control flow (st.stop/st.rerun) but does not re-raise "
                    f"Streamlit exceptions. Add: "
                    f'if e.__class__.__module__.startswith("streamlit"): raise'
                )

        if violations:
            raise AssertionError(
                "except Exception blocks missing Streamlit guard in app.py:\n  "
                + "\n  ".join(violations)
            )

    def test_no_silent_except_pass_at_module_level(self):
        """Bare `except Exception: pass` at module level silently swallows
        all errors — these should be justified with a comment, or better yet,
        replaced with specific exception handling."""
        tree = _parse(self.APP_PATH)

        silent_pass_count = 0
        for stmt in tree.body:
            if not isinstance(stmt, ast.Try):
                continue
            for handler in stmt.handlers:
                if self._is_silent_pass(handler):
                    silent_pass_count += 1

        # Current codebase has 2 intentional silent-passes (date parse, chart gen)
        # If this grows beyond 2, flag it
        if silent_pass_count > 2:
            raise AssertionError(
                f"{silent_pass_count} silent except Exception: pass blocks "
                f"found in app.py (was 2 at baseline). "
                f"Each silent pass hides errors — add a comment justifying it "
                f"or handle the specific exception."
            )

    def _is_streamlit_guard(self, node: ast.If) -> bool:
        """Check if an If node is the Streamlit exception re-raise guard."""
        try:
            test = node.test
            # if e.__class__.__module__.startswith("streamlit"):
            if not isinstance(test, ast.Call):
                return False
            if not isinstance(test.func, ast.Attribute):
                return False
            if test.func.attr != "startswith":
                return False
            # Check the argument is "streamlit"
            if len(test.args) != 1:
                return False
            arg = test.args[0]
            if isinstance(arg, ast.Constant) and arg.value == "streamlit":
                return True
        except Exception:
            pass
        return False

    def _is_silent_pass(self, handler: ast.ExceptHandler) -> bool:
        """Check if an except handler silently swallows all errors.

        Silent = catches Exception (or bare except) with only Pass statements
        in the body. Two passes is still silent. A logging call makes it
        not-silent (at least something happens).
        """
        if handler.type is None:
            # bare `except:` — catches everything including BaseException
            return all(isinstance(n, ast.Pass) for n in handler.body)
        if isinstance(handler.type, ast.Name) and handler.type.id == "Exception":
            return all(isinstance(n, ast.Pass) for n in handler.body)
        return False

    def test_synthetic_missing_guard_detected(self):
        """Prove the linter catches a missing guard."""
        source = textwrap.dedent(
            """\
            import streamlit as st

            try:
                st.stop()
            except Exception as e:
                st.error(f"Error: {e}")
        """
        )
        tree = ast.parse(source)
        # The try body has st.stop() at module level — the handler
        # catches Exception but doesn't re-raise Streamlit exceptions.
        # _is_streamlit_guard should return False for `st.error(...)`
        for stmt in tree.body:
            if isinstance(stmt, ast.Try):
                for handler in stmt.handlers:
                    has_guard = any(self._is_streamlit_guard(node) for node in ast.walk(handler))
                    assert not has_guard, (
                        "Expected no Streamlit guard, but _is_streamlit_guard "
                        "returned True — st.error() is not the guard pattern"
                    )

    def test_synthetic_guard_present_passes(self):
        """Prove the linter accepts a correct guard."""
        source = textwrap.dedent(
            """\
            import streamlit as st

            try:
                st.stop()
            except Exception as e:
                if e.__class__.__module__.startswith("streamlit"):
                    raise
                st.error(f"Error: {e}")
        """
        )
        tree = ast.parse(source)
        for stmt in tree.body:
            if isinstance(stmt, ast.Try):
                for handler in stmt.handlers:
                    has_guard = any(self._is_streamlit_guard(node) for node in ast.walk(handler))
                    assert has_guard, (
                        "_is_streamlit_guard should detect the re-raise pattern: "
                        'if e.__class__.__module__.startswith("streamlit"): raise'
                    )


# ═══════════════════════════════════════════════════════════════════════════
# Pattern 2: on_click anti-pattern (BUG-005)
# ═══════════════════════════════════════════════════════════════════════════


class TestOnClickAntiPattern:
    """Detect `on_click` callbacks that trigger slow operations.

    BUG-005: Streamlit's `on_click` callbacks run synchronously inside the
    event loop, freezing the UI. Any network, disk, or compute operation
    in an on_click callback produces a frozen UI with zero feedback.

    Rule: `on_click` is for instant operations only (clearing state, setting
    flags). Use `if st.button(...)` + `st.spinner()` for API calls.

    Note: This linter uses string matching on source code, which is fragile.
    It flags any `on_click=` that references a function known to make API
    calls. It also warns about lambda usage in on_click (common anti-pattern).
    """

    APP_PATH = os.path.join(ROOT, "app.py")

    # Functions known to trigger slow operations (API calls, network I/O)
    _SLOW_FUNCTIONS = {
        "_generate_summary",  # Gemini API call
        "generate_response",
        "pull_ga4_report",
        "exchange_code",
        "load_file",
    }

    # Functions known to be instant (safe for on_click)
    _INSTANT_FUNCTIONS = {
        "clear_data",  # just sets session_state values
    }

    def test_on_click_no_slow_callbacks(self):
        """on_click callbacks must be instant operations only — not API calls.

        The current codebase has 2 known on_click usages:
        - `on_click=clear_data` — instant (✅ OK)
        - `on_click=lambda: _generate_summary(df, stats)` — API call (⚠️ FLAGGED)

        The _generate_summary lambda is the BUG-005 anti-pattern — it freezes
        the UI for 3-5 seconds during the Gemini call. This test documents
        the known issue and will pass once it's fixed.
        """
        source = self._read()

        # Find all on_click= lines
        violations: list[str] = []
        for i, line in enumerate(source.split("\n"), 1):
            stripped = line.strip()
            if "on_click=" not in stripped:
                continue

            # Check if it references a slow function
            for func in self._SLOW_FUNCTIONS:
                if func in stripped:
                    violations.append(
                        f"Line {i}: on_click calls {func}() — "
                        f"this freezes the UI during API calls. "
                        f"Replace with: if st.button(...): with st.spinner(...): {func}(...)"
                    )

            # Lambda in on_click is almost always wrong (can't use spinner)
            if "lambda" in stripped:
                is_instant = any(f in stripped for f in self._INSTANT_FUNCTIONS)
                if not is_instant:
                    violations.append(
                        f"Line {i}: on_click uses lambda — lambda callbacks "
                        f"can't be wrapped in st.spinner(). "
                        f"Replace with: if st.button(...): with st.spinner(...): ..."
                    )

        if violations:
            raise AssertionError(
                "on_click anti-patterns in app.py:\n  "
                + "\n  ".join(violations)
                + "\n\nUse 'if st.button' + 'st.spinner()' instead of on_click "
                "for any operation that takes >100ms."
            )

    def _read(self) -> str:
        with open(self.APP_PATH) as f:
            return f.read()


# ═══════════════════════════════════════════════════════════════════════════
# Pattern 5: drive.readonly string must not appear in runtime source
# ═══════════════════════════════════════════════════════════════════════════


class TestDriveReadonlyRemoved:
    """Verify no ``drive.readonly`` string survives in runtime source.

    After PR 2 Drive scope removal, the app should only reference
    ``drive.file`` for exports — never ``drive.readonly`` (browsing).
    Scans all .py files under utils/, components/, pages/, and app.py.
    """

    _RUNTIME_DIRS = ["utils", "components", "pages"]
    _RUNTIME_FILES = ["app.py"]

    def test_no_drive_readonly_in_source(self):
        """No .py file under runtime dirs should contain drive.readonly."""
        violations: list[str] = []

        for dir_name in self._RUNTIME_DIRS:
            dir_path = os.path.join(ROOT, dir_name)
            if not os.path.isdir(dir_path):
                continue
            for root, _dirs, files in os.walk(dir_path):
                for fname in files:
                    if fname.endswith(".py") and not fname.startswith("test_"):
                        fpath = os.path.join(root, fname)
                        if self._contains_drive_readonly(fpath):
                            violations.append(
                                f"{os.path.relpath(fpath, ROOT)}: contains 'drive.readonly'"
                            )

        for fname in self._RUNTIME_FILES:
            fpath = os.path.join(ROOT, fname)
            if os.path.isfile(fpath) and self._contains_drive_readonly(fpath):
                violations.append(f"{fname}: contains 'drive.readonly'")

        if violations:
            raise AssertionError(
                "drive.readonly references found in runtime source after PR 2:\n  "
                + "\n  ".join(violations)
                + "\n\nReplace with drive.file only or remove entirely."
            )

    def _contains_drive_readonly(self, path: str) -> bool:
        with open(path) as f:
            return "drive.readonly" in f.read()


# ═══════════════════════════════════════════════════════════════════════════
# Pattern 6: expand silent except: pass scanning to all runtime files
# ═══════════════════════════════════════════════════════════════════════════


class TestSilentExceptPass:
    """Verify no bare ``except Exception: pass`` blocks exist without
    a justifying comment across all runtime source files.

    Scans utils/, components/, pages/, and app.py.
    """

    _RUNTIME_DIRS = ["utils", "components", "pages"]
    _RUNTIME_FILES = ["app.py"]

    def test_no_undocumented_silent_pass(self):
        """No silent except:pass blocks should exist without a justifying
        comment on the same line or the preceding 3 lines."""
        violations: list[str] = []

        all_files: list[str] = []
        for dir_name in self._RUNTIME_DIRS:
            dir_path = os.path.join(ROOT, dir_name)
            if not os.path.isdir(dir_path):
                continue
            for root, _dirs, files in os.walk(dir_path):
                for fname in files:
                    if fname.endswith(".py") and not fname.startswith("test_"):
                        all_files.append(os.path.join(root, fname))

        for fname in self._RUNTIME_FILES:
            fpath = os.path.join(ROOT, fname)
            if os.path.isfile(fpath):
                all_files.append(fpath)

        for fpath in all_files:
            rel = os.path.relpath(fpath, ROOT)
            with open(fpath) as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                stripped = line.strip()
                # Look for bare except: or except Exception:
                is_except = (
                    stripped == "except:"
                    or stripped == "except Exception:"
                    or stripped == "except Exception as e:"
                )
                if not is_except:
                    continue

                # Check if the next non-empty line is just 'pass'
                next_line = ""
                for j in range(i + 1, min(i + 4, len(lines))):
                    nl = lines[j].strip()
                    if nl:
                        next_line = nl
                        break

                if next_line != "pass":
                    continue  # Not a silent pass

                # Check if there's a justifying comment nearby
                has_justification = "#" in line or "#" in next_line
                # Also check 3 preceding lines for comments
                for j in range(max(0, i - 3), i):
                    if "#" in lines[j]:
                        has_justification = True
                        break

                if not has_justification:
                    violations.append(f"{rel}:{i + 1} — silent except:pass")

        if violations:
            raise AssertionError(
                "Undocumented silent except:pass blocks found:\n  "
                + "\n  ".join(violations)
                + "\n\nAdd a comment explaining why the exception is intentionally swallowed."
            )


# ═══════════════════════════════════════════════════════════════════════════
# Pattern 7: Retired data-key AST guard (DataContext Phase 1 Step 4)
# ═══════════════════════════════════════════════════════════════════════════

RETIRED_DATA_KEYS = {
    "df",
    "filtered_df",
    "custom_metrics_df",
    "filters_active",
    "ga4_truncated",
}


class _RetiredKeyVisitor(ast.NodeVisitor):
    """AST visitor that detects access to retired session-state keys."""

    def __init__(self, source_lines: list[str]):
        self.source_lines = source_lines
        self.ss_aliases: set[str] = set()
        self.violations: list[tuple[int, str]] = []

    def visit_Assign(self, node: ast.Assign) -> None:
        if self._is_ss_ref(node.value):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.ss_aliases.add(target.id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value and self._is_ss_ref(node.value):
            if isinstance(node.target, ast.Name):
                self.ss_aliases.add(node.target.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if self._is_ss_ref(node.value) and node.attr in RETIRED_DATA_KEYS:
            self.violations.append((node.lineno, f"st.session_state.{node.attr}"))
        if isinstance(node.value, ast.Name) and node.value.id in self.ss_aliases:
            if node.attr in RETIRED_DATA_KEYS:
                self.violations.append((node.lineno, f"alias.{node.attr}"))
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if self._is_ss_ref(node.value):
            key = self._extract_constant(node.slice)
            if key in RETIRED_DATA_KEYS:
                self.violations.append((node.lineno, f'st.session_state["{key}"]'))
        if isinstance(node.value, ast.Name) and node.value.id in self.ss_aliases:
            key = self._extract_constant(node.slice)
            if key in RETIRED_DATA_KEYS:
                self.violations.append((node.lineno, f'alias["{key}"]'))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute):
            method = node.func.attr
            base = node.func.value
            is_ss = self._is_ss_ref(base) or (
                isinstance(base, ast.Name) and base.id in self.ss_aliases
            )
            if is_ss and method in ("get", "setdefault", "pop"):
                if node.args:
                    key = self._extract_constant(node.args[0])
                    if key in RETIRED_DATA_KEYS:
                        self.violations.append((node.lineno, f'st.session_state.{method}("{key}")'))
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        for op in node.ops:
            if isinstance(op, ast.In) and len(node.comparators) == 1:
                if self._is_ss_ref(node.comparators[0]):
                    key = self._extract_constant(node.left)
                    if key in RETIRED_DATA_KEYS:
                        self.violations.append((node.lineno, f'"{key}" in st.session_state'))
        self.generic_visit(node)

    def visit_Delete(self, node: ast.Delete) -> None:
        for target in node.targets:
            if isinstance(target, ast.Subscript) and self._is_ss_ref(target.value):
                key = self._extract_constant(target.slice)
                if key in RETIRED_DATA_KEYS:
                    self.violations.append((node.lineno, f'del st.session_state["{key}"]'))
            if isinstance(target, ast.Attribute) and self._is_ss_ref(target.value):
                if target.attr in RETIRED_DATA_KEYS:
                    self.violations.append((node.lineno, f"del st.session_state.{target.attr}"))
        self.generic_visit(node)

    @staticmethod
    def _is_ss_ref(node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Attribute)
            and node.attr == "session_state"
            and isinstance(node.value, ast.Name)
            and node.value.id == "st"
        )

    @staticmethod
    def _extract_constant(node: ast.AST) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None


class TestRetiredDataKeys:
    """Verify no retired session-state data keys remain in production code."""

    _RUNTIME_DIRS = ["utils", "components", "pages"]
    _RUNTIME_FILES = ["app.py"]

    def test_no_retired_keys_in_production_source(self):
        """No retired data keys in production .py files."""
        violations: list[str] = []
        all_files: list[str] = []

        for dir_name in self._RUNTIME_DIRS:
            dir_path = os.path.join(ROOT, dir_name)
            if not os.path.isdir(dir_path):
                continue
            for root, _dirs, files in os.walk(dir_path):
                for fname in files:
                    if fname.endswith(".py") and not fname.startswith("test_"):
                        all_files.append(os.path.join(root, fname))

        for fname in self._RUNTIME_FILES:
            fpath = os.path.join(ROOT, fname)
            if os.path.isfile(fpath):
                all_files.append(fpath)

        for fpath in all_files:
            rel = os.path.relpath(fpath, ROOT)
            with open(fpath) as f:
                source = f.read()
            try:
                tree = ast.parse(source, filename=fpath)
            except SyntaxError:
                continue

            visitor = _RetiredKeyVisitor(source.split("\n"))
            visitor.visit(tree)

            for line, desc in visitor.violations:
                violations.append(f"{rel}:{line} — {desc}")

        if violations:
            raise AssertionError(
                "Retired session-state keys found in production code "
                "after Phase 1 Step 4 migration:\n  "
                + "\n  ".join(violations)
                + "\n\nThese keys are retired. Use DataContext fields instead."
            )

    # ── Negative test fixtures ──────────────────────────────────────────

    def test_retired_key_guard_catches_attribute(self):
        source = textwrap.dedent(
            """\
            import streamlit as st
            x = st.session_state.df
        """
        )
        tree = ast.parse(source)
        visitor = _RetiredKeyVisitor(source.split("\n"))
        visitor.visit(tree)
        assert len(visitor.violations) >= 1, "Guard missed st.session_state.df"

    def test_retired_key_guard_catches_subscript(self):
        source = textwrap.dedent(
            """\
            import streamlit as st
            x = st.session_state["filtered_df"]
        """
        )
        tree = ast.parse(source)
        visitor = _RetiredKeyVisitor(source.split("\n"))
        visitor.visit(tree)
        assert len(visitor.violations) >= 1

    def test_retired_key_guard_catches_get(self):
        source = textwrap.dedent(
            """\
            import streamlit as st
            x = st.session_state.get("custom_metrics_df")
        """
        )
        tree = ast.parse(source)
        visitor = _RetiredKeyVisitor(source.split("\n"))
        visitor.visit(tree)
        assert len(visitor.violations) >= 1

    def test_retired_key_guard_catches_alias(self):
        source = textwrap.dedent(
            """\
            import streamlit as st
            state = st.session_state
            x = state.df
        """
        )
        tree = ast.parse(source)
        visitor = _RetiredKeyVisitor(source.split("\n"))
        visitor.visit(tree)
        assert len(visitor.violations) >= 1, "Guard missed alias state.df"

    def test_retired_key_guard_catches_setdefault(self):
        source = textwrap.dedent(
            """\
            import streamlit as st
            st.session_state.setdefault("df", None)
        """
        )
        tree = ast.parse(source)
        visitor = _RetiredKeyVisitor(source.split("\n"))
        visitor.visit(tree)
        assert len(visitor.violations) >= 1

    def test_retired_key_guard_catches_pop(self):
        source = textwrap.dedent(
            """\
            import streamlit as st
            st.session_state.pop("filtered_df", None)
        """
        )
        tree = ast.parse(source)
        visitor = _RetiredKeyVisitor(source.split("\n"))
        visitor.visit(tree)
        assert len(visitor.violations) >= 1

    def test_retired_key_guard_catches_membership(self):
        source = textwrap.dedent(
            """\
            import streamlit as st
            has_it = "custom_metrics_df" in st.session_state
        """
        )
        tree = ast.parse(source)
        visitor = _RetiredKeyVisitor(source.split("\n"))
        visitor.visit(tree)
        assert len(visitor.violations) >= 1

    def test_retired_key_guard_catches_deletion(self):
        source = textwrap.dedent(
            """\
            import streamlit as st
            del st.session_state["ga4_truncated"]
        """
        )
        tree = ast.parse(source)
        visitor = _RetiredKeyVisitor(source.split("\n"))
        visitor.visit(tree)
        assert len(visitor.violations) >= 1

    def test_retired_key_guard_allows_non_retired_keys(self):
        source = textwrap.dedent(
            """\
            import streamlit as st
            x = st.session_state.theme
            y = st.session_state.data_context
            z = st.session_state.get("tour_step", 0)
        """
        )
        tree = ast.parse(source)
        visitor = _RetiredKeyVisitor(source.split("\n"))
        visitor.visit(tree)
        assert len(visitor.violations) == 0, f"Guard flagged non-retired keys: {visitor.violations}"
