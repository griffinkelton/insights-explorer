import { useState } from "react";
import { CheckCircle2, Database, Lock, RefreshCw, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  EVIDENCE_SOURCE,
  SMALL_CELL_MIN,
  evidenceCatalog,
  evidenceGates,
  lastSync,
  linkageCoverage,
} from "@/lib/evidence/mock-evidence";
import { cn } from "@/lib/utils";

type Phase = "idle" | "syncing";

const gateTone = {
  unlocked: "border-success/40 text-success",
  "phase-b": "border-warning/40 text-warning",
  blocked: "border-destructive/40 text-destructive",
} as const;

export function EvidenceConnectorPanel() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [syncedAt, setSyncedAt] = useState(lastSync.at);

  const runSync = () => {
    setPhase("syncing");
    window.setTimeout(() => {
      setSyncedAt(new Date().toISOString());
      setPhase("idle");
    }, 1400);
  };

  const allowlisted = evidenceCatalog.filter((d) => d.allowlisted);
  const excluded = evidenceCatalog.filter((d) => !d.allowlisted);

  return (
    <section aria-label="Evidence connector" className="rounded-md border border-border bg-surface">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
        <div className="flex min-w-0 items-center gap-2">
          <Database className="size-4 text-primary" aria-hidden />
          <h2 className="truncate text-sm font-medium">{EVIDENCE_SOURCE.label}</h2>
          <span className="hidden text-xs text-muted-foreground md:inline">{EVIDENCE_SOURCE.mode}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 rounded-full border border-success/40 px-2.5 py-1 text-xs text-success">
            <CheckCircle2 className="size-3.5" aria-hidden />
            Connected
          </span>
          <Button size="sm" variant="outline" className="gap-1.5" onClick={runSync} disabled={phase === "syncing"}>
            <RefreshCw className={cn("size-3.5", phase === "syncing" && "animate-spin")} aria-hidden />
            {phase === "syncing" ? "Syncing…" : "Manual sync"}
          </Button>
        </div>
      </header>

      <div className="grid gap-4 p-4 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-3">
          <div className="rounded-md border border-border bg-background/40 p-3 text-xs text-muted-foreground">
            <p>
              <span className="text-foreground">{EVIDENCE_SOURCE.baseUrl}</span> · {EVIDENCE_SOURCE.transport}
            </p>
            <p className="mt-1 font-mono">
              manifest {lastSync.manifestHash.slice(0, 12)}… · last sync {syncedAt.replace("T", " ").slice(0, 16)}
            </p>
          </div>

          <div>
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Allowlisted datasets
            </h3>
            {phase === "syncing" ? (
              <div className="space-y-1.5" role="status" aria-label="Syncing datasets">
                {allowlisted.map((d) => (
                  <Skeleton key={d.id} className="h-8 w-full" />
                ))}
              </div>
            ) : (
              <ul className="divide-y divide-border rounded-md border border-border">
                {allowlisted.map((d) => {
                  const record = lastSync.records.find((r) => r.datasetId === d.id);
                  return (
                    <li key={d.id} className="flex flex-wrap items-center gap-2 px-3 py-2 text-xs">
                      <code className="min-w-0 flex-1 truncate text-foreground">{d.id}</code>
                      <span className="text-muted-foreground">{d.rows.toLocaleString()} rows</span>
                      <span
                        className={cn(
                          "rounded-full border px-2 py-0.5 text-[11px]",
                          record?.outcome === "synced"
                            ? "border-success/40 text-success"
                            : "border-warning/40 text-warning",
                        )}
                      >
                        {record?.outcome ?? "pending"}
                      </span>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          <div>
            <h3 className="mb-2 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              <Lock className="size-3.5" aria-hidden />
              Never synced
            </h3>
            <ul className="space-y-1 text-xs text-muted-foreground">
              {excluded.map((d) => (
                <li key={d.id}>
                  <code className="text-foreground">{d.id}</code> — {d.note}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="space-y-3">
          <div className="rounded-md border border-warning/40 bg-warning/5 p-3 text-xs">
            <p className="flex items-center gap-1.5 font-medium text-warning">
              <ShieldAlert className="size-3.5" aria-hidden />
              Linkage coverage {(linkageCoverage.ga4SessionsMatched * 100).toFixed(0)}%
            </p>
            <p className="mt-1 text-muted-foreground">{linkageCoverage.note}</p>
            <p className="mt-1 text-muted-foreground">
              Small-cell minimum: {SMALL_CELL_MIN}. Below-threshold cohorts: {linkageCoverage.cohortsBelowThreshold.join(", ")}.
            </p>
          </div>

          <div>
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Gates
            </h3>
            <ul className="space-y-1.5">
              {evidenceGates.map((g) => (
                <li key={g.id} className="flex items-center gap-2 text-xs">
                  <span className={cn("rounded-full border px-2 py-0.5 text-[11px]", gateTone[g.state])}>
                    {g.state}
                  </span>
                  <span className="text-muted-foreground">
                    <span className="text-foreground">Gate {g.id}</span> — {g.label}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}