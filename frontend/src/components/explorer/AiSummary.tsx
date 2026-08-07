import { Loader2, Sparkles, TriangleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useExplorer } from "@/lib/explorer-store";
import { Markdown } from "./Markdown";

export function AiSummary() {
  const { summary, summaryState, generateSummary, loadState } = useExplorer();

  if (loadState !== "ready") return null;
  const loading = summaryState === "loading";

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Sparkles className="h-4 w-4 text-muted-foreground" aria-hidden />
          AI summary
        </CardTitle>
        {!summary && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => void generateSummary()}
            disabled={loading}
            aria-label="Generate an AI summary"
          >
            {loading ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
            ) : (
              <Sparkles className="h-3.5 w-3.5" aria-hidden />
            )}
            Generate
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
            Analyzing the dataset…
          </div>
        ) : summary ? (
          <Markdown content={summary} />
        ) : summaryState === "error" ? (
          <div className="flex items-start gap-2 text-sm text-destructive">
            <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
            <span>Summary generation failed — check that the Gemini API key is configured, then try again.</span>
          </div>
        ) : (
          <p className="py-4 text-sm text-muted-foreground">
            Generate a concise narrative of the dataset's key characteristics, trends, and
            quality caveats — computed server-side from the deterministic context.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
