// Phase 4 Task 5 — named-SSE reader for POST /api/v1/chat (Phase 3 wire format).
// Wire fields are snake_case to match the FastAPI backend byte-for-byte
// (TypedAiError.public_payload(), usage payloads). Never raw text + [DONE] (D3).
import { ApiRequestError } from "./api";

// Wire shape — matches the backend exactly (snake_case).
export type ChatStreamEvent =
  | { type: "text"; content: string }
  | { type: "usage"; input_tokens?: number; output_tokens?: number }
  | { type: "warning"; code: string; message: string; removed_columns?: string[] }
  | { type: "error"; code: string; retryable: boolean; message: string; retry_after_seconds?: number }
  | { type: "done" };

/** Parse one named-SSE frame ("event: X\ndata: {...}"). Throws on malformed frames. */
export function parseSseFrame(frame: string): { event: string; data: unknown } {
  const lines = frame.split("\n");
  let event = "message";
  const dataLines: string[] = [];
  for (const line of lines) {
    if (line.startsWith("event: ")) event = line.slice(7);
    else if (line.startsWith("data: ")) dataLines.push(line.slice(6));
  }
  if (!dataLines.length) throw new Error("Malformed SSE frame: no data line");
  return { event, data: JSON.parse(dataLines.join("\n")) };
}

export interface ChatStreamHandlers {
  onText: (content: string) => void;
  onUsage?: (inputTokens?: number, outputTokens?: number) => void;
  onWarning?: (message: string, removedColumns?: string[]) => void;
  onError: (code: string, message: string, retryable: boolean, retryAfterSeconds?: number) => void;
  onDone: () => void;
}

/**
 * Stream a POST /api/v1/chat Response. `error` is terminal for assistant content;
 * `done` closes the transport (C5). If the transport ends without a terminal
 * event, synthesize a typed `connection_closed` error so callers never silently
 * accept a truncated reply.
 */
export async function readChatStream(
  res: Response,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  if (!res.ok || !res.body) {
    throw new ApiRequestError(res.status, "AI request failed");
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let terminal = false;

  for (;;) {
    if (signal?.aborted) throw new DOMException("Aborted", "AbortError");
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const { event, data } = parseSseFrame(frame);
      const e = data as Record<string, unknown>;
      if (event === "text") {
        handlers.onText(String(e.content ?? ""));
      } else if (event === "usage") {
        handlers.onUsage?.(
          typeof e.input_tokens === "number" ? e.input_tokens : undefined,
          typeof e.output_tokens === "number" ? e.output_tokens : undefined,
        );
      } else if (event === "warning") {
        handlers.onWarning?.(
          String(e.message ?? ""),
          Array.isArray(e.removed_columns) ? (e.removed_columns as string[]) : undefined,
        );
      } else if (event === "error") {
        handlers.onError(
          String(e.code ?? "provider_error"),
          String(e.message ?? "The AI request failed."),
          e.retryable !== false,
          typeof e.retry_after_seconds === "number" ? e.retry_after_seconds : undefined,
        );
      } else if (event === "done") {
        handlers.onDone();
        terminal = true;
      }
    }
  }

  if (!terminal) {
    handlers.onError(
      "connection_closed",
      "The stream ended without a terminal event — the reply may be incomplete.",
      true,
      undefined,
    );
  }
}
