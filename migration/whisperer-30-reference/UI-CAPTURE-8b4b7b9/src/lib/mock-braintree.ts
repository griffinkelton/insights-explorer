// Mock BrainGuide platform data: GA4 behavior joined to de-identified
// questionnaire demographics. Used for equity analysis + AI answers.

export interface CohortRow {
  segment: string;
  users: number;
  qStarts: number;
  qFinishes: number;
  actionTakers: number;
}

const funnel = (users: number, s: number, f: number, a: number): Omit<CohortRow, "segment"> => ({
  users,
  qStarts: s,
  qFinishes: f,
  actionTakers: a,
});

export const overallCohort: CohortRow = {
  segment: "All visitors",
  ...funnel(118304, 21470, 12988, 4416),
};

export const byAge: CohortRow[] = [
  { segment: "18–34", ...funnel(21180, 2890, 1490, 402) },
  { segment: "35–44", ...funnel(24310, 4120, 2480, 812) },
  { segment: "45–54", ...funnel(26740, 5230, 3310, 1194) },
  { segment: "55–64", ...funnel(24980, 5060, 3220, 1206) },
  { segment: "65+", ...funnel(21094, 4170, 2488, 802) },
];

export const byGender: CohortRow[] = [
  { segment: "Women", ...funnel(74420, 14980, 9410, 3216) },
  { segment: "Men", ...funnel(39510, 6010, 3320, 1112) },
  { segment: "Self-described / not stated", ...funnel(4374, 480, 258, 88) },
];

export const byRaceEthnicity: CohortRow[] = [
  { segment: "White (non-Hispanic)", ...funnel(72110, 14210, 9080, 3120) },
  { segment: "Black / African American", ...funnel(18240, 2980, 1462, 401) },
  { segment: "Hispanic / Latino", ...funnel(15980, 2540, 1210, 318) },
  { segment: "Asian / Pacific Islander", ...funnel(7420, 1210, 806, 297) },
  { segment: "Other / multiple / not stated", ...funnel(4554, 530, 430, 280) },
];

export const byLanguage: CohortRow[] = [
  { segment: "English", ...funnel(116890, 21288, 12946, 4402) },
  { segment: "Spanish", ...funnel(1414, 182, 42, 14) },
];

export const byRole: CohortRow[] = [
  { segment: "Person with concerns about self", ...funnel(52310, 11240, 7180, 2610) },
  { segment: "Caregiver / family member", ...funnel(44120, 8010, 4680, 1520) },
  { segment: "Prevention-oriented / general interest", ...funnel(21874, 2220, 1128, 286) },
];

export const byDevice: CohortRow[] = [
  { segment: "Mobile", ...funnel(74940, 12980, 6810, 2180) },
  { segment: "Desktop", ...funnel(36110, 7620, 5560, 2020) },
  { segment: "Tablet", ...funnel(7254, 870, 618, 216) },
];

export const byChannel: CohortRow[] = [
  { segment: "Organic search", ...funnel(51230, 9880, 6210, 2140) },
  { segment: "Paid social", ...funnel(24410, 3120, 1180, 240) },
  { segment: "Referral (partner orgs)", ...funnel(17820, 4610, 3210, 1290) },
  { segment: "Direct", ...funnel(15640, 2810, 1840, 604) },
  { segment: "Email / newsletter", ...funnel(9204, 1050, 548, 142) },
];

export const questionnaireSteps = [
  { step: "Questionnaire start", value: 21470 },
  { step: "Section 1 complete", value: 17930 },
  { step: "Section 2 complete", value: 15120 },
  { step: "Section 3 complete", value: 13640 },
  { step: "Questionnaire finish", value: 12988 },
  { step: "Tailored results viewed", value: 11402 },
  { step: "Resource / provider click", value: 4416 },
];

export const researchFunnel = [
  { step: "Trial connector visit", value: 6820 },
  { step: "Questionnaire completion", value: 4310 },
  { step: "Trial match returned", value: 2980 },
  { step: "Trial detail viewed", value: 1640 },
  { step: "Account created", value: 612 },
  { step: "Research Action Center referral", value: 208 },
];

