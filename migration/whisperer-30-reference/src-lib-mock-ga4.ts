// CAPTURED REFERENCE (2026-08-05) — source: griffinkelton/insights-whisperer-30 @ a71c3712cb5228b477a9147770aac36faa70cb2c.
// Reference only — do not edit. Original content below verbatim.
// See migration/whisperer-30-reference/WHISPERER-30-REFERENCE.md for why this file was captured.

export type ColumnType = "date" | "number" | "string";

export interface DayRow {
  date: string;
  sessions: number;
  users: number;
  engagement_rate: number;
  bounce_rate: number;
}

export interface PageRow {
  page: string;
  sessions: number;
  users: number;
  engagement_rate: number;
  bounce_rate: number;
  avg_duration: number;
}

export interface DataSource {
  name: string;
  rowCount: number;
  dateRange: string;
  startDate: string;
  endDate: string;
  qualityScore: number;
  missingColumns: string[];
}

export const PAGES = ["/home", "/blog/ga4-guide", "/pricing", "/docs", "/signup"] as const;

const DAYS = 90;

function seeded(i: number) {
  const x = Math.sin(i * 12.9898) * 43758.5453;
  return x - Math.floor(x);
}

export const dailyRows: DayRow[] = Array.from({ length: DAYS }, (_, i) => {
  const d = new Date(Date.UTC(2024, 0, 1));
  d.setUTCDate(d.getUTCDate() + i);
  const weekday = d.getUTCDay();
  const weekendDip = weekday === 0 || weekday === 6 ? 0.68 : 1;
  const trend = 1 + i / DAYS / 1.6;
  const noise = 0.85 + seeded(i) * 0.3;
  const sessions = Math.round(1320 * weekendDip * trend * noise);
  return {
    date: d.toISOString().slice(0, 10),
    sessions,
    users: Math.round(sessions * (0.72 + seeded(i + 99) * 0.08)),
    engagement_rate: Number((0.51 + seeded(i + 7) * 0.14).toFixed(3)),
    bounce_rate: Number((0.34 + seeded(i + 21) * 0.12).toFixed(3)),
  };
});

export const pageRows: PageRow[] = [
  { page: "/home", sessions: 48210, users: 35180, engagement_rate: 0.612, bounce_rate: 0.311, avg_duration: 96 },
  { page: "/blog/ga4-guide", sessions: 31044, users: 27890, engagement_rate: 0.704, bounce_rate: 0.268, avg_duration: 214 },
  { page: "/pricing", sessions: 18732, users: 15021, engagement_rate: 0.548, bounce_rate: 0.402, avg_duration: 78 },
  { page: "/docs", sessions: 12907, users: 9440, engagement_rate: 0.667, bounce_rate: 0.295, avg_duration: 183 },
  { page: "/signup", sessions: 7411, users: 6802, engagement_rate: 0.481, bounce_rate: 0.455, avg_duration: 61 },
];

export const previewColumns: { key: keyof DayRow; label: string; type: ColumnType }[] = [
  { key: "date", label: "date", type: "date" },
  { key: "sessions", label: "sessions", type: "number" },
  { key: "users", label: "users", type: "number" },
  { key: "engagement_rate", label: "engagement_rate", type: "number" },
  { key: "bounce_rate", label: "bounce_rate", type: "number" },
];

export const funnelSteps = [
  { step: "Session start", value: 118304 },
  { step: "Page view", value: 104711 },
  { step: "Scroll 90%", value: 61240 },
  { step: "Signup view", value: 27411 },
  { step: "Signup complete", value: 8492 },
];

export const forecastSeries = (() => {
  const tail = dailyRows.slice(-30);
  const projected = Array.from({ length: 14 }, (_, i) => {
    const d = new Date(`${dailyRows[dailyRows.length - 1]!.date}T00:00:00Z`);
    d.setUTCDate(d.getUTCDate() + i + 1);
    const base = 1580 + i * 11;
    return {
      date: d.toISOString().slice(0, 10),
      actual: null as number | null,
      forecast: Math.round(base * (0.96 + seeded(i + 400) * 0.08)),
    };
  });
  return [
    ...tail.map((r) => ({ date: r.date, actual: r.sessions, forecast: null as number | null })),
    ...projected,
  ];
})();

export const defaultSource: DataSource = {
  name: "ga4_export_q1.csv",
  rowCount: 15042,
  dateRange: "Jan 1 – Mar 30, 2024",
  startDate: "2024-01-01",
  endDate: "2024-03-30",
  qualityScore: 87,
  missingColumns: ["landing_page", "session_source"],
};

export const mockSummary = `## Executive summary

Traffic grew **34%** across the 90-day window, driven almost entirely by organic
entries into \`/blog/ga4-guide\`. Sessions averaged **1,314/day**, peaking at
**1,908** on Mar 12.

### What stands out

- **Engagement is strongest on long-form content.** \`/blog/ga4-guide\` holds a
  70.4% engagement rate — 15 points above site average.
- **Pricing is leaking.** \`/pricing\` carries the second-highest bounce rate
  (40.2%) despite being the most common step before signup.
- **Weekend volume dips ~32%** consistently, so week-over-week comparisons
  should be day-aligned.

### Recommended next step

Segment \`/pricing\` by acquisition channel — the bounce concentration looks
channel-specific rather than page-specific.`;

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export const seededChat: ChatMessage[] = [
  {
    id: "m1",
    role: "user",
    content: "Which page has the worst engagement and why might that be?",
    timestamp: "10:12",
  },
  {
    id: "m2",
    role: "assistant",
    content: `\`/signup\` has the lowest engagement rate at **48.1%**, paired with the highest bounce rate (45.5%) and the shortest average duration (61s).

That combination usually means one of three things:

1. Users arrive with intent already formed and either convert fast or leave fast.
2. The form is doing the filtering — friction above the fold.
3. Traffic quality is mixed, e.g. paid clicks landing directly on signup.

Compare \`/signup\` sessions split by referrer to separate (1) from (3).`,
    timestamp: "10:12",
  },
  {
    id: "m3",
    role: "user",
    content: "Show me the top pages by sessions",
    timestamp: "10:15",
  },
  {
    id: "m4",
    role: "assistant",
    content: `| Page | Sessions | Engagement |
| --- | --- | --- |
| /home | 48,210 | 61.2% |
| /blog/ga4-guide | 31,044 | 70.4% |
| /pricing | 18,732 | 54.8% |
| /docs | 12,907 | 66.7% |
| /signup | 7,411 | 48.1% |

\`/home\` leads on volume, but \`/blog/ga4-guide\` leads on quality of attention.`,
    timestamp: "10:15",
  },
  {
    id: "m5",
    role: "user",
    content: "Is the weekend dip normal?",
    timestamp: "10:18",
  },
  {
    id: "m6",
    role: "assistant",
    content: `Yes — it's stable and predictable, which is a good sign.

- Saturday and Sunday sessions run **~32% below** weekday averages.
- The dip magnitude varies by less than 4 points week to week.
- No weekend has broken the pattern in the 90-day window.

For trend reporting, use a 7-day rolling average so the weekly cycle doesn't read as volatility.`,
    timestamp: "10:18",
  },
];

export const mockReply = `Based on the loaded dataset, sessions trend upward through the window with a clear weekly cycle.

**Key figures**

- Total sessions: **118,304**
- Average daily sessions: **1,314**
- Best day: **Mar 12** (1,908 sessions)
- Site-wide engagement rate: **59.4%**

This is mock output — the Python analysis backend is not wired up in this build.`;
