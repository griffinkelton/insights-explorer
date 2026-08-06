import { useMemo, useState } from "react";
import { ChevronDown, EyeOff, FlaskConical, ShieldCheck } from "lucide-react";
import { buildInsightCandidates, type InsightCandidate } from "@/lib/insights/engine";
import { cn } from "@/lib/utils";

const uncertaintyTone: Record<InsightCandidate["uncertainty"], string> = {
  "high-confidence": "border-success/40 text-success",
  directional: "border-warning/40 text-warning",
  "descriptive-only": "border-border text-muted-foreground",
};

const categories = ["all", "equity", "funnel", "access", "reach", "quality", "change"] as const;

function Card({ c }: { c: InsightCandidate }) {
  const [open, setOpen] = useState(false);
  return (
    <li className="rounded-md border border-border bg-background/40">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-start gap-3 p-3 text-left"
      >
        <span className="mt-0.5 w-9 shrink-0 rounded bg-primary/10 px-1.5 py-0.5 text-center font-mono text-xs text-primary">
          {c.priority}
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium">{c.title}</span>
            <span
              className={cn("rounded-full border px-2 py-0.5 text-[11px]", uncertaintyTone[c.uncertainty])}
            >
              {c.uncertainty}
            </span>
            {c.suppressed && (
              <span className="flex items-center gap-1 rounded-full border border-destructive/40 px-2 py-0.5 text-[11px] text-destructive">
                <EyeOff className="size-3" aria-hidden />
                small cell suppressed
              </span>
            )}
          </span>
          <span className="mt-1 block text-sm text-muted-foreground">{c.finding}</span>
        </span>
        <ChevronDown
          className={cn("mt-1 size-4 shrink-0 text-muted-foreground transition-transform", open && "rotate-180")}
          aria-hidden
        />
      </button>

      {open && (
        <div className="space-y-3 border-t border-border px-3 py-3 text-xs">
          <div>
            <p className="mb-1 font-medium uppercase tracking-wide text-muted-foreground">Evidence</p>
            <ul className="space-y-0.5 font-mono text-[11px] text-foreground/90">
              {c.evidence.map((e, i) => (
                <li key={i}>{e}</li>
              ))}
            </ul>
          </div>
          <div>
            <p className="mb-1 font-medium uppercase tracking-wide text-muted-foreground">Caveats</p>
            <ul className="list-disc space-y-0.5 pl-4 text-muted-foreground">
              {c.caveats.map((e, i) => (
                <li key={i}>{e}</li>
              ))}
            </ul>
          </div>
          <p className="text-muted-foreground">
            <span className="font-medium uppercase tracking-wide">Provenance</span> · {c.provenance.source} ·
            metric <code className="text-foreground">{c.provenance.metric}</code>{" "}
            <span
              className={cn(
                c.provenance.metricStatus === "unavailable" ? "text-destructive" : "text-warning",
              )}
            >
              [{c.provenance.metricStatus}]
            </span>{" "}
            · grain {c.provenance.grain}
          </p>
        </div>
      )}
    </li>
  );
}

export function InsightCandidates() {
  const all = useMemo(() => buildInsightCandidates(), []);
  const [filter, setFilter] = useState<(typeof categories)[number]>("all");
  const shown = filter === "all" ? all : all.filter((c) => c.category === filter);
  const suppressed = all.filter((c) => c.suppressed).length;

  return (
    <section aria-label="Insight candidates" className="rounded-md border border-border bg-surface">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <FlaskConical className="size-4 text-primary" aria-hidden />
          <h2 className="text-sm font-medium">Insight candidates</h2>
          <span className="text-xs text-muted-foreground">
            Deterministic — computed before any model call
          </span>
        </div>
        <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <ShieldCheck className="size-3.5 text-success" aria-hidden />
          {all.length} candidates · {suppressed} suppressed
        </span>
      </header>

      <div className="flex flex-wrap gap-1.5 border-b border-border px-4 py-2">
        {categories.map((c) => (
          <button
            key={c}
            type="button"
            onClick={() => setFilter(c)}
            className={cn(
              "rounded-full border px-2.5 py-1 text-xs capitalize transition-colors",
              filter === c
                ? "border-primary bg-primary/10 text-primary"
                : "border-border text-muted-foreground hover:text-foreground",
            )}
          >
            {c}
          </button>
        ))}
      </div>

      <ul className="space-y-2 p-4">
        {shown.length === 0 ? (
          <li className="py-6 text-center text-sm text-muted-foreground">
            No candidates in this category for the current window.
          </li>
        ) : (
          shown.map((c) => <Card key={c.id} c={c} />)
        )}
      </ul>
    </section>
  );
}