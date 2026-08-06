import { useState } from "react";
import { CheckCircle2, CloudUpload, FileWarning, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useExplorer } from "@/lib/explorer-store";

export function UploadZone({ compact = false }: { compact?: boolean }) {
  const { loadData, failLoad, loadState, error } = useExplorer();
  const [over, setOver] = useState(false);

  const accept = (name: string) => {
    if (/\.(csv|xlsx)$/i.test(name)) loadData(name);
    else failLoad();
  };

  return (
    <div>
      <label
        onDragOver={(e) => {
          e.preventDefault();
          setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setOver(false);
          const f = e.dataTransfer.files[0];
          accept(f ? f.name : "dropped_export.csv");
        }}
        className={cn(
          "group flex cursor-pointer flex-col items-center justify-center gap-2 rounded-md border border-dashed border-border bg-surface/40 text-center transition-colors hover:border-primary hover:bg-primary/5 focus-within:border-primary",
          compact ? "px-3 py-4" : "px-6 py-12",
          over && "border-primary bg-primary/10",
          loadState === "error" && "border-destructive",
        )}
      >
        <input
          type="file"
          accept=".csv,.xlsx"
          className="sr-only"
          onChange={(e) => accept(e.target.files?.[0]?.name ?? "ga4_export_q1.csv")}
        />
        {loadState === "loading" ? (
          <Loader2
            role="status"
            aria-label="Loading data"
            className={cn("animate-spin text-primary", compact ? "size-4" : "size-6")}
          />
        ) : loadState === "error" ? (
          <FileWarning className={cn("text-destructive", compact ? "size-4" : "size-6")} />
        ) : (
          <CloudUpload
            className={cn(
              "text-muted-foreground transition-colors group-hover:text-primary",
              compact ? "size-4" : "size-6",
            )}
          />
        )}
        <span className={cn("font-medium text-foreground", compact ? "text-xs" : "text-sm")}>
          {loadState === "loading" ? "Parsing file…" : "Upload CSV or XLSX"}
        </span>
        {!compact && (
          <span className="text-xs text-muted-foreground">
            Drag and drop a GA4 export here, or click to browse
          </span>
        )}
      </label>
      {loadState === "error" && error && (
        <p className="mt-2 flex items-center gap-1.5 text-xs text-destructive">
          <FileWarning className="size-3.5 shrink-0" aria-hidden />
          {error}
        </p>
      )}
      {loadState === "ready" && !compact && (
        <p className="mt-2 flex items-center gap-1.5 text-xs text-success">
          <CheckCircle2 className="size-3.5 shrink-0" aria-hidden />
          File validated — 5 columns detected
        </p>
      )}
    </div>
  );
}
