// Trust layer: deterministic metrics + quality/privacy rules -> insight
// candidates with evidence, uncertainty and provenance. The model prioritizes
// and explains these; it never calculates them.

import {
  SMALL_CELL_THRESHOLD,
  byChannel,
  byDevice,
  byLanguage,
  byRaceEthnicity,
  equityTables,
  fmtPct,
  overallCohort,
  pct,
  questionnaireSteps,
  relaunchPrePost,
  type CohortRow,
} from "@/lib/mock-braintree";
import { EVIDENCE_SOURCE, linkageCoverage } from "@/lib/evidence/mock-evidence";
import { metricById } from "@/lib/measurement-contract";

export type Uncertainty = "high-confidence" | "directional" | "descriptive-only";

export interface InsightCandidate {
  id: string;
  title: string;
  category: "reach" | "funnel" | "equity" | "access" | "quality" | "change";
  /** Deterministically computed statement — no model involvement. */
  finding: string;
  evidence: string[];
  uncertainty: Uncertainty;
  caveats: string[];
  provenance: { source: string; metric: string; metricStatus: string; grain: string };
  suppressed: boolean;
  /** 0-100, deterministic priority score used for ordering. */
  priority: number;
}

const pp = (a: number, b: number) => `${((a - b) * 100).toFixed(1)} pp`;

function provenance(metricId: string, source: string, grain: string) {
  const m = metricById(metricId);
  return {
    source,
    metric: metricId,
    metricStatus: m?.status ?? "unregistered",
    grain: m?.grain ?? grain,
  };
}

function gapRows(rows: CohortRow[], rate: (r: CohortRow) => number, base: number) {
  return rows
    .map((r) => ({ row: r, rate: rate(r), gap: rate(r) - base }))
    .sort((a, b) => a.gap - b.gap);
}

