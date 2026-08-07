import { CheckCircle2, CircleAlert, Columns3, FileWarning, Layers, Sigma } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useExplorer } from "@/lib/explorer-store";

function Stat({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-muted-foreground">{icon}</span>
      <div>
        <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p>
        <p className="text-sm font-medium">{value}</p>
      </div>
    </div>
  );
}

export function Scorecard() {
  const { quality, loadState } = useExplorer();

  if (loadState === "loading") {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Data quality</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-12" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (!quality) return null;

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <FileWarning className="h-4 w-4 text-muted-foreground" aria-hidden />
          Data quality
        </CardTitle>
        <Badge variant="outline" className={`grade-${quality.grade} gap-1`} aria-label={`Quality grade ${quality.grade}`}>
          <span className="text-sm font-bold">Grade {quality.grade}</span>
        </Badge>
      </CardHeader>
      <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat icon={<CheckCircle2 className="h-4 w-4" aria-hidden />} label="Complete" value={`${quality.completenessPct.toFixed(1)}%`} />
        <Stat icon={<Layers className="h-4 w-4" aria-hidden />} label="Duplicates" value={`${quality.duplicateCount} (${quality.duplicatePct.toFixed(1)}%)`} />
        <Stat icon={<Sigma className="h-4 w-4" aria-hidden />} label="Outliers" value={String(quality.outlierCount)} />
        <Stat icon={<Columns3 className="h-4 w-4" aria-hidden />} label="Columns" value={String(quality.columnCount)} />
        {quality.warnings.length > 0 && (
          <div className="sm:col-span-2 lg:col-span-4">
            <p className="mb-1 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              <CircleAlert className="h-3.5 w-3.5" aria-hidden />
              Warnings
            </p>
            <ul className="space-y-1">
              {quality.warnings.map((w, i) => (
                <li key={i} className="rounded-md bg-accent/60 px-2.5 py-1.5 text-xs text-accent-foreground">
                  {w}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
