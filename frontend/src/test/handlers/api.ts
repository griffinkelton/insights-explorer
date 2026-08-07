// MSW network handlers (Task 6) — real endpoint shapes (snake_case wire).
import { http, HttpResponse } from "msw";
import {
  sampleDriveDownloadWire,
  sampleGa4PullWire,
  samplePreviewWire,
  sampleQualityWire,
  sampleUploadWire,
  sampleUsageWire,
} from "../fixtures/sample";

export const handlers = [
  http.post("/api/v1/upload", () => HttpResponse.json(sampleUploadWire, { status: 201 })),

  http.get("/api/v1/data/context", () => HttpResponse.json(sampleUploadWire.dataset)),

  http.get("/api/v1/data/preview", () => HttpResponse.json(samplePreviewWire)),

  http.get("/api/v1/data/quality", () => HttpResponse.json(sampleQualityWire)),

  http.post("/api/v1/data/clear", () => HttpResponse.json({ status: "cleared" })),

  http.get("/api/v1/ai/usage", () => HttpResponse.json(sampleUsageWire)),

  http.post("/api/v1/analysis/summary", () =>
    HttpResponse.json({
      summary: "Sessions grew steadily across the period with organic as the top channel.",
      model: "gemini-2.5-flash",
      usage: { input_tokens: 300, output_tokens: 40, thoughts_token_count: 0, total_token_count: 340 },
    }),
  ),

  http.post("/api/v1/analysis/forecast", () =>
    HttpResponse.json({
      metric_col: "sessions",
      periods: 30,
      summary: "Projected upward trend of ~3% per period.",
      forecast_points: [
        { date: "2026-06-01", value: 148, lower: 138, upper: 158 },
        { date: "2026-06-02", value: 152, lower: 140, upper: 164 },
      ],
      insufficient_data: false,
    }),
  ),

  http.post("/api/v1/analysis/funnel", () =>
    HttpResponse.json({ steps: ["home", "product", "checkout"], values: [1000, 420, 118] }),
  ),

  // ── Phase 5 — GA4 + Drive (Task 6 MSW) ──────────────────────────────────
  http.get("/api/v1/ga4/status", () => HttpResponse.json({ connected: false })),

  http.post("/api/v1/ga4/connect", () =>
    HttpResponse.json({
      authorization_url:
        "https://accounts.google.com/o/oauth2/auth?client_id=test&state=msw-state&code_challenge=x&code_challenge_method=S256",
    }),
  ),

  http.post("/api/v1/ga4/pull", () => HttpResponse.json(sampleGa4PullWire)),

  http.get("/api/v1/drive/status", () => HttpResponse.json({ configured: false })),

  http.post("/api/v1/drive/picker-token", () =>
    HttpResponse.json({
      access_token: "test-access-token",
      expires_at: "2026-08-06T12:05:00Z",
      app_id: "123456789012",
      request_id: "msw-request-1",
    }),
  ),

  http.post("/api/v1/drive/download", () => HttpResponse.json(sampleDriveDownloadWire, { status: 201 })),
];
