import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";
import { CheckCircle2, TriangleAlert } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// Phase 5 GA4 callback — mounted now as the Task 0 validateSearch spike.
const callbackSearch = z.object({
  status: z.enum(["success", "cancelled", "error"]).optional(),
  reason: z.string().optional(),
});

export const Route = createFileRoute("/auth/ga4/callback")({
  validateSearch: callbackSearch,
  component: Ga4CallbackPage,
});

function Ga4CallbackPage() {
  const { status, reason } = Route.useSearch();

  if (status === "success") {
    return (
      <main className="flex min-h-dvh items-center justify-center bg-background p-6">
        <Card className="w-full max-w-md">
          <CardHeader className="flex items-center gap-2 text-center">
            <CheckCircle2 className="h-8 w-8 text-emerald-500" aria-hidden />
            <CardTitle>Google Analytics connected</CardTitle>
          </CardHeader>
          <CardContent className="text-center text-sm text-muted-foreground">
            <p>Returning to your workspace…</p>
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
          <CardTitle>Connection failed</CardTitle>
        </CardHeader>
        <CardContent className="text-center text-sm text-muted-foreground">
          <p>{reason ?? (status === "cancelled" ? "The connection was cancelled." : "Google Analytics is not connected.")}</p>
        </CardContent>
      </Card>
    </main>
  );
}
