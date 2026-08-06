import { RefreshCw, Sparkles, TriangleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useExplorer } from "@/lib/explorer-store";
import { Markdown } from "./Markdown";

export function AiSummary() {
  const { summary, summaryState, generateSummary } = useExplorer();

  return (
    <section
      data-tour="summary"
      className="rounded-md border border-border bg-surface"
      aria-label="AI summary"
    >
      <header className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <Sparkles className="size-4 text-primary" aria-hidden />
          <h2 className="text-sm font-medium">AI summary</h2>
          {summaryState === "streaming" && (
            <span role="status" className="text-xs text-muted-foreground">
              Generating…
            </span>
          )}
        </div>
        <Button
          size="sm"
          variant={summaryState === "ready" ? "outline" : "default"}
          onClick={generateSummary}
          disabled={summaryState === "streaming"}
          className="gap-1.5"
        >
          <RefreshCw className="size-3.5" aria-hidden />
          {summaryState === "ready" ? "Regenerate" : "Generate summary"}
        </Button>
      </header>

      <div className="p-4">
        {summaryState === "idle" && (
          <div className="flex flex-col items-center gap-2 py-8 text-center">
            <Sparkles className="size-5 text-muted-foreground" aria-hidden />
            <p className="text-sm text-muted-foreground">
              No summary yet — generate one to get an orientation on this dataset.
            </p>
          </div>
        )}

        {summaryState === "error" && (
          <div className="rounded-md border border-destructive bg-destructive/5 p-4">
            <p className="flex items-center gap-2 text-sm font-medium text-destructive">
              <TriangleAlert className="size-4" aria-hidden />
              Summary failed to generate
            </p>
            <Button size="sm" variant="outline" className="mt-3" onClick={generateSummary}>
              Retry
            </Button>
          </div>
        )}

        {(summaryState === "streaming" || summaryState === "ready") && (
          <div className="border-l-2 border-primary pl-4">
            {summaryState === "streaming" && summary.length < 40 ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-2/5" />
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-4/5" />
              </div>
            ) : (
              <Markdown content={summary} />
            )}
            {summaryState === "streaming" && (
              <span className="caret-blink-text ml-0.5 inline-block h-4 w-[2px] translate-y-0.5 bg-primary" />
            )}
          </div>
        )}
      </div>
    </section>
  );
}
