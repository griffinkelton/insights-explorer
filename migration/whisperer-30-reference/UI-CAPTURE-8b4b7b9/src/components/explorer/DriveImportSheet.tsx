import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ChevronRight,
  ExternalLink,
  FileSpreadsheet,
  FileText,
  Folder,
  Loader2,
  Lock,
  RefreshCw,
  Search,
  TriangleAlert,
} from "lucide-react";
import { toast } from "sonner";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useExplorer } from "@/lib/explorer-store";

interface DriveEntry {
  id: string;
  name: string;
  mimeType: string;
  modifiedTime?: string;
  size?: string;
  webViewLink?: string;
}

interface BrowseResult {
  state: "ready" | "not_configured" | "permission" | "error";
  message?: string;
  setupHint?: string;
  files: DriveEntry[];
}

const FOLDER = "application/vnd.google-apps.folder";

function isFolder(f: DriveEntry) {
  return f.mimeType === FOLDER;
}

function isTabular(f: DriveEntry) {
  return (
    f.mimeType === "application/vnd.google-apps.spreadsheet" ||
    f.mimeType.includes("spreadsheetml") ||
    f.mimeType === "text/csv" ||
    /\.(csv|xlsx?|tsv)$/i.test(f.name)
  );
}

function fileIcon(f: DriveEntry) {
  if (isFolder(f)) return Folder;
  if (isTabular(f)) return FileSpreadsheet;
  return FileText;
}

function formatSize(bytes?: string) {
  if (!bytes) return null;
  const n = Number(bytes);
  if (!Number.isFinite(n) || n <= 0) return null;
  const units = ["B", "KB", "MB", "GB"];
  let v = n;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i += 1;
  }
  return `${v < 10 && i > 0 ? v.toFixed(1) : Math.round(v)} ${units[i]}`;
}

function formatDate(iso?: string) {
  if (!iso) return null;
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? null
    : d.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" });
}

