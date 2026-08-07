import { TriangleAlert, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useExplorer } from "@/lib/explorer-store";

/** Empty-state error banner — surfaces typed failures (ga4/drive error codes,
 *  upload errors) while no dataset is active. Once a dataset loads, ChatPanel
 *  owns the error display, so this banner renders only when there is no
 *  dataset (spec phase-5-ga4-drive.md Task 5: safe message keyed by code). */
export function ErrorBanner() {
  const { error, clearError, loadState } = useExplorer();
  if (!error || loadState === "ready") return null;

  return (
    <div
      role="alert"
      data-testid="error-banner"
      className="mb-4 flex items-start gap-3 rounded-lg border border-destructive/40 bg-destructive/5 px-4 py-3 text-sm text-destructive"
    >
      <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <p className="flex-1 leading-snug">{error}</p>
      <Button
        variant="ghost"
        size="icon"
        className="h-6 w-6 shrink-0 text-destructive"
        aria-label="Dismiss error"
        onClick={clearError}
      >
        <X className="h-4 w-4" aria-hidden />
      </Button>
    </div>
  );
}
