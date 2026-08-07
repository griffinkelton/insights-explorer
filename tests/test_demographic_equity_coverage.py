from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "validate_demographic_equity_coverage.py"
SPEC = importlib.util.spec_from_file_location("coverage_validator", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


EXPECTED_GATE_IDS = {
    "0.1",
    "0.2",
    "0.3",
    "0.4",
    "0.5",
    "0.6",
    "1.1",
    "1.2",
    "1.3",
    "1.4",
    "1.5",
    "1.6",
    "1.7",
    "1.8",
    "1.9",
    "1.10",
    "2.1",
    "2.2",
    "2.3",
    "2.3-RACE",
    "2.4",
    "2.5",
    "2.6",
    "2.7",
    "2.8",
    "3.1",
    "3.2",
    "3.3",
    "3.4",
    "3.5",
    "T.1",
    "T.2",
    "T.3",
    "T.4",
    "T.5",
    "T.6",
    "T.7",
    "T.8",
}


def load_data() -> dict:
    return json.loads(
        (ROOT / "braintree-evidence" / "analysis" / "DEMOGRAPHIC_EQUITY_COVERAGE.json").read_text()
    )


def test_all_questions_and_gates_are_valid() -> None:
    data = load_data()
    MODULE.validate_coverage(data)

    assert [row["id"] for row in data["questions"]] == list(range(1, 26))
    assert {row["id"] for row in data["gates"]} == EXPECTED_GATE_IDS
    assert {row["id"] for row in data["gates"] if row["id"].startswith("1.")} == {
        f"1.{i}" for i in range(1, 10)
    } | {"1.10"}


def test_every_question_has_evidence_and_an_explicit_boundary() -> None:
    data = load_data()
    for question in data["questions"]:
        assert question["evidence"], question["id"]
        assert question["limitations"], question["id"]
        assert question["unlock"], question["id"]
        if question["status"] in {"partial_now", "blocked_external_input"}:
            assert question["unlock"] != "None", question["id"]


def test_checked_in_markdown_matches_canonical_json() -> None:
    data = load_data()
    MODULE.assert_rendered_markdown_matches(data)


def test_rendered_matrix_has_all_25_questions() -> None:
    data = load_data()
    rendered = MODULE.render_markdown(data)
    for question_id in range(1, 26):
        assert f"| {question_id} |" in rendered
    assert "## Implementation gates" in rendered
    assert "## Decision boundary" in rendered
