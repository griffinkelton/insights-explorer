import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";
import { OAuthCallbackPage } from "@/components/auth/OAuthCallbackPage";

// Phase 5 Drive callback — the separate drive.file consent (D2) lands here
// after the server-side OAuth round-trip (same locked status vocabulary).
const callbackSearch = z.object({
  status: z.enum(["success", "cancelled", "error"]).optional(),
  reason: z.string().optional(),
});

export const Route = createFileRoute("/auth/drive/callback")({
  validateSearch: callbackSearch,
  component: DriveCallbackPage,
});

function DriveCallbackPage() {
  const { status, reason } = Route.useSearch();
  return <OAuthCallbackPage serviceLabel="Google Drive" status={status} reason={reason} />;
}
