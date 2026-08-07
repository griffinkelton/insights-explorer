import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";
import { OAuthCallbackPage } from "@/components/auth/OAuthCallbackPage";

// Phase 5 GA4 callback — backend 303s here with the locked status vocabulary.
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
  return <OAuthCallbackPage serviceLabel="Google Analytics" status={status} reason={reason} />;
}
