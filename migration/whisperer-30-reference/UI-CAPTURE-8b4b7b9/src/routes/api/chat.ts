import { createFileRoute } from "@tanstack/react-router";
import { streamText } from "ai";
import { createLovableAiGatewayProvider } from "@/lib/ai-gateway.server";
import { buildDataContext } from "@/lib/mock-braintree";

type Msg = { role: "user" | "assistant"; content: string };
type Body = { messages?: Msg[]; mode?: "chat" | "summary" };

const SYSTEM = `You are the analyst inside Insights Explorer, working for a public-health client (BrainGuide).
You answer questions about reach, engagement, questionnaire completion, equity across priority populations,
language access, device access, acquisition quality, the clinical-research pathway, and the March 2026 relaunch.

Rules:
- Answer ONLY from the dataset below. Never invent numbers; if a figure is not present, say so.
- Always state the denominator you used (all users, questionnaire starters, completers, action-takers).
- Compare each segment against the overall rate and quantify the gap in percentage points.
- Respect the small-cell rule: fewer than 50 in a cell is descriptive only, never a reliable rate.
- Never make causal claims; describe patterns and propose the next analysis or action.
- Be concise and concrete. Use markdown: short bolded takeaway, tight bullets, a small table when comparing segments.

DATASET
=======
${buildDataContext()}`;

const SUMMARY_PROMPT = `Write the executive summary for this dataset: overall reach and funnel, the two or three
largest equity gaps with numbers, language and device access, relaunch impact, and one recommended next step.
Use "## Executive summary", "### What stands out", "### Recommended next step".`;

export const Route = createFileRoute("/api/chat")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const body = (await request.json()) as Body;
        const key = process.env["LOVABLE_API_KEY"];
        if (!key) return new Response("Missing LOVABLE_API_KEY", { status: 500 });

        const messages: Msg[] =
          body.mode === "summary"
            ? [{ role: "user", content: SUMMARY_PROMPT }]
            : (body.messages ?? []).filter((m) => m && typeof m.content === "string" && m.content.length > 0);

        if (messages.length === 0) return new Response("Messages are required", { status: 400 });

        try {
          const gateway = createLovableAiGatewayProvider(key);
          const result = streamText({
            model: gateway("google/gemini-3.6-flash"),
            system: SYSTEM,
            messages,
          });
          return result.toTextStreamResponse();
        } catch (err) {
          const status = (err as { statusCode?: number })?.statusCode ?? 500;
          if (status === 429) return new Response("Rate limit exceeded — try again shortly.", { status: 429 });
          if (status === 402) return new Response("AI credits exhausted — add credits to continue.", { status: 402 });
          return new Response("AI request failed", { status: 500 });
        }
      },
    },
  },
});
