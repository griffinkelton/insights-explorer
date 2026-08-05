// CAPTURED REFERENCE (2026-08-05) — source: griffinkelton/insights-whisperer-30 @ a71c3712cb5228b477a9147770aac36faa70cb2c.
// Reference only — do not edit. Original content below verbatim.
// See migration/whisperer-30-reference/WHISPERER-30-REFERENCE.md for why this file was captured.

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { defaultSource, type ChatMessage, type DataSource } from "./mock-ga4";

async function streamAi(
  body: unknown,
  onDelta: (full: string) => void,
): Promise<void> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok || !res.body) throw new Error(await res.text().catch(() => "AI request failed"));
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let acc = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    acc += decoder.decode(value, { stream: true });
    onDelta(acc);
  }
}

export type LoadState = "idle" | "loading" | "error" | "ready";
export type SummaryState = "idle" | "streaming" | "ready" | "error";

export interface Filter {
  id: string;
  field: string;
  value: string;
}

export interface Metric {
  id: string;
  name: string;
  agg: string;
}

interface ExplorerValue {
  loadState: LoadState;
  source: DataSource | null;
  error: string | null;
  filters: Filter[];
  metrics: Metric[];
  summary: string;
  summaryState: SummaryState;
  chat: ChatMessage[];
  streamingId: string | null;
  loadData: (name?: string) => void;
  failLoad: () => void;
  clearData: () => void;
  addFilter: (f: Omit<Filter, "id">) => void;
  removeFilter: (id: string) => void;
  addMetric: (m: Omit<Metric, "id">) => void;
  removeMetric: (id: string) => void;
  generateSummary: () => void;
  sendMessage: (text: string) => void;
  clearChat: () => void;
}

const ExplorerContext = createContext<ExplorerValue | null>(null);

const initialFilters: Filter[] = [
  { id: "f1", field: "date", value: "Jan – Mar 2024" },
  { id: "f2", field: "page", value: "/home" },
];

const initialMetrics: Metric[] = [
  { id: "me1", name: "sessions", agg: "sum" },
  { id: "me2", name: "users", agg: "sum" },
  { id: "me3", name: "engagement_rate", agg: "avg" },
  { id: "me4", name: "bounce_rate", agg: "avg" },
];

function now() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function ExplorerProvider({ children }: { children: ReactNode }) {
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [source, setSource] = useState<DataSource | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<Filter[]>(initialFilters);
  const [metrics, setMetrics] = useState<Metric[]>(initialMetrics);
  const [summary, setSummary] = useState("");
  const [summaryState, setSummaryState] = useState<SummaryState>("idle");
  const [chat, setChat] = useState<ChatMessage[]>([]);
  const [streamingId, setStreamingId] = useState<string | null>(null);

  const loadData = useCallback((name?: string) => {
    setError(null);
    setLoadState("loading");
    window.setTimeout(() => {
      setSource({ ...defaultSource, name: name ?? defaultSource.name });
      setLoadState("ready");
    }, 1100);
  }, []);

  const failLoad = useCallback(() => {
    setLoadState("error");
    setError("Unsupported file type. Upload a .csv or .xlsx export.");
  }, []);

  const clearData = useCallback(() => {
    setSource(null);
    setLoadState("idle");
    setError(null);
    setSummary("");
    setSummaryState("idle");
    setChat([]);
  }, []);

  const generateSummary = useCallback(() => {
    setSummaryState("streaming");
    setSummary("");
    streamAi({ mode: "summary" }, setSummary)
      .then(() => setSummaryState("ready"))
      .catch(() => setSummaryState("error"));
  }, []);

  const sendMessage = useCallback((text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    const userMsg: ChatMessage = {
      id: `u${Date.now()}`,
      role: "user",
      content: trimmed,
      timestamp: now(),
    };
    const replyId = `a${Date.now()}`;
    let history: ChatMessage[] = [];
    setChat((c) => {
      history = [...c, userMsg];
      return [...history, { id: replyId, role: "assistant", content: "", timestamp: now() }];
    });
    setStreamingId(replyId);

    const write = (content: string) =>
      setChat((c) => c.map((m) => (m.id === replyId ? { ...m, content } : m)));

    if (trimmed === "/help") {
      write(
        "**Available commands**\n\n- `/summary` — regenerate the dataset summary\n- `/equity` — equity gaps across priority populations\n- `/funnel` — questionnaire funnel drop-off\n- `/clear` — reset this conversation",
      );
      setStreamingId(null);
      return;
    }

    const prompt =
      trimmed === "/equity"
        ? "Where are the largest equity gaps across priority populations? Quantify each in percentage points."
        : trimmed === "/funnel"
          ? "Walk through the questionnaire funnel step by step and show where the biggest drop-off is, overall and by segment."
          : trimmed;

    streamAi(
      {
        messages: [
          ...history.slice(-8).map((m) => ({ role: m.role, content: m.content })).slice(0, -1),
          { role: "user", content: prompt },
        ],
      },
      write,
    )
      .catch((err: Error) =>
        write(`⚠️ ${err.message || "The analysis request failed. Try again."}`),
      )
      .finally(() => setStreamingId(null));
  }, []);

  const value = useMemo<ExplorerValue>(
    () => ({
      loadState,
      source,
      error,
      filters,
      metrics,
      summary,
      summaryState,
      chat,
      streamingId,
      loadData,
      failLoad,
      clearData,
      addFilter: (f) => setFilters((x) => [...x, { ...f, id: `f${Date.now()}` }]),
      removeFilter: (id) => setFilters((x) => x.filter((f) => f.id !== id)),
      addMetric: (m) => setMetrics((x) => [...x, { ...m, id: `me${Date.now()}` }]),
      removeMetric: (id) => setMetrics((x) => x.filter((m) => m.id !== id)),
      generateSummary,
      sendMessage,
      clearChat: () => setChat([]),
    }),
    [
      loadState,
      source,
      error,
      filters,
      metrics,
      summary,
      summaryState,
      chat,
      streamingId,
      loadData,
      failLoad,
      clearData,
      generateSummary,
      sendMessage,
    ],
  );

  return <ExplorerContext.Provider value={value}>{children}</ExplorerContext.Provider>;
}

export function useExplorer() {
  const ctx = useContext(ExplorerContext);
  if (!ctx) throw new Error("useExplorer must be used inside ExplorerProvider");
  return ctx;
}

export function useTheme() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    const stored = window.localStorage.getItem("ie-theme");
    if (stored === "light" || stored === "dark") setTheme(stored);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    window.localStorage.setItem("ie-theme", theme);
  }, [theme]);

  return { theme, toggle: () => setTheme((t) => (t === "dark" ? "light" : "dark")) };
}
