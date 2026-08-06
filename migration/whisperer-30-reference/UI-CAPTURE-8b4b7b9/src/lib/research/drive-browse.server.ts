const GATEWAY = "https://connector-gateway.lovable.dev";

export interface DriveEntry {
  id: string;
  name: string;
  mimeType: string;
  modifiedTime?: string;
  size?: string;
  webViewLink?: string;
  iconLink?: string;
}

export type BrowseState = "ready" | "not_configured" | "permission" | "error";

export interface BrowseResult {
  state: BrowseState;
  message?: string;
  setupHint?: string;
  files: DriveEntry[];
}

const SETUP_HINT =
  "Connect the Google Drive connector in Lovable settings with your Google account and grant read access to the folder holding your exports.";

function driveHeaders() {
  const lovableKey = process.env["LOVABLE_API_KEY"];
  const driveKey = process.env["GOOGLE_DRIVE_API_KEY"];
  if (!lovableKey || !driveKey) return null;
  return {
    Authorization: `Bearer ${lovableKey}`,
    "X-Connection-Api-Key": driveKey,
  };
}

function escapeTerm(term: string) {
  return term.replace(/['\\]/g, "\\$&");
}

export async function browseDrive(opts: {
  search?: string;
  folderId?: string;
}): Promise<BrowseResult> {
  const headers = driveHeaders();
  if (!headers) {
    return {
      state: "not_configured",
      message: "No Google Drive connection is linked to this project.",
      setupHint: SETUP_HINT,
      files: [],
    };
  }

  const search = (opts.search ?? "").trim();
  const clauses = ["trashed = false"];
  if (search) clauses.push(`name contains '${escapeTerm(search)}'`);
  else clauses.push(`'${escapeTerm(opts.folderId || "root")}' in parents`);

  const params = new URLSearchParams({
    pageSize: "50",
    orderBy: "folder,modifiedTime desc",
    fields: "files(id,name,mimeType,modifiedTime,size,webViewLink,iconLink)",
    q: clauses.join(" and "),
  });

  try {
    const res = await fetch(`${GATEWAY}/google_drive/drive/v3/files?${params}`, { headers });
    if (!res.ok) {
      const body = await res.text().catch(() => "");
      if (res.status === 401 || res.status === 403) {
        return {
          state: "permission",
          message: "Drive rejected the request — the connection lacks read permission or its access expired.",
          setupHint: "Reconnect Google Drive in Lovable settings and include the drive.readonly scope.",
          files: [],
        };
      }
      return { state: "error", message: `Drive request failed [${res.status}]: ${body}`, files: [] };
    }
    const files = ((await res.json()) as { files?: DriveEntry[] }).files ?? [];
    return { state: "ready", files };
  } catch (err) {
    return {
      state: "error",
      message: err instanceof Error ? err.message : "Unknown Drive error",
      files: [],
    };
  }
}
