// CAPTURED REFERENCE (2026-08-05) — source: griffinkelton/insights-whisperer-30 @ a71c3712cb5228b477a9147770aac36faa70cb2c.
// Reference only — do not edit. Original content below verbatim.
// See migration/whisperer-30-reference/WHISPERER-30-REFERENCE.md for why this file was captured.

import { buildDataContext } from "@/lib/mock-braintree";
import type { SourceLink, SourceStatus } from "./types";

const GATEWAY = "https://connector-gateway.lovable.dev";

export interface SourceContext {
  status: SourceStatus;
  /** Text handed to the model as grounding material. Empty when unavailable. */
  context: string;
  links: SourceLink[];
}

export interface ResearchSource {
  id: string;
  label: string;
  /** Cheap check that needs no network call. */
  check: () => SourceStatus;
  /** Full fetch used by the research flow. */
  load: (query: string) => Promise<SourceContext>;
}

function status(
  id: string,
  label: string,
  state: SourceStatus["state"],
  detail: string,
  setupHint?: string,
): SourceStatus {
  return { id, label, state, detail, ...(setupHint ? { setupHint } : {}) };
}

/* ------------------------------- GA4 ------------------------------- */

const GA4_SETUP =
  "Connect the Google Analytics connector in Lovable settings and pick the GA4 property whose measurement ID you want to use.";

function ga4MeasurementId() {
  return (
    process.env["GOOGLE_ANALYTICS_API_KEY"] ??
    process.env["VITE_LOVABLE_CONNECTOR_GOOGLE_ANALYTICS_API_KEY"] ??
    null
  );
}

const ga4Source: ResearchSource = {
  id: "ga4",
  label: "Google Analytics 4",
  check: () => {
    const id = ga4MeasurementId();
    return id
      ? status("ga4", "Google Analytics 4", "ready", `Measurement ID ${id} linked.`)
      : status("ga4", "Google Analytics 4", "not_configured", "No GA4 connection linked.", GA4_SETUP);
  },
  load: async () => {
    const id = ga4MeasurementId();
    if (!id) {
      return { status: ga4Source.check(), context: "", links: [] };
    }
    return {
      status: status(
        "ga4",
        "Google Analytics 4",
        "ready",
        `Measurement ID ${id} — reporting on the linked property dataset.`,
      ),
      context: `GA4 property (measurement ID ${id}) — behavioural and demographic metrics:\n${buildDataContext()}`,
      links: [
        {
          label: `GA4 property ${id}`,
          url: "https://analytics.google.com/analytics/web/",
        },
      ],
    };
  },
};

/* ------------------------------ Drive ------------------------------ */

const DRIVE_SETUP =
  "Connect the Google Drive connector in Lovable settings with your Google account and grant read access to the folder holding the research documents.";

interface DriveFile {
  id: string;
  name: string;
  mimeType: string;
  modifiedTime?: string;
  webViewLink?: string;
}

function driveHeaders() {
  const lovableKey = process.env["LOVABLE_API_KEY"];
  const driveKey = process.env["GOOGLE_DRIVE_API_KEY"];
  if (!lovableKey || !driveKey) return null;
  return {
    Authorization: `Bearer ${lovableKey}`,
    "X-Connection-Api-Key": driveKey,
  };
}

function driveEscape(term: string) {
  return term.replace(/['\\]/g, "\\$&");
}

async function driveFetch(path: string, headers: Record<string, string>) {
  const res = await fetch(`${GATEWAY}/google_drive${path}`, { headers });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    const err = new Error(`Drive request failed [${res.status}]: ${body}`) as Error & {
      httpStatus: number;
    };
    err.httpStatus = res.status;
    throw err;
  }
  return res;
}

async function readDriveFile(file: DriveFile, headers: Record<string, string>) {
  const isGoogleDoc = file.mimeType.startsWith("application/vnd.google-apps");
  if (isGoogleDoc && !/document|presentation|spreadsheet/.test(file.mimeType)) return "";
  const path = isGoogleDoc
    ? `/drive/v3/files/${file.id}/export?mimeType=text/plain`
    : `/drive/v3/files/${file.id}?alt=media`;
  const res = await driveFetch(path, headers);
  const text = await res.text();
  return text.slice(0, 6000);
}

const driveSource: ResearchSource = {
  id: "drive",
  label: "Google Drive",
  check: () =>
    driveHeaders()
      ? status("drive", "Google Drive", "ready", "Google account connected.")
      : status("drive", "Google Drive", "not_configured", "No Drive connection linked.", DRIVE_SETUP),
  load: async (query: string) => {
    const headers = driveHeaders();
    if (!headers) return { status: driveSource.check(), context: "", links: [] };

    const terms = query
      .split(/\s+/)
      .map((t) => t.replace(/[^\p{L}\p{N}-]/gu, ""))
      .filter((t) => t.length > 3)
      .slice(0, 4);
    const q = [
      "trashed = false",
      terms.length
        ? `(${terms.map((t) => `fullText contains '${driveEscape(t)}'`).join(" or ")})`
        : "",
    ]
      .filter(Boolean)
      .join(" and ");

    try {
      const res = await driveFetch(
        `/drive/v3/files?pageSize=5&orderBy=modifiedTime desc&fields=${encodeURIComponent(
          "files(id,name,mimeType,modifiedTime,webViewLink)",
        )}&q=${encodeURIComponent(q)}`,
        headers,
      );
      const files = ((await res.json()) as { files?: DriveFile[] }).files ?? [];

      if (files.length === 0) {
        return {
          status: status("drive", "Google Drive", "ready", "Connected — no matching documents found."),
          context: "",
          links: [],
        };
      }

      const docs = await Promise.all(
        files.map(async (f) => {
          const body = await readDriveFile(f, headers).catch(() => "");
          return `--- ${f.name} (${f.mimeType}, modified ${f.modifiedTime ?? "unknown"}) ---\n${
            body || "[content could not be read]"
          }`;
        }),
      );

      return {
        status: status(
          "drive",
          "Google Drive",
          "ready",
          `${files.length} document${files.length === 1 ? "" : "s"} matched.`,
        ),
        context: `Google Drive documents:\n${docs.join("\n\n")}`,
        links: files.map((f) => ({
          label: f.name,
          url: f.webViewLink ?? `https://drive.google.com/file/d/${f.id}/view`,
        })),
      };
    } catch (err) {
      const httpStatus = (err as { httpStatus?: number }).httpStatus;
      const message = err instanceof Error ? err.message : "Unknown Drive error";
      if (httpStatus === 401 || httpStatus === 403) {
        return {
          status: status(
            "drive",
            "Google Drive",
            "permission",
            "Drive rejected the request — the connection lacks read permission or its access expired.",
            "Reconnect Google Drive in Lovable settings and include the drive.readonly scope.",
          ),
          context: "",
          links: [],
        };
      }
      return {
        status: status("drive", "Google Drive", "error", message),
        context: "",
        links: [],
      };
    }
  },
};

/* ----------------------------- Registry ---------------------------- */

// Add a new source (GitHub, Notion, …) by appending an adapter here.
export const researchSources: ResearchSource[] = [ga4Source, driveSource];

export function checkSources(): SourceStatus[] {
  return researchSources.map((s) => s.check());
}

export async function loadSources(query: string): Promise<SourceContext[]> {
  return Promise.all(researchSources.map((s) => s.load(query)));
}
