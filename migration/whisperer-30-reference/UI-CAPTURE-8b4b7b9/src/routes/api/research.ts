import { createFileRoute } from "@tanstack/react-router";
import { streamText } from "ai";
import { createLovableAiGatewayProvider, RESEARCH_MODEL } from "@/lib/ai-gateway.server";
import { checkSources, loadSources } from "@/lib/research/sources.server";
import type { ResearchResult, SourceLink } from "@/lib/research/types";

const SYSTEM = `You are the research analyst inside Insights Explorer.
You answer a question by combining Google Analytics 4 metrics, Evidence dashboard aggregates and Google Drive documents supplied below.

Rules:
- Use ONLY the supplied context. Never invent or recalculate numbers — precomputed insight candidates are authoritative. Your job is to prioritize, explain, question assumptions and recommend.
- Respect the GA4 measurement contract: never present an \`unavailable\` metric as measured, and label \`provisional\` metrics as unvalidated.
- Never report a rate for a cell marked SUPPRESSED; give counts and say why.
- Carry each finding's caveats and provenance into your answer.
- State the denominator behind every rate, and quantify segment gaps in percentage points.
- Cells under 50 people are descriptive only, never a reliable rate.
- No causal claims — describe patterns and propose the next analysis.

Respond with ONLY a JSON object, no markdown fence, matching:
{"summary": string (markdown, 2-5 sentences),
 "evidence": [{"source": string, "fact": string}],
 "nextSteps": [string]}`;

function parseResult(raw: string): ResearchResult | null {
  const text = raw.trim().replace(/^```(?:json)?/i, "").replace(/```$/, "");
  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");
  if (start === -1 || end === -1) return null;
  try {
    const parsed = JSON.parse(text.slice(start, end + 1)) as Partial<ResearchResult>;
    if (typeof parsed.summary !== "string") return null;
    return {
      summary: parsed.summary,
      evidence: Array.isArray(parsed.evidence)
        ? parsed.evidence
            .filter((e) => e && typeof e.fact === "string")
            .map((e) => ({ source: String(e.source ?? "context"), fact: e.fact }))
            .slice(0, 12)
        : [],
      sources: [],
      nextSteps: Array.isArray(parsed.nextSteps)
        ? parsed.nextSteps.filter((s) => typeof s === "string").slice(0, 6)
        : [],
    };
  } catch {
    return null;
  }
}

export const Route = createFileRoute("/api/research")({
  server: {
    handlers: {
      GET: async () =>
        Response.json({
          statuses: checkSources(),
          model: RESEARCH_MODEL,
          aiConfigured: Boolean(process.env["LOVABLE_API_KEY"]),
        }),

      POST: async ({ request }) => {
        const { question } = (await request.json().catch(() => ({}))) as { question?: string };
        const query = (question ?? "").trim();
        if (!query) return new Response("A question is required", { status: 400 });

        const key = process.env["LOVABLE_API_KEY"];
        if (!key) {
          return Response.json(
            {
              error:
                "Lovable AI is not enabled for this project. Enable the Lovable AI integration in Lovable settings, then retry.",
              statuses: checkSources(),
            },
            { status: 503 },
          );
        }

        const loaded = await loadSources(query);
        const statuses = loaded.map((l) => l.status);
        const links: SourceLink[] = loaded.flatMap((l) => l.links);
        const context = loaded
          .map((l) => l.context)
          .filter(Boolean)
          .join("\n\n");

        if (!context) {
          return Response.json(
            {
              error:
                "No data source returned anything to reason over. Connect Google Analytics and Google Drive in Lovable settings.",
              statuses,
            },
            { status: 409 },
          );
        }

        try {
          const gateway = createLovableAiGatewayProvider(key);
          const stream = streamText({
            model: gateway(RESEARCH_MODEL),
            system: SYSTEM,
            prompt: `QUESTION\n${query}\n\nCONTEXT\n${context}`,
          });
          const text = await stream.text;
          const result = parseResult(text);

          return Response.json({
            result: result
              ? { ...result, sources: links }
              : { summary: text, evidence: [], sources: links, nextSteps: [] },
            statuses,
            model: RESEARCH_MODEL,
          });
        } catch (err) {
          const status = (err as { statusCode?: number })?.statusCode ?? 500;
          const message =
            status === 429
              ? "Rate limit exceeded — try again shortly."
              : status === 402
                ? "AI credits exhausted — add credits in Lovable settings to continue."
                : "The research request failed. Try again.";
          return Response.json({ error: message, statuses }, { status });
        }
      },
    },
  },
});