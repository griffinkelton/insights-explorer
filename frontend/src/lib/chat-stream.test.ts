import { describe, expect, it, vi } from "vitest";
import { parseSseFrame, readChatStream, type ChatStreamHandlers } from "./chat-stream";

function sseResponse(frames: string[]): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      for (const f of frames) controller.enqueue(encoder.encode(f));
      controller.close();
    },
  });
  return new Response(stream, { status: 200, headers: { "content-type": "text/event-stream" } });
}

function makeHandlers() {
  const onText = vi.fn();
  const onError = vi.fn();
  const onDone = vi.fn();
  const onUsage = vi.fn();
  const onWarning = vi.fn();
  const handlers: ChatStreamHandlers = { onText, onError, onDone, onUsage, onWarning };
  return { ...handlers, onText, onError, onDone, onUsage, onWarning };
}

describe("parseSseFrame", () => {
  it("parses a named event with a JSON data payload", () => {
    const { event, data } = parseSseFrame('event: text\ndata: {"type":"text","content":"hi"}');
    expect(event).toBe("text");
    expect(data).toEqual({ type: "text", content: "hi" });
  });

  it("joins multi-line data payloads with newlines (SSE spec) before parsing", () => {
    // JSON whitespace (including \n) between tokens keeps this valid when joined.
    const { data } = parseSseFrame('event: error\ndata: {"type":\ndata: "error"}');
    expect(data).toEqual({ type: "error" });
  });

  it("throws on a frame with no data line", () => {
    expect(() => parseSseFrame("event: done")).toThrow(/no data line/);
  });
});

describe("readChatStream — terminal behavior (C5)", () => {
  it("text → done: appends text deltas, done exactly once, no [DONE] anywhere", async () => {
    const h = makeHandlers();
    const res = sseResponse([
      'event: text\ndata: {"type":"text","content":"Hel"}\n\n',
      'event: text\ndata: {"type":"text","content":"lo"}\n\n',
      'event: done\ndata: {"type":"done"}\n\n',
    ]);
    await readChatStream(res, h);
    expect(h.onText).toHaveBeenNthCalledWith(1, "Hel");
    expect(h.onText).toHaveBeenNthCalledWith(2, "lo");
    expect(h.onDone).toHaveBeenCalledTimes(1);
    expect(h.onError).not.toHaveBeenCalled();
  });

  it("text → error → done: keeps partial output, surfaces typed error, done closes", async () => {
    const h = makeHandlers();
    const res = sseResponse([
      'event: text\ndata: {"type":"text","content":"Partial"}\n\n',
      'event: error\ndata: {"type":"error","code":"provider_unavailable","retryable":true,"message":"Provider down"}\n\n',
      'event: done\ndata: {"type":"done"}\n\n',
    ]);
    await readChatStream(res, h);
    expect(h.onText).toHaveBeenCalledWith("Partial");
    expect(h.onError).toHaveBeenCalledWith("provider_unavailable", "Provider down", true, undefined);
    expect(h.onDone).toHaveBeenCalledTimes(1);
  });

  it("error → done (failure before any text)", async () => {
    const h = makeHandlers();
    const res = sseResponse([
      'event: error\ndata: {"type":"error","code":"ai_busy","retryable":true,"message":"Busy","retry_after_seconds":30}\n\n',
      'event: done\ndata: {"type":"done"}\n\n',
    ]);
    await readChatStream(res, h);
    expect(h.onText).not.toHaveBeenCalled();
    expect(h.onError).toHaveBeenCalledWith("ai_busy", "Busy", true, 30);
    expect(h.onDone).toHaveBeenCalledTimes(1);
  });

  it("warning + usage events are forwarded", async () => {
    const h = makeHandlers();
    const res = sseResponse([
      'event: warning\ndata: {"type":"warning","code":"identifiers_removed_for_ai","message":"Removed","removed_columns":["email"]}\n\n',
      'event: usage\ndata: {"type":"usage","input_tokens":10,"output_tokens":5}\n\n',
      'event: done\ndata: {"type":"done"}\n\n',
    ]);
    await readChatStream(res, h);
    expect(h.onWarning).toHaveBeenCalledWith("Removed", ["email"]);
    expect(h.onUsage).toHaveBeenCalledWith(10, 5);
  });

  it("transport closing without a terminal event synthesizes connection_closed", async () => {
    const h = makeHandlers();
    const res = sseResponse(['event: text\ndata: {"type":"text","content":"oops"}\n\n']);
    await readChatStream(res, h);
    expect(h.onDone).not.toHaveBeenCalled();
    expect(h.onError).toHaveBeenCalledWith("connection_closed", expect.stringContaining("terminal"), true, undefined);
  });

  it("a non-ok response throws ApiRequestError with status", async () => {
    const h = makeHandlers();
    const res = new Response(null, { status: 503 });
    await expect(readChatStream(res, h)).rejects.toMatchObject({ status: 503 });
  });
});
