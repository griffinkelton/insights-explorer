import { useEffect } from "react";
import { Link } from "@tanstack/react-router";
import { CheckCircle2, TriangleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useExplorer } from "@/lib/explorer-store";

/** Server-side OAuth callback landing page (Phase 5 Task 5).

 *  The backend 303s here with the locked status vocabulary
 *  (success | cancelled | error&reason=<code>) after the Google round-trip.
 *  The store's ``handleGA4Callback`` refreshes server-owned connection state;
 *  no provider token ever reaches this page (browser-memory-only rule).
 */
export function OAuthCallbackPage({
  serviceLabel,
  status,
  reason,
}: {
  serviceLabel: string;
  status?: string;
  reason?: string;
}) {
  const { handleGA4Callback } = useExplorer();

  useEffect(() => {
    void handleGA4Callback({ status, reason });
  }, [handleGA4Callback, status, reason]);

  if (status === "success") {
    return (
      <main className="flex min-h-dvh items-center justify-center bg-background p-6">
        <Card className="w-full max-w-md">
          <CardHeader className="flex items-center gap-2 text-center">
            <CheckCircle2 className="h-8 w-8 text-emerald-500" aria-hidden />
            <CardTitle>{serviceLabel} connected</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center gap-4 text-center text-sm text-muted-foreground">
            <p>Returning to your workspace…</p>
            <Button asChild>
              <Link to="/">Open workspace</Link>
            </Button>
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="flex min-h-dvh items-center justify-center bg-background p-6">
      <Card className="w-full max-w-md">
        <CardHeader className="flex items-center gap-2 text-center">
          <TriangleAlert className="h-8 w-8 text-destructive" aria-hidden />
          <CardTitle>{status === "cancelled" ? "Connection cancelled" : "Connection failed"}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center gap-4 text-center text-sm text-muted-foreground">
          <p>
            {reason ??
              (status === "cancelled"
                ? "The connection was cancelled."
                : "The connection could not be completed.")}
          </p>
          <Button asChild variant="outline">
            <Link to="/">Back to workspace</Link>
          </Button>
        </CardContent>
      </Card>
    </main>
  );
}
