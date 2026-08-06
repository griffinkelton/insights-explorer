import { useState } from "react";
import {
  BarChart3,
  CalendarRange,
  ChevronsLeft,
  ChevronsRight,
  Database,
  FolderInput,
  GraduationCap,
  Plug,
  Plus,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { Link } from "@tanstack/react-router";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useExplorer } from "@/lib/explorer-store";
import { UploadZone } from "./UploadZone";
import { DriveImportSheet } from "./DriveImportSheet";

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="px-1 pb-2 text-[10px] font-semibold tracking-[0.12em] text-muted-foreground uppercase">
      {children}
    </p>
  );
}

export function SidebarContent({
  collapsed,
  onToggle,
  onReplayTour,
}: {
  collapsed: boolean;
  onToggle: () => void;
  onReplayTour: () => void;
}) {
  const {
    source,
    filters,
    metrics,
    removeFilter,
    removeMetric,
    addFilter,
    addMetric,
    clearData,
    loadData,
  } = useExplorer();
  const [confirmClear, setConfirmClear] = useState(false);
  const [driveOpen, setDriveOpen] = useState(false);

  if (collapsed) {
    return (
      <div className="flex h-full flex-col items-center gap-2 border-r border-sidebar-border bg-sidebar py-3">
        <div className="grid size-8 place-items-center rounded-md bg-primary/15 text-primary">
          <BarChart3 className="size-4" aria-hidden />
        </div>
        <Separator className="my-1 w-6" />
        {[
          { icon: Database, label: "Data sources" },
          { icon: CalendarRange, label: "Filters" },
          { icon: Sparkles, label: "Metrics" },
        ].map(({ icon: Icon, label }) => (
          <Button
            key={label}
            variant="ghost"
            size="icon"
            aria-label={label}
            onClick={onToggle}
            className="size-9 text-muted-foreground"
          >
            <Icon className="size-4" aria-hidden />
          </Button>
        ))}
        <div className="mt-auto">
          <Button
            variant="ghost"
            size="icon"
            aria-label="Expand sidebar"
            onClick={onToggle}
            className="size-9 text-muted-foreground"
          >
            <ChevronsRight className="size-4" aria-hidden />
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full w-full flex-col border-r border-sidebar-border bg-sidebar">
      <div className="flex items-center gap-2 px-3 py-3">
        <div className="grid size-8 shrink-0 place-items-center rounded-md bg-primary/15 text-primary">
          <BarChart3 className="size-4" aria-hidden />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold tracking-tight">Insights Explorer</p>
          <p className="truncate text-[11px] text-muted-foreground">GA4 analysis workspace</p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Collapse sidebar"
          onClick={onToggle}
          className="hidden size-8 text-muted-foreground lg:inline-flex"
        >
          <ChevronsLeft className="size-4" aria-hidden />
        </Button>
      </div>

      <Separator />

      <div className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
        <section data-tour="data-source">
          <SectionLabel>Data source</SectionLabel>
          <UploadZone compact />
          <div className="mt-2 grid gap-1.5">
            <Button
              variant="outline"
              size="sm"
              className="justify-start gap-2"
              onClick={() => {
                toast.info("Mock OAuth", { description: "Real GA4 connection is handled by the Python backend." });
                loadData("GA4 · property 284910233");
              }}
            >
              <Plug className="size-3.5 text-muted-foreground" aria-hidden />
              Connect GA4
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="justify-start gap-2"
              onClick={() => setDriveOpen(true)}
            >
              <FolderInput className="size-3.5 text-muted-foreground" aria-hidden />
              Import from Drive
            </Button>
          </div>
          <DriveImportSheet open={driveOpen} onOpenChange={setDriveOpen} />
        </section>

        {source && (
          <section className="rounded-md border border-sidebar-border bg-surface p-3">
            <div className="flex items-center gap-2">
              <span className="size-1.5 rounded-full bg-success" aria-hidden />
              <p className="truncate text-xs font-medium">{source.name}</p>
            </div>
            <dl className="mt-2 space-y-1 text-[11px] text-muted-foreground">
              <div className="flex justify-between gap-2">
                <dt>Rows</dt>
                <dd className="num text-foreground">{source.rowCount.toLocaleString()}</dd>
              </div>
              <div className="flex justify-between gap-2">
                <dt>Range</dt>
                <dd className="text-foreground">{source.dateRange}</dd>
              </div>
            </dl>
          </section>
        )}

        <section>
          <SectionLabel>Filters</SectionLabel>
          <Button
            variant="ghost"
            size="sm"
            className="mb-2 h-8 w-full justify-start gap-2 border border-dashed border-border text-muted-foreground"
            onClick={() => addFilter({ field: "device", value: "mobile" })}
          >
            <CalendarRange className="size-3.5" aria-hidden />
            Jan 1 – Mar 30, 2024
          </Button>
          <div className="flex flex-wrap gap-1.5">
            {filters.map((f) => (
              <span
                key={f.id}
                className="inline-flex max-w-full items-center gap-1 rounded-sm border border-border bg-surface-2 py-0.5 pr-0.5 pl-2 text-[11px]"
              >
                <span className="text-muted-foreground">{f.field}:</span>
                <span className="truncate text-foreground">{f.value}</span>
                <button
                  aria-label={`Remove ${f.field} filter`}
                  onClick={() => removeFilter(f.id)}
                  className="grid size-4 place-items-center rounded-xs text-muted-foreground hover:bg-accent hover:text-foreground"
                >
                  <X className="size-3" aria-hidden />
                </button>
              </span>
            ))}
            {filters.length === 0 && (
              <p className="text-[11px] text-muted-foreground">No filters applied</p>
            )}
            <button
              onClick={() => addFilter({ field: "channel", value: "organic" })}
              className="inline-flex items-center gap-1 rounded-sm border border-dashed border-border px-2 py-0.5 text-[11px] text-muted-foreground hover:border-primary hover:text-primary"
            >
              <Plus className="size-3" aria-hidden />
              Filter
            </button>
          </div>
        </section>

        <section>
          <div className="flex items-center justify-between">
            <SectionLabel>Active metrics</SectionLabel>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Add custom metric"
              className="mb-2 size-6 text-muted-foreground"
              onClick={() => addMetric({ name: "conversions", agg: "sum" })}
            >
              <Plus className="size-3.5" aria-hidden />
            </Button>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {metrics.map((m) => (
              <span
                key={m.id}
                className="inline-flex items-center gap-1 rounded-sm border border-primary/30 bg-primary/10 py-0.5 pr-0.5 pl-2 text-[11px] text-primary"
              >
                <span className="num">{m.name}</span>
                <span className="text-primary/60">· {m.agg}</span>
                <button
                  aria-label={`Remove ${m.name} metric`}
                  onClick={() => removeMetric(m.id)}
                  className="grid size-4 place-items-center rounded-xs hover:bg-primary/20"
                >
                  <X className="size-3" aria-hidden />
                </button>
              </span>
            ))}
          </div>
        </section>
      </div>

      <Separator />
      <div className="space-y-2 p-3">
        <Link
          to="/learn"
          className="flex items-center gap-2 rounded-md px-2 py-1.5 text-xs text-muted-foreground hover:bg-accent hover:text-foreground"
        >
          <GraduationCap className="size-3.5" aria-hidden />
          Learn the platform
        </Link>
        <button
          onClick={onReplayTour}
          className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-muted-foreground hover:bg-accent hover:text-foreground"
        >
          <Sparkles className="size-3.5" aria-hidden />
          Replay tour
        </button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            if (!confirmClear) {
              setConfirmClear(true);
              window.setTimeout(() => setConfirmClear(false), 3000);
              return;
            }
            clearData();
            setConfirmClear(false);
            toast.success("Workspace cleared");
          }}
          className={cn(
            "w-full justify-start gap-2 text-destructive/80 hover:bg-destructive/10 hover:text-destructive",
            confirmClear && "bg-destructive/10 text-destructive",
          )}
        >
          <Trash2 className="size-3.5" aria-hidden />
          {confirmClear ? "Click again to confirm" : "Clear data"}
        </Button>
      </div>
    </div>
  );
}
