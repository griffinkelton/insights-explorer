import { AlertTriangle, CalendarRange, Database, Gauge } from "lucide-react";
import { useExplorer } from "@/lib/explorer-store";

export function Scorecard() {
  const { source } = useExplorer();
  if (!source) return null;

  return (
    <section
      aria-label="Data quality scorecard"
      className="grid gap-px overflow-hidden rounded-md border border-border bg-border sm:grid-cols-2 xl:grid-cols-4"
    >
      <div className="bg-surface p-4">
        <p className="flex items-center gap-1.5 text-[11px] tracking-wide text-muted-foreground uppercase">
          <Database className="size-3" aria-hidden /> Row count
        </p>
        <p className="num mt-2 text-2xl font-semibold">{source.rowCount.toLocaleString()}</p>
        <p className="mt-1 text-xs text-muted-foreground">5 columns · 0 duplicates</p>
      </div>

      <div className="bg-surface p-4">
        <p className="flex items-center gap-1.5 text-[11px] tracking-wide text-muted-foreground uppercase">
          <CalendarRange className="size-3" aria-hidden /> Date range
        </p>
        <p className="mt-2 text-lg font-semibold tracking-tight">{source.dateRange}</p>
        <p className="num mt-1 text-xs text-muted-foreground">90 days · no gaps</p>
      </div>

      <div className="bg-surface p-4">
        <p className="flex items-center gap-1.5 text-[11px] tracking-wide text-muted-foreground uppercase">
          <AlertTriangle className="size-3" aria-hidden /> Missing columns
        </p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {source.missingColumns.map((c) => (
            <span
              key={c}
              className="inline-flex items-center gap-1 rounded-sm border border-warning/40 bg-warning/10 px-1.5 py-0.5 font-mono text-[11px] text-warning"
            >
              <AlertTriangle className="size-3" aria-hidden />
              {c}
            </span>
          ))}
        </div>
        <p className="mt-2 text-xs text-muted-foreground">Optional for the loaded analyses</p>
      </div>

      <div className="bg-surface p-4">
        <p className="flex items-center gap-1.5 text-[11px] tracking-wide text-muted-foreground uppercase">
          <Gauge className="size-3" aria-hidden /> Quality score
        </p>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="num text-2xl font-semibold text-success">{source.qualityScore}</span>
          <span className="text-xs text-muted-foreground">/ 100 · Good</span>
        </div>
        <div
          role="progressbar"
          aria-valuenow={source.qualityScore}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Data quality score"
          className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-surface-2"
        >
          <div className="h-full bg-success" style={{ width: `${source.qualityScore}%` }} />
        </div>
      </div>
    </section>
  );
}
