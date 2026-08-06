import { useMemo, useState } from "react";
import { ArrowDown, ArrowUp, Calendar, ChevronDown, Hash, Type } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { dailyRows, previewColumns, type DayRow } from "@/lib/mock-ga4";

const typeIcon = { date: Calendar, number: Hash, string: Type };

export function DataPreview() {
  const [sort, setSort] = useState<{ key: keyof DayRow; dir: "asc" | "desc" }>({
    key: "date",
    dir: "asc",
  });
  const [expanded, setExpanded] = useState(false);

  const rows = useMemo(() => {
    const sorted = [...dailyRows].sort((a, b) => {
      const av = a[sort.key];
      const bv = b[sort.key];
      const cmp = typeof av === "number" && typeof bv === "number"
        ? av - bv
        : String(av).localeCompare(String(bv));
      return sort.dir === "asc" ? cmp : -cmp;
    });
    return expanded ? sorted.slice(0, 30) : sorted.slice(0, 10);
  }, [sort, expanded]);

  return (
    <section className="rounded-md border border-border bg-surface" aria-label="Data preview">
      <header className="flex items-center justify-between border-b border-border px-4 py-3">
        <div>
          <h2 className="text-sm font-medium">Data preview</h2>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Showing {rows.length} of {dailyRows.length} aggregated day rows
          </p>
        </div>
      </header>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-surface-2">
              {previewColumns.map((c) => {
                const Icon = typeIcon[c.type];
                const active = sort.key === c.key;
                return (
                  <th key={c.key} scope="col" className="p-0">
                    <button
                      onClick={() =>
                        setSort((s) =>
                          s.key === c.key
                            ? { key: c.key, dir: s.dir === "asc" ? "desc" : "asc" }
                            : { key: c.key, dir: "asc" },
                        )
                      }
                      className={cn(
                        "flex w-full items-center gap-1.5 px-4 py-2.5 text-left text-[11px] font-medium tracking-wide uppercase hover:bg-accent",
                        active ? "text-foreground" : "text-muted-foreground",
                      )}
                    >
                      <Icon className="size-3 shrink-0 opacity-70" aria-hidden />
                      {c.label}
                      {active &&
                        (sort.dir === "asc" ? (
                          <ArrowUp className="size-3 text-primary" aria-hidden />
                        ) : (
                          <ArrowDown className="size-3 text-primary" aria-hidden />
                        ))}
                    </button>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.date} className="border-b border-border/60 last:border-0 hover:bg-accent/40">
                {previewColumns.map((c) => (
                  <td
                    key={c.key}
                    className={cn(
                      "px-4 py-2 whitespace-nowrap",
                      c.type === "number" ? "num text-right text-foreground" : "text-muted-foreground",
                    )}
                  >
                    {c.type === "number" && typeof r[c.key] === "number"
                      ? (r[c.key] as number) < 1
                        ? `${((r[c.key] as number) * 100).toFixed(1)}%`
                        : (r[c.key] as number).toLocaleString()
                      : String(r[c.key])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="border-t border-border p-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setExpanded((e) => !e)}
          className="w-full gap-1.5 text-xs text-muted-foreground"
        >
          <ChevronDown className={cn("size-3.5 transition-transform", expanded && "rotate-180")} aria-hidden />
          {expanded ? "Show less" : "Show more rows"}
        </Button>
      </div>
    </section>
  );
}
