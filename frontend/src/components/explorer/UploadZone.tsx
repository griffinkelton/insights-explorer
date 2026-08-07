import { useCallback, useRef, useState } from "react";
import { FileUp, Loader2 } from "lucide-react";
import { useExplorer } from "@/lib/explorer-store";
import { cn } from "@/lib/utils";

const ACCEPTED = ".csv,.xlsx,.xls";

export function UploadZone() {
  const { loadData, loadState } = useExplorer();
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const loading = loadState === "loading";

  const handleFile = useCallback(
    (file: File | undefined) => {
      if (file && !loading) void loadData(file);
    },
    [loadData, loading],
  );

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Upload a CSV, XLSX, or XLS file"
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          inputRef.current?.click();
        }
      }}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFile(e.dataTransfer.files[0]);
      }}
      className={cn(
        "group flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        dragging
          ? "border-primary bg-primary/5"
          : "border-border bg-card hover:border-primary/50 hover:bg-accent/40",
        loading && "pointer-events-none opacity-70",
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        className="sr-only"
        onChange={(e) => {
          handleFile(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
      {loading ? (
        <>
          <Loader2 className="h-8 w-8 animate-spin text-primary" aria-hidden />
          <p className="text-sm font-medium">Uploading & parsing…</p>
          <p className="text-xs text-muted-foreground">
            Reading rows, building preview, and scoring quality.
          </p>
        </>
      ) : (
        <>
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary transition-transform group-hover:scale-105">
            <FileUp className="h-6 w-6" aria-hidden />
          </span>
          <div>
            <p className="text-sm font-medium">
              Drop your file here, or <span className="text-primary underline underline-offset-4">browse</span>
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              CSV, XLSX, or XLS · up to 25 MB · parsed server-side
            </p>
          </div>
        </>
      )}
    </div>
  );
}
