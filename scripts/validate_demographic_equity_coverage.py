"""Validate and render the BrainGuide equity coverage matrix.

The coverage matrix is intentionally separate from the descriptive snapshot:
it records whether each client question is supported now, partial, or blocked,
and exactly what unlocks a blocked question. This prevents a plan from being
mistaken for evidence.

Usage:
    python scripts/validate_demographic_equity_coverage.py
    python scripts/validate_demographic_equity_coverage.py --markdown-out braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_COVERAGE.md
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COVERAGE_PATH = ROOT / "braintree-evidence" / "analysis" / "DEMOGRAPHIC_EQUITY_COVERAGE.json"
RENDERED_MARKDOWN_PATH = ROOT / "braintree-evidence" / "analysis" / "DEMOGRAPHIC_EQUITY_COVERAGE.md"
CHECKLIST_PATH = ROOT / "BRAINTREE_CHECKLIST.md"
REQUIRED_QUESTION_FIELDS = {
    "id",
    "question",
    "gate",
    "status",
    "current_answer",
    "evidence",
    "limitations",
    "unlock",
}
VALID_STATUSES = {
    "supported_now",
    "partial_now",
    "blocked_external_input",
    "not_applicable_to_snapshot",
}
VALID_GATE_STATUS_PREFIXES = (
    "blocked_external_input",
    "design_only",
    "implemented_",
    "method_defined_",
    "not_implemented_",
    "partial_",
    "partially_",
    "protocol_defined",
    "snapshot_",
    "supported_",
    "source_",
    "snapshot ",
)


def load_coverage() -> dict[str, Any]:
    return json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))


def _normalize_question(text: str) -> str:
    """Normalize harmless source wording differences before comparison."""
    normalized = text.strip().lower()
    normalized = normalized.replace("the intended", "intended")
    normalized = normalized.replace("for themselves", "")
    normalized = normalized.replace("content/interaction", "content or interaction")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def checklist_questions() -> dict[int, str]:
    questions: dict[int, str] = {}
    pattern = re.compile(r"^\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*[^|]+\s*\|\s*- \[[ x]\]")
    for line in CHECKLIST_PATH.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match and 1 <= int(match.group(1)) <= 25:
            questions[int(match.group(1))] = match.group(2)
    if set(questions) != set(range(1, 26)):
        raise AssertionError(f"Could not parse all 25 checklist questions: {sorted(questions)}")
    return questions


def validate_coverage(data: dict[str, Any]) -> None:
    questions = data.get("questions")
    if not isinstance(questions, list) or len(questions) != 25:
        raise AssertionError("Coverage matrix must contain exactly 25 questions")

    ids = [question.get("id") for question in questions]
    if ids != list(range(1, 26)):
        raise AssertionError(f"Question IDs must be exactly 1..25, got {ids}")

    authoritative = checklist_questions()
    for question in questions:
        missing = REQUIRED_QUESTION_FIELDS - question.keys()
        if missing:
            raise AssertionError(f"Question {question.get('id')} missing fields: {sorted(missing)}")
        if _normalize_question(question["question"]) != _normalize_question(
            authoritative[question["id"]]
        ):
            raise AssertionError(
                f"Question {question['id']} does not match BRAINTREE_CHECKLIST.md: "
                f"{question['question']!r} != {authoritative[question['id']]!r}"
            )
        if question["status"] not in VALID_STATUSES:
            raise AssertionError(
                f"Question {question['id']} has invalid status {question['status']}"
            )
        if not question["current_answer"].strip():
            raise AssertionError(f"Question {question['id']} has no current answer")
        if not isinstance(question["evidence"], list) or not question["evidence"]:
            raise AssertionError(f"Question {question['id']} has no evidence references")
        if not question["limitations"]:
            raise AssertionError(f"Question {question['id']} has no limitations")
        if not question["unlock"].strip():
            raise AssertionError(f"Question {question['id']} has no unlock condition")

    gates = data.get("gates")
    if not isinstance(gates, list) or not gates:
        raise AssertionError("Coverage matrix must contain gates")
    gate_ids = {gate.get("id") for gate in gates}
    for gate in gates:
        for field in ("id", "requirement", "status", "evidence"):
            if field not in gate or not gate[field]:
                raise AssertionError(f"Gate {gate.get('id')} missing non-empty {field}")
        if not isinstance(gate["evidence"], list):
            raise TypeError(f"Gate {gate['id']} evidence must be a list")
        if not gate["status"].startswith(VALID_GATE_STATUS_PREFIXES):
            raise AssertionError(f"Gate {gate['id']} has unrecognized status: {gate['status']}")
    required_gates = {
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
    missing_gates = required_gates - gate_ids
    if missing_gates:
        raise AssertionError(f"Missing required gate rows: {sorted(missing_gates)}")


def render_markdown(data: dict[str, Any]) -> str:
    artifact = data["artifact"]
    questions = data["questions"]
    gates = data["gates"]
    lines = [
        "# BrainGuide Equity Coverage Matrix",
        "",
        f"> **Version:** {artifact['version']}",
        "> **Purpose:** Make every client question and implementation gate auditable: what the current evidence answers, what it only partially answers, and what remains blocked.",
        "> **Important:** `blocked_external_input` means the method is defined but the required external data, owner decision, permission, or intervention result is not present in this repository snapshot.",
        "",
        "## Status legend",
        "",
        "| Status | Meaning |",
        "|---|---|",
    ]
    for status, meaning in artifact["status_vocabulary"].items():
        lines.append(f"| `{status}` | {meaning} |")
    lines += [
        "",
        "## Client questions",
        "",
        "| # | Gate | Status | Question | Current answer / coverage | What remains to unlock full support |",
        "|---:|---|---|---|---|---|",
    ]
    for question in questions:
        answer = question["current_answer"].replace("|", "\\|")
        unlock = question["unlock"].replace("|", "\\|")
        label = question["question"].replace("|", "\\|")
        lines.append(
            f"| {question['id']} | {question['gate']} | `{question['status']}` | {label} | {answer} | {unlock} |"
        )
    lines += [
        "",
        "## Implementation gates",
        "",
        "| Gate | Requirement | Status | Evidence / implementation note |",
        "|---|---|---|---|",
    ]
    for gate in gates:
        evidence = "; ".join(gate["evidence"]).replace("|", "\\|")
        lines.append(f"| {gate['id']} | {gate['requirement']} | `{gate['status']}` | {evidence} |")
    lines += [
        "",
        "## Decision boundary",
        "",
        "The current artifacts support a defensible descriptive equity-risk assessment and a complete execution specification. They do not manufacture population representation ratios, demographic funnel rates, causal mechanisms, intervention effects, or awareness impact where the required denominator, linkage, benchmark, or evaluation design is absent.",
        "",
    ]
    return "\n".join(lines)


def assert_rendered_markdown_matches(data: dict[str, Any]) -> None:
    expected = render_markdown(data)
    if not RENDERED_MARKDOWN_PATH.exists():
        raise AssertionError(f"Missing rendered coverage matrix: {RENDERED_MARKDOWN_PATH}")
    actual = RENDERED_MARKDOWN_PATH.read_text(encoding="utf-8")
    if actual != expected:
        raise AssertionError(
            "DEMOGRAPHIC_EQUITY_COVERAGE.md is out of sync with the canonical JSON matrix"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args()
    data = load_coverage()
    validate_coverage(data)
    rendered = render_markdown(data)
    if args.markdown_out:
        args.markdown_out.write_text(rendered, encoding="utf-8")
        assert_rendered_markdown_matches(data)
    else:
        assert_rendered_markdown_matches(data)
        print(rendered)


if __name__ == "__main__":
    main()
