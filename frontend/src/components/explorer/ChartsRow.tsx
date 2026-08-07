import { ChartNoAxesCombined } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useExplorer } from "@/lib/explorer-store";

export function ChartsRow() {
  const { loadState } = useExplorer();
  if (loadState !== "ready") return null;

  return (
    <Card className="border-dashed">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <ChartNoAxesCombined className="h-4 w-4 text-muted-foreground" aria-hidden />
          Charts
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed bg-muted/30 px-6 py-10 text-center">
          <ChartNoAxesCombined className="h-6 w-6 text-muted-foreground" aria-hidden />
          <p className="text-sm font-medium text-muted-foreground">
            Charts will appear when the chart-analysis API is available.
          </p>
          <p className="max-w-sm text-xs text-muted-foreground/80">
            The first slice shows data preview and quality only — chart endpoints ship with a
            later release, and charts are never derived client-side.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
