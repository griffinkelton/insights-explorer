import { BarChart3, Database, FileUp, LogOut, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useExplorer } from "@/lib/explorer-store";
import { cn } from "@/lib/utils";

export function Sidebar({ className }: { className?: string }) {
  const { source, filename, loadState, clearData, connectGA4, connectDrive, ga4Connected } =
    useExplorer();
  const activeDataset = loadState === "ready" && source;
  const busy = loadState === "loading";

  return (
    <nav
      aria-label="Main navigation"
      className={cn(
        "flex h-full flex-col gap-2 border-r bg-card p-3",
        className,
      )}
    >
      <div className="flex items-center gap-2 px-2 py-2">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <BarChart3 className="h-4 w-4" aria-hidden />
        </span>
        <div className="leading-tight">
          <p className="text-sm font-semibold">Insights Explorer</p>
          <p className="text-[11px] text-muted-foreground">Analytics, explained</p>
        </div>
      </div>

      <Separator className="my-1" />

      <div className="flex flex-1 flex-col gap-1">
        <div className="px-2 pb-1 pt-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
          Workspace
        </div>
        <Button
          variant="ghost"
          className="justify-start gap-2"
          aria-label="Upload a dataset"
          disabled={busy}
        >
          <FileUp className="h-4 w-4" aria-hidden />
          Upload data
        </Button>
        <Button
          variant="ghost"
          className="justify-start gap-2"
          aria-label="Import a file from Google Drive"
          onClick={() => void connectDrive()}
          disabled={busy}
        >
          <Database className="h-4 w-4" aria-hidden />
          Import from Drive
        </Button>
        <Button
          variant="ghost"
          className="justify-start gap-2"
          aria-label={ga4Connected ? "Load Google Analytics data" : "Connect Google Analytics"}
          onClick={() => void connectGA4()}
          disabled={busy}
        >
          <Sparkles className="h-4 w-4" aria-hidden />
          {ga4Connected ? "Load GA4 data" : "GA4 connect"}
        </Button>
      </div>

      <div className="space-y-1">
        {activeDataset && (
          <div className="rounded-md border bg-background px-3 py-2">
            <p className="truncate text-xs font-medium">{filename}</p>
            <p className="text-[11px] text-muted-foreground">Loaded via {source}</p>
          </div>
        )}
        <Button
          variant="ghost"
          className="w-full justify-start gap-2 text-destructive hover:text-destructive"
          onClick={() => void clearData()}
          disabled={!activeDataset}
        >
          <LogOut className="h-4 w-4" aria-hidden />
          Clear Data
        </Button>
      </div>
    </nav>
  );
}
