import { useState } from "react";
import { Scale, TriangleAlert } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  equityTables,
  overallCohort,
  fmtPct,
  pct,
  dataQualityFlags,
  SMALL_CELL_THRESHOLD,
} from "@/lib/mock-braintree";

export function EquityPanel() {
  const [active, setActive] = useState(equityTables[0]!.id);
  const table = equityTables.find((t) => t.id === active) ?? equityTables[0]!;

  const overallStart = pct(overallCohort.qStarts, overallCohort.users);
  const overallFinish = pct(overallCohort.qFinishes, overallCohort.qStarts);
  const overallAction = pct(overallCohort.actionTakers, overallCohort.qFinishes);

  const gap = (v: number, base: number) => {
    const d = (v - base) * 100;
    return (
      <span className={cn("num text-xs", d < -3 ? "text-destructive" : d > 3 ? "text-success" : "text-muted-foreground")}>
        {d >= 0 ? "+" : ""}
        {d.toFixed(1)}pp
      </span>
    );
  };

  return (
    <section
      data-tour="equity"
      className="rounded-md border border-border bg-surface"
      aria-label="Equity overlay"
    >
      <header className="flex flex-wrap items-center gap-2 border-b border-border px-4 py-3">
        <Scale className="size-4 text-primary" aria-hidden />
        <h2 className="text-sm font-medium">Equity overlay</h2>
        <span className="text-xs text-muted-foreground">
          GA4 behavior × self-reported questionnaire demographics
        </span>
        <div className="ml-auto flex flex-wrap gap-1">
          {equityTables.map((t) => (
            <button
              key={t.id}
              onClick={() => setActive(t.id)}
              aria-pressed={t.id === active}
              className={cn(
                "rounded-sm border px-2 py-0.5 text-[11px] transition-colors",
                t.id === active
                  ? "border-primary text-primary"
                  : "border-border text-muted-foreground hover:text-foreground",
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
      </header>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted-foreground">
              <th className="px-4 py-2 font-medium">{table.label}</th>
              <th className="px-4 py-2 text-right font-medium">Users</th>
              <th className="px-4 py-2 text-right font-medium">Start rate</th>
              <th className="px-4 py-2 text-right font-medium">Completion rate</th>
              <th className="px-4 py-2 text-right font-medium">Action rate</th>
            </tr>
          </thead>
          <tbody>
            {table.rows.map((r) => {
              const small = r.qFinishes < SMALL_CELL_THRESHOLD;
              return (
                <tr key={r.segment} className="border-b border-border/60 last:border-0">
                  <td className="px-4 py-2">
                    {r.segment}
                    {small && (
                      <span className="ml-2 inline-flex items-center gap-1 text-[10px] text-warning">
                        <TriangleAlert className="size-3" aria-hidden />
                        small cell
                      </span>
                    )}
                  </td>
                  <td className="num px-4 py-2 text-right">{r.users.toLocaleString()}</td>
                  <td className="px-4 py-2 text-right">
                    <span className="num mr-2">{fmtPct(pct(r.qStarts, r.users))}</span>
                    {gap(pct(r.qStarts, r.users), overallStart)}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <span className="num mr-2">{fmtPct(pct(r.qFinishes, r.qStarts))}</span>
                    {gap(pct(r.qFinishes, r.qStarts), overallFinish)}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <span className="num mr-2">{fmtPct(pct(r.actionTakers, r.qFinishes))}</span>
                    {gap(pct(r.actionTakers, r.qFinishes), overallAction)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <footer className="border-t border-border px-4 py-3">
        <p className="mb-1 text-xs font-medium text-muted-foreground">Caveats applied to every answer</p>
        <ul className="space-y-1 text-xs text-muted-foreground">
          {dataQualityFlags.map((f) => (
            <li key={f}>— {f}</li>
          ))}
        </ul>
      </footer>
    </section>
  );
}
