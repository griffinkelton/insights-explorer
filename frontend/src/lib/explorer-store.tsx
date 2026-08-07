// Phase 4 Task 4 — store wiring per STORE-DRIFT-MATRIX.md (the instruction set;
// F3's 13 steps are superseded). Server-owned state (filters/metrics/summary/chat
// context) resolves from the session; the browser holds only view state + the
// HttpOnly cookie. The union ExplorerValue keeps every captured member (drift
// row 13) — Phase 5 members are present as typed stubs, never silently removed.
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  api,
  ApiRequestError,
  mapApiError,
  setSourceFromApi,
} from "./api";
import { readChatStream } from "./chat-stream";
import type {
  ChatMessage,
  DataPreviewResponse,
  DatasetContext,
  DataSource,
  DrivePickerTokenResponse,
  ForecastResponse,
  FunnelResponse,
  QualityReport,
  UsageResponse,
} from "./api-types";

export type LoadState = "idle" | "loading" | "ready" | "error";
export type SummaryState = "idle" | "loading" | "ready" | "error";
export type ChatState = "idle" | "streaming" | "ready" | "error";

export interface Filter {
  id: string;
  column: string;
  operator: string;
  value: string;
}

export interface Metric {
  id: string;
  column: string;
  aggregation: string;
}

interface ExplorerContextValue {
  // state
  loadState: LoadState;
  source: DataSource | null;
  error: string | null;
  filters: Filter[];
  metrics: Metric[];
  summary: string;
  summaryState: SummaryState;
  chat: ChatMessage[];
  chatState: ChatState;
  streamingId: string | null;
  theme: "dark" | "light";
  quality: QualityReport | null;
  charts: unknown[];
  usage: UsageResponse | null;
  previewRows: Record<string, unknown>[];
  context: DatasetContext | null;
  filename: string | null;
  forecast: ForecastResponse | null;
  funnel: FunnelResponse | null;
  // Phase 5 — connection + Picker UI state (spec phase-5-ga4-drive.md Task 5)
  ga4Connected: boolean;
  driveConfigured: boolean;
  drivePickerOpen: boolean;
  pickerToken: DrivePickerTokenResponse | null;
  // actions
  loadData(file: File): Promise<void>;
  failLoad(message: string): void;
  clearError(): void;
  clearData(): Promise<void>;
  addFilter(f: Omit<Filter, "id">): void;
  removeFilter(id: string): void;
  addMetric(m: Omit<Metric, "id">): void;
  removeMetric(id: string): void;
  generateSummary(): Promise<void>;
  sendMessage(text: string): Promise<void>;
  retryLastTurn(): Promise<void>;
  cancelStream(): void;
  clearChat(): void;
  setSourceFromApi(payload: DataPreviewResponse | { dataset: DatasetContext }): void;
  refreshConnections(): Promise<void>;
  connectGA4(): Promise<void>;
  handleGA4Callback(params: unknown): Promise<void>;
  connectDrive(): Promise<void>;
  openDrivePicker(): Promise<void>;
  closeDrivePicker(): void;
  downloadFromDrive(selection: { requestId: string; fileId: string }): Promise<void>;
  fetchQuality(): Promise<void>;
  fetchCharts(): Promise<void>;
  fetchForecast(metricCol: string, periods?: number): Promise<void>;
  fetchFunnel(metricCol: string, steps: string[]): Promise<void>;
  exportData(): Promise<void>;
  refreshUsage(): Promise<void>;
  toggleTheme(): void;
}

const ExplorerContext = createContext<ExplorerContextValue | null>(null);

function loadTheme(): "dark" | "light" {
  try {
    const stored = localStorage.getItem("ie-theme");
    if (stored === "dark" || stored === "light") return stored;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  } catch {
    return "light";
  }
}

