from __future__ import annotations

import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "analyze_demographic_equity.py"
SPEC = importlib.util.spec_from_file_location("demographic_equity", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_snapshot_reproduces_displayed_race_metrics() -> None:
    snapshot = MODULE.build_snapshot()
    race = snapshot["displayed_race_rows"]

    assert race["denominator"] == 54_626
    assert race["shares_percent"]["White/Caucasian"] == 77.9
    assert race["shares_percent"]["Black/African American"] == 4.5
    assert race["shares_percent"]["Hispanic/Latino"] == 4.9
    assert race["white_to_black_ratio"] == 17.49
    assert race["white_to_hispanic_ratio"] == 15.91


def test_snapshot_reproduces_language_rates() -> None:
    rates = MODULE.build_snapshot()["language_and_resource_rates"]

    assert rates["top_content_pageviews"]["spanish_share_percent"] == 5.5
    assert rates["clinical_trials"]["english_visit_click_rate_percent"] == 18.0
    assert rates["clinical_trials"]["spanish_visit_click_rate_percent"] == 5.8
    assert rates["find_provider"]["english_visit_click_rate_percent"] == 7.7
    assert (
        rates["find_provider"]["spanish_visit_click_rate_percent"] == "suppressed: numerator < 10"
    )
    assert rates["find_provider"]["counts"]["clicks"]["Spanish"] == "<10"


def test_snapshot_does_not_promote_blocked_claims() -> None:
    claims = {item["claim"] for item in MODULE.build_snapshot()["blocked_claims"]}

    assert "Population-level Black or Hispanic under-representation" in claims
    assert "Completion or drop-off disparity by race/ethnicity" in claims
    assert "Effectiveness of UX, copy, or outreach interventions" in claims


def test_checked_in_snapshot_matches_calculator() -> None:
    checked_in = json.loads(
        (
            MODULE.ROOT / "braintree-evidence" / "analysis" / "DEMOGRAPHIC_EQUITY_SNAPSHOT.json"
        ).read_text()
    )
    assert checked_in == MODULE.build_snapshot()


def test_flow_rows_are_explicitly_displayed_row_compositions() -> None:
    snapshot = MODULE.build_snapshot()
    flows = snapshot["flow_race_rows"]["flows"]

    assert flows["AD8"]["displayed_row_sum"] == 10_760
    assert flows["MIS"]["displayed_row_sum"] == 94_929
    assert flows["SBC"]["displayed_row_sum"] == 1_679
    assert "Displayed-row composition only" in snapshot["flow_race_rows"]["interpretation"]
