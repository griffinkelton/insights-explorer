import { createFileRoute } from "@tanstack/react-router";
import { browseDrive } from "@/lib/research/drive-browse.server";

export const Route = createFileRoute("/api/drive-files")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const url = new URL(request.url);
        const result = await browseDrive({
          search: url.searchParams.get("q") ?? "",
          folderId: url.searchParams.get("folderId") ?? "",
        });
        return Response.json(result, { status: result.state === "error" ? 502 : 200 });
      },
    },
  },
});
