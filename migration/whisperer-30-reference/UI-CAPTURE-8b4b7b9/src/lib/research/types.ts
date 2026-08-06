export type SourceId = "ga4" | "drive" | "evidence";

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