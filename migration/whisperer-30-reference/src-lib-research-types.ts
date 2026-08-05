// CAPTURED REFERENCE (2026-08-05) — source: griffinkelton/insights-whisperer-30 @ a71c3712cb5228b477a9147770aac36faa70cb2c.
// Reference only — do not edit. Original content below verbatim.
// See migration/whisperer-30-reference/WHISPERER-30-REFERENCE.md for why this file was captured.

export type SourceId = "ga4" | "drive";

export type SourceState = "ready" | "not_configured" | "permission" | "error";

export interface SourceStatus {
  id: SourceId | string;
  label: string;
  state: SourceState;
  detail: string;
  /** What the user must connect in Lovable settings when not ready. */
  setupHint?: string;
}

export interface Evidence {
  source: string;
  fact: string;
}

export interface SourceLink {
  label: string;
  url: string;
}

export interface ResearchResult {
  summary: string;
  evidence: Evidence[];
  sources: SourceLink[];
  nextSteps: string[];
}

export interface ResearchResponse {
  result: ResearchResult;
  statuses: SourceStatus[];
  model: string;
}
