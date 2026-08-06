import { useState } from "react";
import { ChevronDown, ScrollText } from "lucide-react";
import {
  MEASUREMENT_CONTRACT_VERSION,
  measurementContract,
  type MetricRow,
} from "@/lib/measurement-contract";
import { cn } from "@/lib/utils";

const statusTone: Record<MetricRow["status"], string> = {
  validated: "border-success/40 text-success",
  provisional: "border-warning/40 text-warning",
  unavailable: "border-destructive/40 text-destructive",
};

function Row({ m }: { m: MetricRow }) {
  const [open, setOpen] = useState(false);
  return (
    <li className="border-b border-border last:border-0">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-center gap-3 px-4 py-2.5 text-left"
      >
        <code className="min-w-0 flex-1 truncate font-mono text-xs text-foreground">{m.id}</code>
        <span className="hidden text-xs text-muted-foreground sm:block">{m.grain}</span>
        <span className={cn("rounded-full border px-2 py-0.5 text-[11px]", statusTone[m.status])}>
          {m.status}
        </span>
        <ChevronDown
          className={cn("size-4 shrink-0 text-muted-foreground transition-transform", open && "rotate-180")}
          aria-hidden
        />
      </button>
      {open && (
        <dl className="grid gap-x-6 gap-y-1.5 px-4 pb-3 text-xs sm:grid-cols-2">
          <div>
            <dt className="text-muted-foreground">Numerator</dt>
            <dd>{m.numerator}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Denominator</dt>
            <dd>{m.denominator}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Source</dt>
            <dd>{m.source}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Event mapping</dt>
            <dd>{m.eventMapping}</dd>
          </div>
          {m.blockedBy && (
            <div className="sm:col-span-2">
              <dt className="text-muted-foreground">Blocked by</dt>
              <dd className="text-destructive">{m.blockedBy}</dd>
            </div>
          )}
          <div className="sm:col-span-2">
            <dt className="text-muted-foreground">Known limitations</dt>
            <dd>
              <ul className="list-disc pl-4">
                {m.limitations.map((l, i) => (
                  <li key={i}>{l}</li>
                ))}
              </ul>
            </dd>
          </div>
        </dl>
      )}
    </li>
  );
}

export function MeasurementContractPanel() {
  const counts = measurementContract.reduce<Record<string, number>>((acc, m) => {
    acc[m.status] = (acc[m.status] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <section
      aria-label="GA4 measurement contract"
      className="rounded-md border border-border bg-surface"
    >
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <ScrollText className="size-4 text-primary" aria-hidden />
          <h2 className="text-sm font-medium">GA4 measurement contract</h2>
          <span className="text-xs text-muted-foreground">{MEASUREMENT_CONTRACT_VERSION}</span>
        </div>
        <span className="text-xs text-muted-foreground">
          {counts["provisional"] ?? 0} provisional · {counts["unavailable"] ?? 0} unavailable ·{" "}
          {counts["validated"] ?? 0} validated
        </span>
      </header>
      <p className="border-b border-border px-4 py-2 text-xs text-muted-foreground">
        No metric reaches the insights layer or the model until it has a row here. Unavailable rows are
        never presented as measured.
      </p>
      <ul>
        {measurementContract.map((m) => (
          <Row key={m.id} m={m} />
        ))}
      </ul>
    </section>
  );
}