export const relaunchPrePost = [
  { metric: "Users / month", pre: 31200, post: 42800 },
  { metric: "Questionnaire start rate", pre: 0.152, post: 0.196 },
  { metric: "Questionnaire completion rate", pre: 0.548, post: 0.622 },
  { metric: "Resource action rate", pre: 0.291, post: 0.34 },
  { metric: "Mobile completion rate", pre: 0.441, post: 0.525 },
];

export const dataQualityFlags = [
  "Spanish-language questionnaire finishes (n=42) are below the small-cell threshold — descriptive only.",
  "~4.1% of landing-page rows are asset/malformed URLs and are excluded from entry-page analysis.",
  "`Questionnaire` fires as a repeated event; key-event rate is not a conversion rate.",
  "Demographics are self-reported in the questionnaire, not GA4 inferred demographics.",
  "Linkage coverage: 78% of questionnaire completers join to a GA4 session ID.",
];

export const SMALL_CELL_THRESHOLD = 50;

export const pct = (num: number, den: number) => (den ? num / den : 0);
export const fmtPct = (v: number) => `${(v * 100).toFixed(1)}%`;

export interface EquityTable {
  id: string;
  label: string;
  rows: CohortRow[];
}

export const equityTables: EquityTable[] = [
  { id: "age", label: "Age band", rows: byAge },
  { id: "gender", label: "Gender", rows: byGender },
  { id: "race", label: "Race / ethnicity", rows: byRaceEthnicity },
  { id: "language", label: "Language", rows: byLanguage },
  { id: "role", label: "User role", rows: byRole },
  { id: "device", label: "Device", rows: byDevice },
  { id: "channel", label: "Acquisition channel", rows: byChannel },
];

function table(label: string, rows: CohortRow[]) {
  const lines = rows.map(
    (r) =>
      `  ${r.segment}: users=${r.users}, starts=${r.qStarts} (${fmtPct(pct(r.qStarts, r.users))} of users), finishes=${r.qFinishes} (${fmtPct(pct(r.qFinishes, r.qStarts))} of starters), action-takers=${r.actionTakers} (${fmtPct(pct(r.actionTakers, r.qFinishes))} of completers)`,
  );
  return `${label}\n${lines.join("\n")}`;
}

/** Compact, model-friendly description of the whole mock dataset. */
export function buildDataContext(): string {
  return [
    "DATASET: BrainGuide platform, GA4 behavior joined to de-identified questionnaire demographics. Window: Jan 1 – Mar 30, 2026 (90 days).",
    "",
    table("OVERALL", [overallCohort]),
    "",
    ...equityTables.map((t) => table(t.label.toUpperCase(), t.rows) + "\n"),
    "QUESTIONNAIRE FUNNEL:",
    ...questionnaireSteps.map((s) => `  ${s.step}: ${s.value}`),
    "",
    "CLINICAL RESEARCH FUNNEL:",
    ...researchFunnel.map((s) => `  ${s.step}: ${s.value}`),
    "",
    "MARCH 2026 RELAUNCH (pre vs post):",
    ...relaunchPrePost.map((r) => `  ${r.metric}: ${r.pre} -> ${r.post}`),
    "",
    "DATA QUALITY FLAGS:",
    ...dataQualityFlags.map((f) => `  - ${f}`),
  ].join("\n");
}

export const SUGGESTED_QUESTIONS = [
  "Are we reaching priority populations equitably?",
  "Where does the questionnaire funnel leak by race and ethnicity?",
  "Is Spanish-language access functional and used?",
  "Which acquisition channels bring meaningful users, not just volume?",
  "Does mobile access create a completion barrier for older users?",
  "Did the March 2026 relaunch improve the experience for everyone?",
  "Where does the clinical research pathway leak?",
  "What three actions should we prioritize next?",
];
