// MSW network handlers (Task 6) — real endpoint shapes (snake_case wire).
import { http, HttpResponse } from "msw";
import {
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
];