export function DriveImportSheet({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { loadData } = useExplorer();
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [path, setPath] = useState<{ id: string; name: string }[]>([{ id: "root", name: "My Drive" }]);
  const [data, setData] = useState<BrowseResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<DriveEntry | null>(null);

  const folderId = path[path.length - 1]?.id ?? "root";

  useEffect(() => {
    const t = window.setTimeout(() => setDebounced(search.trim()), 350);
    return () => window.clearTimeout(t);
  }, [search]);

  const load = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams(debounced ? { q: debounced } : { folderId });
    fetch(`/api/drive-files?${params}`)
      .then((r) => r.json() as Promise<BrowseResult>)
      .then(setData)
      .catch(() =>
        setData({ state: "error", message: "Could not reach the Drive endpoint.", files: [] }),
      )
      .finally(() => setLoading(false));
  }, [debounced, folderId]);

  useEffect(() => {
    if (!open) return;
    setSelected(null);
    load();
  }, [open, load]);

  const files = useMemo(() => data?.files ?? [], [data]);

  const importFile = (file: DriveEntry) => {
    loadData(`drive · ${file.name}`);
    onOpenChange(false);
    toast.success("Importing from Drive", { description: file.name });
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full flex-col gap-0 p-0 sm:max-w-md">
        <SheetHeader className="gap-1 border-b border-border px-5 py-4">
          <SheetTitle className="text-base">Import from Drive</SheetTitle>
          <SheetDescription className="text-xs">
            Browse your connected Google Drive and pick an export to load into the workspace.
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-2 border-b border-border px-5 py-3">
          <div className="relative">
            <Search
              className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground"
              aria-hidden
            />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search files by name…"
              aria-label="Search Drive files"
              className="h-9 pl-8 text-sm"
            />
          </div>
          {!debounced && (
            <nav aria-label="Drive folder path" className="flex flex-wrap items-center gap-0.5 text-[11px]">
              {path.map((crumb, i) => (
                <span key={crumb.id} className="flex items-center gap-0.5">
                  {i > 0 && <ChevronRight className="size-3 text-muted-foreground" aria-hidden />}
                  <button
                    onClick={() => setPath((p) => p.slice(0, i + 1))}
                    disabled={i === path.length - 1}
                    className={cn(
                      "max-w-[10rem] truncate rounded-xs px-1 py-0.5",
                      i === path.length - 1
                        ? "text-foreground"
                        : "text-muted-foreground hover:bg-accent hover:text-foreground",
                    )}
                  >
                    {crumb.name}
                  </button>
                </span>
              ))}
            </nav>
          )}
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
          {loading ? (
            <div className="space-y-2 px-2" role="status" aria-label="Loading Drive files">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : data && data.state !== "ready" ? (
            <div className="mx-2 rounded-md border border-border bg-surface p-4 text-sm">
              <p className="flex items-center gap-2 font-medium">
                {data.state === "permission" ? (
                  <Lock className="size-4 text-warning" aria-hidden />
                ) : (
                  <TriangleAlert
                    className={cn(
                      "size-4",
                      data.state === "error" ? "text-destructive" : "text-muted-foreground",
                    )}
                    aria-hidden
                  />
                )}
                {data.state === "not_configured"
                  ? "Google Drive isn’t connected"
                  : data.state === "permission"
                    ? "Drive access denied"
                    : "Drive request failed"}
              </p>
              <p className="mt-1.5 text-xs text-muted-foreground">{data.message}</p>
              {data.setupHint && (
                <p className="mt-2 rounded-sm border border-dashed border-border p-2 text-xs text-muted-foreground">
                  {data.setupHint}
                </p>
              )}
              <Button variant="outline" size="sm" className="mt-3 gap-2" onClick={load}>
                <RefreshCw className="size-3.5" aria-hidden />
                Retry
              </Button>
            </div>
          ) : files.length === 0 ? (
            <div className="mx-2 rounded-md border border-dashed border-border p-6 text-center">
              <p className="text-sm font-medium">
                {debounced ? "No files match that search" : "This folder is empty"}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                {debounced
                  ? "Try a shorter term, or clear the search to browse folders."
                  : "Open another folder or search across your whole Drive."}
              </p>
            </div>
          ) : (
            <ul className="space-y-0.5">
              {files.map((f) => {
                const Icon = fileIcon(f);
                const folder = isFolder(f);
                const active = selected?.id === f.id;
                return (
                  <li key={f.id}>
                    <div
                      className={cn(
                        "group flex items-center gap-2 rounded-md px-2 py-2",
                        active ? "bg-primary/10" : "hover:bg-accent",
                      )}
                    >
                      <button
                        onClick={() =>
                          folder
                            ? (setPath((p) => [...p, { id: f.id, name: f.name }]), setSelected(null))
                            : setSelected(f)
                        }
                        onDoubleClick={() => !folder && importFile(f)}
                        className="flex min-w-0 flex-1 items-center gap-2 text-left"
                      >
                        <Icon
                          className={cn(
                            "size-4 shrink-0",
                            folder ? "text-primary" : "text-muted-foreground",
                          )}
                          aria-hidden
                        />
                        <span className="min-w-0">
                          <span className="block truncate text-sm">{f.name}</span>
                          <span className="block truncate text-[11px] text-muted-foreground">
                            {[folder ? "Folder" : null, formatDate(f.modifiedTime), formatSize(f.size)]
                              .filter(Boolean)
                              .join(" · ") || "—"}
                          </span>
                        </span>
                      </button>
                      {f.webViewLink && (
                        <a
                          href={f.webViewLink}
                          target="_blank"
                          rel="noreferrer"
                          aria-label={`Open ${f.name} in Google Drive`}
                          className="hidden size-7 place-items-center rounded-sm text-muted-foreground hover:text-foreground group-hover:grid"
                        >
                          <ExternalLink className="size-3.5" aria-hidden />
                        </a>
                      )}
                      {folder && <ChevronRight className="size-3.5 text-muted-foreground" aria-hidden />}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <div className="flex items-center gap-2 border-t border-border px-5 py-3">
          <p className="min-w-0 flex-1 truncate text-xs text-muted-foreground">
            {selected ? `Selected: ${selected.name}` : "Select a file to import"}
          </p>
          <Button variant="ghost" size="sm" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button size="sm" disabled={!selected} onClick={() => selected && importFile(selected)}>
            {loading && <Loader2 className="size-3.5 animate-spin" aria-hidden />}
            Import
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
