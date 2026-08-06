import { describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { act, renderHook } from "@testing-library/react";
import { ExplorerProvider, useExplorer } from "./explorer-store";
import { csvFile, expectedQuality } from "@/test/fixtures/sample";
import { server } from "@/test/server";

function renderStore() {
  return renderHook(() => useExplorer(), { wrapper: ExplorerProvider });
}

async function loadSample(hook: ReturnType<typeof renderStore>) {
  await act(async () => {
    await hook.result.current.loadData(csvFile());
  });
}

describe("explorer-store — drift matrix rows", () => {
  it("row 1/4: upload sets source/rowCount from the API response; no seeds", async () => {
    const hook = renderStore();
    // Row 4 — fresh store has empty filters/metrics until context hydrates.
    expect(hook.result.current.filters).toEqual([]);
    expect(hook.result.current.metrics).toEqual([]);
    expect(hook.result.current.source).toBeNull();

    await loadSample(hook);

    expect(hook.result.current.source).toBe("upload");
    expect(hook.result.current.context?.rowCount).toBe(1240);
    expect(hook.result.current.context?.filename).toBe("sessions.csv");
    expect(hook.result.current.loadState).toBe("ready");
    expect(hook.result.current.previewRows.length).toBeGreaterThan(0);
    // Hydrated from GET /data/quality — snake_case wire normalized to camelCase.
    expect(hook.result.current.quality).toEqual(expectedQuality);
  });

  it("row 2: upload failure maps server typed errors (413) to a message", async () => {
    server.use(
      http.post("/api/v1/upload", () =>
        HttpResponse.json({ detail: "Uploaded file exceeds the 25 MB browser limit." }, { status: 413 }),
      ),
    );
    const hook = renderStore();
    await loadSample(hook);
    expect(hook.result.current.loadState).toBe("error");
    expect(hook.result.current.error).toContain("25 MB");
  });

  it("row 3: Clear Data resets derived state and calls POST /data/clear", async () => {
    const hook = renderStore();
    await loadSample(hook);
    await act(async () => {
      hook.result.current.addFilter({ column: "channel", operator: "eq", value: "organic" });
      hook.result.current.addMetric({ column: "sessions", aggregation: "sum" });
    });
    expect(hook.result.current.filters).toHaveLength(1);
    expect(hook.result.current.metrics).toHaveLength(1);

    await act(async () => {
      await hook.result.current.clearData();
    });

    expect(hook.result.current.filters).toEqual([]);
    expect(hook.result.current.metrics).toEqual([]);
    expect(hook.result.current.source).toBeNull();
    expect(hook.result.current.quality).toBeNull();
    expect(hook.result.current.previewRows).toEqual([]);
    expect(hook.result.current.loadState).toBe("idle");
  });

  it("row 6: summary request is a POST with { mode: summary } — no dataset reference", async () => {
    let body: unknown;
    server.use(
      http.post("/api/v1/analysis/summary", async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({
          summary: "Sessions grew steadily.",
          model: "gemini-2.5-flash",
          usage: { input_tokens: 300, output_tokens: 40, thoughts_token_count: 0, total_token_count: 340 },
        });
      }),
    );
    const hook = renderStore();
    await loadSample(hook);
    await act(async () => {
      await hook.result.current.generateSummary();
    });
    expect(body).toEqual({ mode: "summary" });
    expect(hook.result.current.summary).toContain("Sessions grew");
    expect(hook.result.current.summaryState).toBe("ready");
  });

  it("rows 7/11: sendMessage posts { messages, mode } and streams text→done", async () => {
    let body: { messages: { role: string; content: string }[]; mode: string } | undefined;
    server.use(
      http.post("/api/v1/chat", async ({ request }) => {
        body = (await request.json()) as typeof body;
        const encoder = new TextEncoder();
        const stream = new ReadableStream({
          start(controller) {
            controller.enqueue(encoder.encode('event: text\ndata: {"type":"text","content":"Trends are up"}\n\n'));
            controller.enqueue(encoder.encode('event: done\ndata: {"type":"done"}\n\n'));
            controller.close();
          },
        });
        return new HttpResponse(stream, {
          headers: { "content-type": "text/event-stream" },
        });
      }),
    );
    const hook = renderStore();
    await loadSample(hook);
    await act(async () => {
      await hook.result.current.sendMessage("What are the trends?");
    });

    expect(body?.mode).toBe("chat");
    expect(body?.messages.at(-1)).toEqual({ role: "user", content: "What are the trends?" });
    expect(hook.result.current.chat).toHaveLength(2);
    expect(hook.result.current.chat[0].role).toBe("user");
    expect(hook.result.current.chat[1].content).toBe("Trends are up");
    expect(hook.result.current.chatState).toBe("ready");
    expect(hook.result.current.streamingId).toBeNull();
  });

  it("C5: text → error → done keeps partial output and marks the turn failed", async () => {
    server.use(
      http.post("/api/v1/chat", () => {
        const encoder = new TextEncoder();
        const stream = new ReadableStream({
          start(controller) {
            controller.enqueue(encoder.encode('event: text\ndata: {"type":"text","content":"Partial answer"}\n\n'));
            controller.enqueue(
              encoder.encode(
                'event: error\ndata: {"type":"error","code":"provider_unavailable","retryable":true,"message":"Provider down"}\n\n',
              ),
            );
            controller.enqueue(encoder.encode('event: done\ndata: {"type":"done"}\n\n'));
            controller.close();
          },
        });
        return new HttpResponse(stream, { headers: { "content-type": "text/event-stream" } });
      }),
    );
    const hook = renderStore();
    await loadSample(hook);
    await act(async () => {
      await hook.result.current.sendMessage("Summarize?");
    });

    // Partial assistant content retained; turn failed; user message kept (row 11).
    expect(hook.result.current.chat[1].content).toContain("Partial answer");
    expect(hook.result.current.chatState).toBe("error");
    expect(hook.result.current.error).toContain("Provider down");
    expect(hook.result.current.chat[0].role).toBe("user");
  });

  it("row 12: store types come from api-types, never mock fixtures — context normalized at the boundary", async () => {
    const hook = renderStore();
    await loadSample(hook);
    // snake_case wire (row_count/date_range) → camelCase domain (rowCount/dateRange).
    expect(hook.result.current.context?.rowCount).toBe(1240);
    expect(hook.result.current.context?.dateRange).toEqual({ start: "2026-01-01", end: "2026-05-31" });
    expect(hook.result.current.context?.filename).toBe("sessions.csv");
    expect(hook.result.current.context?.columns).toHaveLength(3);
  });
});