export function buildInsightCandidates(): InsightCandidate[] {
  const out: InsightCandidate[] = [];
  const baseStart = pct(overallCohort.qStarts, overallCohort.users);
  const baseFinish = pct(overallCohort.qFinishes, overallCohort.qStarts);

  // 1. Reach — descriptive, computable from the aggregate report today.
  out.push({
    id: "reach",
    title: "Property reach over the 90-day window",
    category: "reach",
    finding: `${overallCohort.users.toLocaleString()} users produced ${overallCohort.qStarts.toLocaleString()} questionnaire starts (${fmtPct(baseStart)} of users) and ${overallCohort.qFinishes.toLocaleString()} finishes (${fmtPct(baseFinish)} of starters).`,
    evidence: [
      `Denominator: ${overallCohort.users.toLocaleString()} users, Jan 1 – Mar 30 2026.`,
      `Post-questionnaire actions: ${overallCohort.actionTakers.toLocaleString()} (${fmtPct(pct(overallCohort.actionTakers, overallCohort.qFinishes))} of completers).`,
    ],
    uncertainty: "directional",
    caveats: [
      "daily_reach is provisional — no bot/crawler filtering.",
      "Start/finish counts come from Evidence aggregates, not a validated GA4 event-level query.",
    ],
    provenance: provenance("daily_reach", "GA4 aggregate report", "daily, property-wide"),
    suppressed: false,
    priority: 40,
  });

  // 2. Equity gaps in start rate, per dimension.
  for (const table of equityTables) {
    if (table.id === "device" || table.id === "channel") continue;
    const ranked = gapRows(table.rows, (r) => pct(r.qStarts, r.users), baseStart);
    const worst = ranked[0];
    if (!worst || worst.gap > -0.02) continue;
    const small = worst.row.qFinishes < SMALL_CELL_THRESHOLD;
    out.push({
      id: `equity-${table.id}`,
      title: `${table.label}: ${worst.row.segment} starts below the property average`,
      category: "equity",
      finding: `${worst.row.segment} start at ${fmtPct(worst.rate)} of ${worst.row.users.toLocaleString()} users — ${pp(worst.rate, baseStart)} versus the ${fmtPct(baseStart)} property average.`,
      evidence: [
        `Numerator ${worst.row.qStarts.toLocaleString()} starts / denominator ${worst.row.users.toLocaleString()} users.`,
        `Completion within this cohort: ${worst.row.qFinishes.toLocaleString()} finishes.`,
      ],
      uncertainty: small ? "descriptive-only" : "directional",
      caveats: [
        "Demographics are self-reported in the questionnaire, not GA4 inferred demographics.",
        `Linkage coverage is ${(linkageCoverage.ga4SessionsMatched * 100).toFixed(0)}% — un-joined completers are excluded.`,
        ...(small ? [`Cell below the ${SMALL_CELL_THRESHOLD}-person reporting minimum — descriptive only.`] : []),
      ],
      provenance: provenance(
        "questionnaire_start_count",
        `${EVIDENCE_SOURCE.label} · questionnaire_agg`,
        "cohort × period",
      ),
      suppressed: small,
      priority: Math.min(95, 55 + Math.round(Math.abs(worst.gap) * 300)),
    });
  }

  // 3. Language access — explicit small-cell suppression case.
  const spanish = byLanguage.find((r) => r.segment === "Spanish");
  if (spanish) {
    const suppressed = spanish.qFinishes < SMALL_CELL_THRESHOLD;
    out.push({
      id: "language-access",
      title: "Spanish-language pathway is measurable but not reportable as a rate",
      category: "access",
      finding: `Spanish sessions: ${spanish.users.toLocaleString()} users, ${spanish.qStarts} starts, ${spanish.qFinishes} finishes. The completion cell (n=${spanish.qFinishes}) sits under the ${SMALL_CELL_THRESHOLD}-person minimum.`,
      evidence: [
        `Spanish is ${fmtPct(pct(spanish.users, overallCohort.users))} of all users.`,
        `English finishes: ${(byLanguage.find((r) => r.segment === "English")?.qFinishes ?? 0).toLocaleString()}.`,
      ],
      uncertainty: "descriptive-only",
      caveats: [
        "Rate reporting is suppressed; counts are shown for operational awareness only.",
        "Difference-attack protection: do not publish this cell alongside a total that allows back-calculation.",
      ],
      provenance: provenance(
        "questionnaire_completion_rate",
        `${EVIDENCE_SOURCE.label} · questionnaire_agg`,
        "cohort × period",
      ),
      suppressed,
      priority: 88,
    });
  }

  // 4. Funnel drop — largest step-to-step loss.
  let worstStep = { from: "", to: "", loss: 0, rate: 0 };
  for (let i = 1; i < questionnaireSteps.length; i++) {
    const prev = questionnaireSteps[i - 1]!;
    const cur = questionnaireSteps[i]!;
    const loss = prev.value - cur.value;
    if (loss > worstStep.loss) {
      worstStep = { from: prev.step, to: cur.step, loss, rate: pct(loss, prev.value) };
    }
  }
  out.push({
    id: "funnel-drop",
    title: `Largest questionnaire drop-off: ${worstStep.from} → ${worstStep.to}`,
    category: "funnel",
    finding: `${worstStep.loss.toLocaleString()} users are lost between ${worstStep.from} and ${worstStep.to} (${fmtPct(worstStep.rate)} of the prior step).`,
    evidence: questionnaireSteps.map((s) => `${s.step}: ${s.value.toLocaleString()}`),
    uncertainty: "directional",
    caveats: [
      "Computed from Evidence step aggregates, not a GA4 event sequence — re-entry and multi-session journeys are not modelled.",
      "Gate 1.7 (session funnel) remains blocked on event-level data.",
    ],
    provenance: provenance(
      "questionnaire_completion_rate",
      `${EVIDENCE_SOURCE.label} · questionnaire_funnel`,
      "step aggregate",
    ),
    suppressed: false,
    priority: 72,
  });

  // 5. Device-mediated completion barrier.
  const mobile = byDevice.find((r) => r.segment === "Mobile");
  const desktop = byDevice.find((r) => r.segment === "Desktop");
  if (mobile && desktop) {
    const m = pct(mobile.qFinishes, mobile.qStarts);
    const d = pct(desktop.qFinishes, desktop.qStarts);
    out.push({
      id: "device-gap",
      title: "Mobile completion trails desktop",
      category: "funnel",
      finding: `Mobile starters finish at ${fmtPct(m)} versus ${fmtPct(d)} on desktop — a gap of ${pp(m, d)} on ${mobile.qStarts.toLocaleString()} mobile starts.`,
      evidence: [
        `Mobile: ${mobile.qFinishes.toLocaleString()} / ${mobile.qStarts.toLocaleString()} starts.`,
        `Desktop: ${desktop.qFinishes.toLocaleString()} / ${desktop.qStarts.toLocaleString()} starts.`,
      ],
      uncertainty: "directional",
      caveats: [
        "page_device_engagement_rate is provisional — asset/malformed URLs are not yet filtered.",
        "Device is a proxy for context, not a cause; age and device are correlated in this dataset.",
      ],
      provenance: provenance("page_device_engagement_rate", "GA4 aggregate report", "page × device"),
      suppressed: false,
      priority: 68,
    });
  }

  // 6. Channel quality — volume vs meaningful action.
  const ranked = byChannel
    .map((c) => ({ c, action: pct(c.actionTakers, c.users) }))
    .sort((a, b) => b.action - a.action);
  const best = ranked[0];
  const worst = ranked[ranked.length - 1];
  if (best && worst) {
    out.push({
      id: "channel-quality",
      title: "Acquisition volume and downstream action diverge",
      category: "quality",
      finding: `${best.c.segment} converts ${fmtPct(best.action)} of users into a post-questionnaire action versus ${fmtPct(worst.action)} for ${worst.c.segment} — ${pp(best.action, worst.action)}.`,
      evidence: byChannel.map(
        (c) => `${c.segment}: ${c.users.toLocaleString()} users → ${c.actionTakers.toLocaleString()} actions.`,
      ),
      uncertainty: "directional",
      caveats: [
        "post_questionnaire_action_rate is `unavailable` in the contract — the action taxonomy is unapproved, so these are proxy counts.",
        "No causal claim: channel mix confounds with campaign targeting.",
      ],
      provenance: provenance(
        "post_questionnaire_action_rate",
        `${EVIDENCE_SOURCE.label} · traffic_attribution`,
        "channel × period",
      ),
      suppressed: false,
      priority: 60,
    });
  }

  // 7. Relaunch change detection.
  const completion = relaunchPrePost.find((r) => r.metric === "Questionnaire completion rate");
  if (completion) {
    out.push({
      id: "relaunch",
      title: "Post-relaunch completion improved property-wide",
      category: "change",
      finding: `Completion moved from ${fmtPct(completion.pre)} to ${fmtPct(completion.post)} (${pp(completion.post, completion.pre)}) across the March 2026 relaunch.`,
      evidence: relaunchPrePost.map(
        (r) =>
          `${r.metric}: ${r.pre < 1 ? fmtPct(r.pre) : r.pre.toLocaleString()} → ${r.post < 1 ? fmtPct(r.post) : r.post.toLocaleString()}`,
      ),
      uncertainty: "directional",
      caveats: [
        "Pre/post comparison without a control period — seasonality and campaign timing are not separated.",
        "Not a statistical test; no confidence interval is computed.",
      ],
      provenance: provenance("questionnaire_completion_rate", `${EVIDENCE_SOURCE.label} · questionnaire_trend`, "period"),
      suppressed: false,
      priority: 52,
    });
  }

  // 8. Race/ethnicity completion equity.
  const raceRanked = gapRows(byRaceEthnicity, (r) => pct(r.qFinishes, r.qStarts), baseFinish);
  const raceWorst = raceRanked[0];
  if (raceWorst) {
    out.push({
      id: "equity-race-completion",
      title: `Completion equity: ${raceWorst.row.segment}`,
      category: "equity",
      finding: `${raceWorst.row.segment} starters finish at ${fmtPct(raceWorst.rate)} versus ${fmtPct(baseFinish)} overall (${pp(raceWorst.rate, baseFinish)}).`,
      evidence: byRaceEthnicity.map(
        (r) => `${r.segment}: ${r.qFinishes.toLocaleString()} / ${r.qStarts.toLocaleString()} starts.`,
      ),
      uncertainty: "directional",
      caveats: [
        "Self-reported demographics with partial response — cohort sizes are not census-representative.",
        `Linkage coverage ${(linkageCoverage.ga4SessionsMatched * 100).toFixed(0)}%.`,
      ],
      provenance: provenance(
        "questionnaire_completion_rate",
        `${EVIDENCE_SOURCE.label} · questionnaire_agg`,
        "cohort × period",
      ),
      suppressed: raceWorst.row.qFinishes < SMALL_CELL_THRESHOLD,
      priority: 80,
    });
  }

  return out.sort((a, b) => b.priority - a.priority);
}

/** Compact serialization handed to the model as the ONLY numeric input. */
export function insightContext(): string {
  const candidates = buildInsightCandidates();
  return [
    "PRECOMPUTED INSIGHT CANDIDATES (deterministic — do not recalculate, reprioritize and explain only):",
    ...candidates.map((c) =>
      [
        `  [${c.id}] (${c.category}, priority ${c.priority}, ${c.uncertainty}${c.suppressed ? ", SUPPRESSED cell" : ""})`,
        `    finding: ${c.finding}`,
        `    evidence: ${c.evidence.join(" | ")}`,
        `    caveats: ${c.caveats.join(" ")}`,
        `    provenance: ${c.provenance.source}, metric ${c.provenance.metric} [${c.provenance.metricStatus}], grain ${c.provenance.grain}`,
      ].join("\n"),
    ),
  ].join("\n");
}