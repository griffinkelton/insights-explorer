// GA4 Measurement Contract (v0.1 draft) — Gate 0A artifact.
// No metric may be consumed by the insights layer or referenced by the model
// until it has a row here with status `validated`.

export type MetricStatus = "validated" | "provisional" | "unavailable";

export interface MetricRow {
  id: string;
  name: string;
  numerator: string;
  denominator: string;
  grain: string;
  source: string;
  eventMapping: string;
  status: MetricStatus;
  blockedBy?: string;
  limitations: string[];
}

export const MEASUREMENT_CONTRACT_VERSION = "v0.1 draft";

export const measurementContract: MetricRow[] = [
  {
    id: "daily_reach",
    name: "Daily reach",
    numerator: "distinct totalUsers per day",
    denominator: "n/a (raw count)",
    grain: "daily, property-wide",
    source: "pull_ga4_report() aggregate report, dimensions [date]",
    eventMapping: "none required (session/user-level GA4 aggregate)",
    status: "provisional",
    limitations: [
      "No bot/crawler filtering yet.",
      "Excludes incomplete current day/week.",
    ],
  },
  {
    id: "page_device_engagement_rate",
    name: "Page/device engagement",
    numerator: "engagementRate (engaged sessions) per pagePath × deviceCategory",
    denominator: "total sessions for that page/device slice",
    grain: "daily, page path × device category",
    source: "pull_ga4_report(), dimensions [date, pagePath, deviceCategory]",
    eventMapping: "none required",
    status: "provisional",
    limitations: [
      "No session identifier.",
      "Asset/malformed URLs not yet filtered.",
      "Small-cell suppression not yet applied.",
    ],
  },
  {
    id: "questionnaire_start_count",
    name: "Questionnaire start",
    numerator: "count of canonical questionnaire_started event",
    denominator: "n/a (raw count), or daily_reach if reported as a rate",
    grain: "daily, event-level",
    source: "requires event-level GA4 query (not in the current aggregate report)",
    eventMapping: "questionnaire_started → property-specific event name (TBD)",
    status: "unavailable",
    blockedBy: "Event-level query design",
    limitations: ["Cannot be computed from pull_ga4_report(); needs a new report contract."],
  },
  {
    id: "questionnaire_completion_rate",
    name: "Questionnaire completion",
    numerator: "questionnaire_finished, same session, within 24h of start (window TBD)",
    denominator: "questionnaire_start_count for the same cohort/window",
    grain: "daily or period, event-level, per-session",
    source: "requires event-level GA4 query with a session/user identifier",
    eventMapping: "questionnaire_finished → property-specific event name (TBD)",
    status: "unavailable",
    blockedBy: "Event-level query design + funnel specification sign-off",
    limitations: [
      "\u201cCompletion\u201d must not be conflated with generic key-event counts until the taxonomy is validated.",
    ],
  },
  {
    id: "post_questionnaire_action_rate",
    name: "Meaningful post-questionnaire action",
    numerator: "approved action-taxonomy event after questionnaire completion",
    denominator: "questionnaire_completion_count for the same cohort/window",
    grain: "daily or period, event-level, per-session/user",
    source: "requires event-level GA4 query + action taxonomy sign-off",
    eventMapping: "TBD — action taxonomy must be defined and approved",
    status: "unavailable",
    blockedBy: "Action taxonomy definition + event-level data",
    limitations: ["Risk of conflating routine clicks with meaningful outcomes."],
  },
];

export function metricById(id: string) {
  return measurementContract.find((m) => m.id === id) ?? null;
}

/** Metrics the insights layer is allowed to compute from today. */
export function computableMetrics() {
  return measurementContract.filter((m) => m.status !== "unavailable");
}

export function contractContext(): string {
  return [
    `GA4 MEASUREMENT CONTRACT (${MEASUREMENT_CONTRACT_VERSION}) — metric governance:`,
    ...measurementContract.map(
      (m) =>
        `  ${m.id} [${m.status}${m.blockedBy ? `: blocked on ${m.blockedBy}` : ""}] — ${m.numerator} / ${m.denominator}; grain ${m.grain}. Limits: ${m.limitations.join(" ")}`,
    ),
    "  RULE: never present an `unavailable` metric as measured. Label `provisional` metrics as unvalidated.",
  ].join("\n");
}