export function ExplorerProvider({ children }: { children: ReactNode }) {
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [source, setSource] = useState<DataSource | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<Filter[]>([]); // no seeds (drift row 4)
  const [metrics, setMetrics] = useState<Metric[]>([]); // no seeds (drift row 4)
  const [summary, setSummary] = useState("");
  const [summaryState, setSummaryState] = useState<SummaryState>("idle");
  const [chat, setChat] = useState<ChatMessage[]>([]);
  const [chatState, setChatState] = useState<ChatState>("idle");
  const [streamingId, setStreamingId] = useState<string | null>(null);
  const [theme, setTheme] = useState<"dark" | "light">(loadTheme);
  const [quality, setQuality] = useState<QualityReport | null>(null);
  const [charts, setCharts] = useState<unknown[]>([]); // placeholder only (row 13)
  const [usage, setUsage] = useState<UsageResponse | null>(null);
  const [previewRows, setPreviewRows] = useState<Record<string, unknown>[]>([]);
  const [context, setContext] = useState<DatasetContext | null>(null);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [funnel, setFunnel] = useState<FunnelResponse | null>(null);
  // Phase 5 — connection + Picker UI state (server-owned connection status;
  // the Picker token is browser-memory-only and cleared on close/select/error).
  const [ga4Connected, setGa4Connected] = useState(false);
  const [driveConfigured, setDriveConfigured] = useState(false);
  const [drivePickerOpen, setDrivePickerOpen] = useState(false);
  const [pickerToken, setPickerToken] = useState<DrivePickerTokenResponse | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const partialAssistantRef = useRef<ChatMessage | null>(null);

  // Theme side effect — keep <html> in sync with the store value.
  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    try {
      localStorage.setItem("ie-theme", theme);
    } catch {
      /* storage unavailable — theme still applies for the session */
    }
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((t) => (t === "dark" ? "light" : "dark"));
  }, []);

  const refreshUsage = useCallback(async () => {
    try {
      setUsage(await api.usage());
    } catch {
      // Usage is observability — never block the UI on it.
    }
  }, []);

  const failLoad = useCallback((message: string) => {
    setError(message);
    setLoadState("error");
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const setSourceFromApiCb = useCallback(
    (payload: DataPreviewResponse | { dataset: DatasetContext }) => {
      const normalized = setSourceFromApi(payload);
      setSource(normalized.source);
      setContext(normalized.context);
    },
    [],
  );

  const fetchQuality = useCallback(async () => {
    try {
      setQuality(await api.quality());
    } catch (err) {
      if (err instanceof ApiRequestError) failLoad(mapApiError(err.status, err.message));
    }
  }, [failLoad]);

  const loadData = useCallback(
    async (file: File) => {
      setLoadState("loading");
      setError(null);
      try {
        const uploaded = await api.upload(file);
        // Never fall back to defaultSource (drift row 1).
        setSourceFromApiCb(uploaded);
        const preview = await api.preview();
        setPreviewRows(preview.rows);
        await fetchQuality();
        void refreshUsage();
        setLoadState("ready");
      } catch (err) {
        if (err instanceof ApiRequestError) {
          failLoad(mapApiError(err.status, err.message));
        } else {
          failLoad("Upload failed. Please try again.");
        }
      }
    },
    [failLoad, fetchQuality, refreshUsage, setSourceFromApiCb],
  );

  /** Derived state dies with the dataset (drift row 3; retention policy §5).
   *  Shared by Clear Data and by dataset replacement (GA4 pull / Drive import
   *  over an existing dataset — the server clears first, the UI must too). */
  const resetDerivedState = useCallback(() => {
    setFilters([]);
    setMetrics([]);
    setSummary("");
    setSummaryState("idle");
    setChat([]);
    setChatState("idle");
    setStreamingId(null);
    setQuality(null);
    setPreviewRows([]);
    setCharts([]);
    setForecast(null);
    setFunnel(null);
    setSource(null);
    setContext(null);
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  const clearData = useCallback(async () => {
    resetDerivedState();
    try {
      await api.clear();
      await refreshUsage(); // the ledger resets server-side with Clear Data
    } catch (err) {
      if (err instanceof ApiRequestError) failLoad(mapApiError(err.status, err.message));
    }
    setLoadState("idle");
  }, [failLoad, refreshUsage, resetDerivedState]);

  const addFilter = useCallback((f: Omit<Filter, "id">) => {
    // Server-owned: kept as local view state; sync endpoints land in a later PR.
    setFilters((prev) => [...prev, { ...f, id: crypto.randomUUID() }]);
  }, []);

  const removeFilter = useCallback((id: string) => {
    setFilters((prev) => prev.filter((f) => f.id !== id));
  }, []);

  const addMetric = useCallback((m: Omit<Metric, "id">) => {
    setMetrics((prev) => [...prev, { ...m, id: crypto.randomUUID() }]);
  }, []);

  const removeMetric = useCallback((id: string) => {
    setMetrics((prev) => prev.filter((m) => m.id !== id));
  }, []);

  const generateSummary = useCallback(async () => {
    setSummaryState("loading");
    setError(null);
    try {
      const res = await api.summary();
      setSummary(res.summary);
      setSummaryState("ready");
      void refreshUsage();
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(mapApiError(err.status, err.message));
        setSummaryState("error");
      } else {
        setError("Summary generation failed.");
        setSummaryState("error");
      }
    }
  }, [refreshUsage]);

  /** Shared streaming core — sends `history + userText`, streams into a partial assistant turn. */
  const startStream = useCallback(
    async (history: ChatMessage[], text: string) => {
      const id = crypto.randomUUID();
      setStreamingId(id);
      const userMsg: ChatMessage = { role: "user", content: text, timestamp: new Date().toISOString() };
      const nextChat = [...history, userMsg];
      const assistantMsg: ChatMessage = { role: "assistant", content: "", timestamp: new Date().toISOString() };
      partialAssistantRef.current = assistantMsg;
      setChat([...nextChat, assistantMsg]);
      setChatState("streaming");
      setError(null);

      const controller = new AbortController();
      abortRef.current = controller;
      try {
        // Wire contract is { role, content } — strip client display timestamps.
        const payloadMessages = nextChat.map((m) => ({ role: m.role, content: m.content }));
        const res = await api.chatStream({ messages: payloadMessages, mode: "chat" }, controller.signal);
        await readChatStream(
          res,
          {
            onText: (content) => {
              const cur = partialAssistantRef.current;
              if (cur) {
                cur.content += content;
                setChat((prev) => {
                  const next = [...prev];
                  next[next.length - 1] = { ...cur };
                  return next;
                });
              }
            },
            onWarning: () => {
              /* identifier-removal warnings surface via the error banner if relevant */
            },
            onError: (code, message) => {
              // Typed SSE error is terminal for assistant content (C5) — the
              // turn failed even though `done` still closes the transport.
              setError(code === "ai_busy" ? `${message} Wait a moment, then retry.` : message);
              setChatState("error");
            },
            onDone: () => {
              partialAssistantRef.current = null;
              // Never clobber an error terminal state — only success reaches ready.
              setChatState((s) => (s === "error" ? s : "ready"));
            },
          },
          controller.signal,
        );
      } catch (err) {
        const isAbort = err instanceof DOMException && err.name === "AbortError";
        const cur = partialAssistantRef.current;
        const interrupted = isAbort ? "_Interrupted._" : "_Request failed — retry to continue._";
        if (cur) {
          cur.content = cur.content ? `${cur.content}\n\n${interrupted}` : interrupted;
          setChat((prev) => {
            const next = [...prev];
            next[next.length - 1] = { ...cur };
            return next;
          });
        }
        if (!isAbort) {
          setError(
            err instanceof ApiRequestError
              ? mapApiError(err.status, err.message)
              : "The AI request failed. Check the connection and try again.",
          );
        }
        setChatState("error");
      } finally {
        abortRef.current = null;
        setStreamingId(null);
        void refreshUsage();
      }
    },
    [refreshUsage],
  );

  const sendMessage = useCallback(
    async (text: string) => {
      if (chatState === "streaming") return;
      // Drop any stale partial assistant turn from an interrupted attempt.
      const history = partialAssistantRef.current ? chat.slice(0, -1) : chat;
      await startStream(history, text);
    },
    [chat, chatState, startStream],
  );

  const retryLastTurn = useCallback(async () => {
    // Drift row 11: retry sends the SAME { messages, mode } history — strip any
    // trailing partial assistant turn, then re-send the last user turn. Never
    // duplicate the user message or the assistant turn. (The typed-error path
    // clears partialAssistantRef on `done`, so derive from chat shape, not the
    // ref — otherwise the last user turn gets duplicated.)
    if (chatState === "streaming") return;
    const withoutPartial = chat.at(-1)?.role === "assistant" ? chat.slice(0, -1) : chat;
    const lastUser = [...withoutPartial].reverse().find((m) => m.role === "user");
    if (!lastUser) return;
    await startStream(withoutPartial.slice(0, -1), lastUser.content);
  }, [chat, chatState, startStream]);

  const cancelStream = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const clearChat = useCallback(() => {
    // Server chat context clears in the same call path as Clear Data (row 8/3).
    setChat([]);
    setChatState("idle");
    partialAssistantRef.current = null;
  }, []);

  const fetchCharts = useCallback(async () => {
    // Placeholder only — no chart endpoint exists yet; ChartsRow renders an
    // honest empty state. Never derive charts client-side (track B).
    setCharts([]);
  }, []);

  const fetchForecast = useCallback(
    async (metricCol: string, periods = 30) => {
      try {
        setForecast(await api.forecast(metricCol, periods));
      } catch (err) {
        if (err instanceof ApiRequestError) setError(mapApiError(err.status, err.message));
      }
    },
    [],
  );

  const fetchFunnel = useCallback(
    async (metricCol: string, steps: string[]) => {
      try {
        setFunnel(await api.funnel(metricCol, steps));
      } catch (err) {
        if (err instanceof ApiRequestError) setError(mapApiError(err.status, err.message));
      }
    },
    [],
  );

  // ── Phase 5 — GA4 + Drive (spec phase-5-ga4-drive.md Task 5) ────────────
  const refreshConnections = useCallback(async () => {
    try {
      const [ga4, drive] = await Promise.all([api.ga4Status(), api.driveStatus()]);
      setGa4Connected(ga4.connected);
      setDriveConfigured(drive.configured);
    } catch {
      // Connection status is best-effort — never block the UI on it.
    }
  }, []);

  const connectGA4 = useCallback(async () => {
    setError(null);
    try {
      const status = await api.ga4Status();
      if (!status.connected) {
        // Disconnected → server-owned OAuth: browser follows the auth URL.
        const { authorizationUrl } = await api.ga4Connect("ga4");
        window.location.assign(authorizationUrl);
        return;
      }
      // Connected → the same affordance becomes "Load GA4 data" (Task 5 pull).
      resetDerivedState();
      setLoadState("loading");
      const res = await api.ga4Pull();
      setSourceFromApiCb(res);
      const preview = await api.preview();
      setPreviewRows(preview.rows);
      await fetchQuality();
      void refreshUsage();
      setLoadState("ready");
    } catch (err) {
      if (err instanceof ApiRequestError) {
        failLoad(mapApiError(err.status, err.message, err.code));
      } else {
        failLoad("Could not start Google Analytics sign-in.");
      }
    }
  }, [failLoad, fetchQuality, refreshUsage, resetDerivedState, setSourceFromApiCb]);

  const handleGA4Callback = useCallback(
    async (params: unknown) => {
      const p = (params ?? {}) as { status?: string; reason?: string };
      if (p.status === "success") {
        await refreshConnections();
      } else if (p.status === "cancelled") {
        setError("Google sign-in was cancelled.");
      } else {
        setError(p.reason ? `Google connection failed: ${p.reason}` : "Google connection failed.");
      }
    },
    [refreshConnections],
  );

  const openDrivePicker = useCallback(async () => {
    setError(null);
    try {
      // JIT token — fetched immediately before Picker opens, memory-only.
      const token = await api.drivePickerToken();
      setPickerToken(token);
      setDrivePickerOpen(true);
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(mapApiError(err.status, err.message, err.code));
      } else {
        setError("Could not open the file picker.");
      }
    }
  }, []);

  const closeDrivePicker = useCallback(() => {
    // Token cleared on close/cancel/select — never persisted (Task 4).
    setPickerToken(null);
    setDrivePickerOpen(false);
  }, []);

  const connectDrive = useCallback(async () => {
    setError(null);
    try {
      const status = await api.driveStatus();
      if (!status.configured) {
        // Separate drive.file consent (D2) — server-owned OAuth flow.
        const { authorizationUrl } = await api.ga4Connect("drive");
        window.location.assign(authorizationUrl);
        return;
      }
      await openDrivePicker();
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(mapApiError(err.status, err.message, err.code));
      } else {
        setError("Could not start Drive import.");
      }
    }
  }, [openDrivePicker]);

  const downloadFromDrive = useCallback(
    async (selection: { requestId: string; fileId: string }) => {
      resetDerivedState();
      setLoadState("loading");
      setError(null);
      try {
        const res = await api.driveDownload(selection);
        setSourceFromApiCb(res);
        const preview = await api.preview();
        setPreviewRows(preview.rows);
        await fetchQuality();
        closeDrivePicker();
        setLoadState("ready");
        void refreshUsage();
      } catch (err) {
        if (err instanceof ApiRequestError) {
          failLoad(mapApiError(err.status, err.message, err.code));
        } else {
          failLoad("Drive import failed. Please try again.");
        }
      }
    },
    [closeDrivePicker, failLoad, fetchQuality, refreshUsage, resetDerivedState, setSourceFromApiCb],
  );

  const exportData = useCallback(async () => {
    setError("Exports arrive with the React download flow.");
  }, []);

  // Phase 5 — refresh connection status + usage on mount (best-effort; never
  // blocks the UI). Connection state is server-owned; the browser only mirrors it.
  useEffect(() => {
    void refreshConnections();
    void refreshUsage();
  }, [refreshConnections, refreshUsage]);

  const value = useMemo<ExplorerContextValue>(
    () => ({
      loadState,
      source,
      error,
      filters,
      metrics,
      summary,
      summaryState,
      chat,
      chatState,
      streamingId,
      theme,
      quality,
      charts,
      usage,
      previewRows,
      context,
      filename: context?.filename ?? null,
      forecast,
      funnel,
      ga4Connected,
      driveConfigured,
      drivePickerOpen,
      pickerToken,
      loadData,
      failLoad,
      clearError,
      clearData,
      addFilter,
      removeFilter,
      addMetric,
      removeMetric,
      generateSummary,
      sendMessage,
      retryLastTurn,
      cancelStream,
      clearChat,
      setSourceFromApi: setSourceFromApiCb,
      refreshConnections,
      connectGA4,
      handleGA4Callback,
      connectDrive,
      openDrivePicker,
      closeDrivePicker,
      downloadFromDrive,
      fetchQuality,
      fetchCharts,
      fetchForecast,
      fetchFunnel,
      exportData,
      refreshUsage,
      toggleTheme,
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
      chatState,
      streamingId,
      theme,
      quality,
      charts,
      usage,
      previewRows,
      context,
      forecast,
      funnel,
      ga4Connected,
      driveConfigured,
      drivePickerOpen,
      pickerToken,
      loadData,
      failLoad,
      clearError,
      clearData,
      addFilter,
      removeFilter,
      addMetric,
      removeMetric,
      generateSummary,
      sendMessage,
      retryLastTurn,
      cancelStream,
      clearChat,
      setSourceFromApiCb,
      refreshConnections,
      connectGA4,
      handleGA4Callback,
      connectDrive,
      openDrivePicker,
      closeDrivePicker,
      downloadFromDrive,
      fetchQuality,
      fetchCharts,
      fetchForecast,
      fetchFunnel,
      exportData,
      refreshUsage,
      toggleTheme,
    ],
  );

  return <ExplorerContext.Provider value={value}>{children}</ExplorerContext.Provider>;
}

export function useExplorer(): ExplorerContextValue {
  const ctx = useContext(ExplorerContext);
  if (!ctx) throw new Error("useExplorer must be used within ExplorerProvider");
  return ctx;
}
