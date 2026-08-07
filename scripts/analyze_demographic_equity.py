"""Reproducible descriptive calculations for the BrainGuide equity snapshot.

This script intentionally does not estimate population under-representation or
funnel disparities. The Evidence PDFs provide selected aggregate rows, not a
linked eligible-visitor/start/completer cohort. It calculates only claims whose
numerators and denominators are explicit in the captured snapshot.

Usage:
    python scripts/analyze_demographic_equity.py
    python scripts/analyze_demographic_equity.py --json-out braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_SNAPSHOT.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INPUTS_PATH = ROOT / "braintree-evidence" / "analysis" / "DEMOGRAPHIC_EQUITY_INPUTS.json"
MIN_RELEASE_CELL = 10
RATE_STABILITY_MIN_DENOMINATOR = 50


def load_inputs() -> dict[str, Any]:
    return json.loads(INPUTS_PATH.read_text(encoding="utf-8"))


def share(part: float, whole: float) -> float:
    if whole <= 0:
        raise ValueError("Denominator must be positive")
    return round(part / whole * 100, 1)


def ratio(part: float, reference: float) -> float:
    if reference <= 0:
        raise ValueError("Reference must be positive")
    return round(part / reference, 2)


def validate_rows(rows: dict[str, int], expected_total: int) -> None:
    actual = sum(rows.values())
    if actual != expected_total:
        raise AssertionError(f"Displayed-row total {actual} != expected {expected_total}")
    if any(value < 0 for value in rows.values()):
        raise AssertionError("Counts cannot be negative")


def safe_cell(value: int) -> int | str:
    """Apply the release floor to a cell before it enters the artifact."""
    return value if value >= MIN_RELEASE_CELL else f"<{MIN_RELEASE_CELL}"


def visit_click_rate(clicks: int | str, visits: int) -> float | str:
    """Return a rate only when numerator and denominator are releasable/stable."""
    if isinstance(clicks, str) or clicks < MIN_RELEASE_CELL:
        return f"suppressed: numerator < {MIN_RELEASE_CELL}"
    if visits < RATE_STABILITY_MIN_DENOMINATOR:
        return f"suppressed: denominator < {RATE_STABILITY_MIN_DENOMINATOR}"
    return share(clicks, visits)


def build_snapshot() -> dict[str, Any]:
    inputs = load_inputs()
    race_rows = inputs["race_rows"]
    gender_rows = inputs["gender_rows"]
    flow_race_rows = inputs["flow_race_rows"]
    flow_kpis = inputs["flow_kpis"]
    locale = inputs["locale_and_resource"]
    race_total = sum(race_rows.values())
    gender_total = sum(gender_rows.values())
    validate_rows(race_rows, 54_626)
    validate_rows(gender_rows, 56_885)

    for flow, rows in flow_race_rows.items():
        named_total = sum(value for key, value in rows.items() if key != "displayed_row_sum")
        if named_total > rows["displayed_row_sum"]:
            raise AssertionError(f"Named {flow} race rows exceed displayed total")

    trials_visits = locale["clinical_trials_visits"]
    trials_clicks = locale["clinical_trials_clicks"]
    provider_visits = locale["find_provider_visits"]
    provider_clicks = locale["find_provider_clicks"]

    return {
        "artifact": {
            "name": "BrainGuide demographic equity snapshot",
            "version": inputs["artifact"]["version"],
            "status": "provisional_descriptive",
            "source": "braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_INPUTS.json",
            "source_snapshot": inputs["artifact"]["source_snapshot"],
            "not_population_estimate": True,
            "release_floor_n": MIN_RELEASE_CELL,
            "rate_stability_min_denominator": RATE_STABILITY_MIN_DENOMINATOR,
        },
        "displayed_race_rows": {
            "rows": race_rows,
            "denominator": race_total,
            "shares_percent": {key: share(value, race_total) for key, value in race_rows.items()},
            "white_to_black_ratio": ratio(
                race_rows["White/Caucasian"], race_rows["Black/African American"]
            ),
            "white_to_hispanic_ratio": ratio(
                race_rows["White/Caucasian"], race_rows["Hispanic/Latino"]
            ),
            "provenance": inputs["provenance"]["race_rows"] + "; displayed rows only",
        },
        "displayed_gender_rows": {
            "rows": gender_rows,
            "denominator": gender_total,
            "shares_percent": {
                key: share(value, gender_total) for key, value in gender_rows.items()
            },
            "provenance": inputs["provenance"]["gender_rows"] + "; displayed rows only",
        },
        "flow_race_rows": {
            "flows": flow_race_rows,
            "flow_kpis": flow_kpis,
            "provenance": inputs["provenance"]["flow_race_rows"],
            "interpretation": "Displayed-row composition only; row sums do not equal all flow KPIs.",
        },
        "language_and_resource_rates": {
            "top_content_pageviews": {
                "counts": locale["top_content_pageviews"],
                "spanish_share_percent": share(28_531, 487_949 + 28_531),
            },
            "clinical_trials": {
                "english_visit_click_rate_percent": visit_click_rate(
                    trials_clicks["English"], trials_visits["English"]
                ),
                "spanish_visit_click_rate_percent": visit_click_rate(
                    trials_clicks["Spanish"], trials_visits["Spanish"]
                ),
                "counts": {"visits": trials_visits, "clicks": trials_clicks},
            },
            "find_provider": {
                "english_visit_click_rate_percent": visit_click_rate(
                    provider_clicks["English"], provider_visits["English"]
                ),
                "spanish_visit_click_rate_percent": visit_click_rate(
                    provider_clicks["Spanish"], provider_visits["Spanish"]
                ),
                "counts": {
                    "visits": provider_visits,
                    "clicks": {
                        "English": provider_clicks["English"],
                        "Spanish": (
                            provider_clicks["Spanish"]
                            if isinstance(provider_clicks["Spanish"], str)
                            else safe_cell(provider_clicks["Spanish"])
                        ),
                    },
                },
            },
            "provenance": "; ".join(
                [
                    inputs["provenance"]["top_content"],
                    inputs["provenance"]["clinical_trials"],
                    inputs["provenance"]["find_provider"],
                ]
            ),
            "interpretation": "Visit-based descriptive rates; rates require denominator >= 50; released cells require n >= 10.",
        },
        "device_exit_rates": {
            "rates_percent": inputs["device_exit_rates"],
            "provenance": inputs["provenance"]["device_exit_rates"],
            "interpretation": "Page-sequence exit measure, not bounce rate and not linked to self-reported demographics.",
        },
        "blocked_claims": [
            {
                "claim": "Population-level Black or Hispanic under-representation",
                "reason": "No defined benchmark and no all-eligible visitor denominator",
            },
            {
                "claim": "Completion or drop-off disparity by race/ethnicity",
                "reason": "No event-level demographic linkage at starts and steps",
            },
            {
                "claim": "Cause of the White-heavy respondent profile",
                "reason": "Acquisition, device, language, trust, and nonresponse mechanisms are not identified",
            },
            {
                "claim": "Effectiveness of UX, copy, or outreach interventions",
                "reason": "No intervention comparison or prespecified evaluation",
            },
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    snapshot = build_snapshot()
    rendered = json.dumps(snapshot, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
