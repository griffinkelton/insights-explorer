import { useEffect, useState } from "react";
import {
  BookOpenCheck,
  CheckCircle2,
  ExternalLink,
  Loader2,
  Lock,
  Search,
  TriangleAlert,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { ResearchResult, SourceStatus } from "@/lib/research/types";
import { Markdown } from "./Markdown";

type Phase = "idle" | "loading" | "ready" | "error";

interface StatusPayload {
  statuses: SourceStatus[];
  model: string;
  aiConfigured: boolean;
}

function StatusPill({ s }: { s: SourceStatus }) {
  const tone =
    s.state === "ready"
      ? "border-success/40 text-success"
      : s.state === "permission"
        ? "border-warning/40 text-warning"
        : s.state === "error"
          ? "border-destructive/40 text-destructive"
          : "border-border text-muted-foreground";
  const Icon = s.state === "ready" ? CheckCircle2 : s.state === "permission" ? Lock : TriangleAlert;
  return (
    <span
      title={s.setupHint ?? s.detail}
      className={cn("flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs", tone)}
    >
      <Icon className="size-3.5 shrink-0" aria-hidden />
      {s.label}: {s.detail}
    </span>
  );
}

export function ResearchPanel() {
  const [question, setQuestion] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [result, setResult] = useState<ResearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [meta, setMeta] = useState<StatusPayload | null>(null);

  useEffect(() => {
    fetch("/api/research")
      .then((r) => r.json() as Promise<StatusPayload>)
      .then(setMeta)
      .catch(() => setMeta(null));
  }, []);

  const run = async () => {
    const q = question.trim();
    if (!q) return;
    setPhase("loading");
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      const data = (await res.json()) as {
        result?: ResearchResult;
        statuses?: SourceStatus[];
        error?: string;
      };
      if (data.statuses && meta) setMeta({ ...meta, statuses: data.statuses });
      if (!res.ok || !data.result) {
        setError(data.error ?? "The research request failed.");
        setPhase("error");
        return;
      }
      setResult(data.result);
      setPhase("ready");
    } catch {
      setError("Could not reach the research service.");
      setPhase("error");
    }
  };

  const blocked = meta && !meta.aiConfigured;
  const needsSetup = (meta?.statuses ?? []).filter((s) => s.state !== "ready");

  return (
    <section
      data-tour="research"
      aria-label="Research"
      className="rounded-md border border-border bg-surface"
    >
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <BookOpenCheck className="size-4 text-primary" aria-hidden />
          <h2 className="text-sm font-medium">Research</h2>
          <span className="text-xs text-muted-foreground">
            GA4 + Drive, reasoned over by {meta?.model ?? "Lovable AI"}
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {meta ? (
            meta.statuses.map((s) => <StatusPill key={s.id} s={s} />)
          ) : (
            <Skeleton className="h-6 w-40" />
          )}
        </div>
      </header>

      <div className="space-y-4 p-4">
        {blocked && (
          <div className="rounded-md border border-warning/40 bg-warning/5 p-3 text-sm">
            Lovable AI is not enabled. Enable the Lovable AI integration in Lovable settings to run
            research.
          </div>
        )}

        {needsSetup.length > 0 && (
          <div className="rounded-md border border-border bg-background/40 p-3 text-xs text-muted-foreground">
            <p className="mb-1 font-medium text-foreground">Setup needed</p>
            <ul className="list-disc space-y-1 pl-4">
              {needsSetup.map((s) => (
                <li key={s.id}>
                  <span className="text-foreground">{s.label}</span> — {s.setupHint ?? s.detail}
                </li>
              ))}
            </ul>
          </div>
        )}

        <form
          className="flex flex-col gap-2 sm:flex-row"
          onSubmit={(e) => {
            e.preventDefault();
            void run();
          }}
        >
          <Input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a research question across GA4 and Drive…"
            aria-label="Research question"
          />
          <Button type="submit" disabled={phase === "loading" || !question.trim()} className="gap-1.5">
            {phase === "loading" ? (
              <Loader2 className="size-3.5 animate-spin" aria-hidden />
            ) : (
              <Search className="size-3.5" aria-hidden />
            )}
            Research
          </Button>
        </form>

        {phase === "idle" && (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No research run yet — ask a question to combine GA4 metrics with your Drive documents.
          </p>
        )}

        {phase === "loading" && (
          <div className="space-y-2" role="status" aria-label="Running research">
            <Skeleton className="h-4 w-2/5" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-4/5" />
          </div>
        )}

        {phase === "error" && error && (
          <div className="rounded-md border border-destructive bg-destructive/5 p-4">
            <p className="flex items-center gap-2 text-sm font-medium text-destructive">
              <TriangleAlert className="size-4" aria-hidden />
              {error}
            </p>
            <Button size="sm" variant="outline" className="mt-3" onClick={() => void run()}>
              Retry
            </Button>
          </div>
        )}

        {phase === "ready" && result && (
          <div className="space-y-4">
            <div className="border-l-2 border-primary pl-4">
              <Markdown content={result.summary} />
            </div>

            {result.evidence.length > 0 && (
              <div>
                <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Evidence
                </h3>
                <ul className="space-y-1.5">
                  {result.evidence.map((e, i) => (
                    <li key={i} className="text-sm">
                      <span className="mr-2 rounded bg-primary/10 px-1.5 py-0.5 text-xs text-primary">
                        {e.source}
                      </span>
                      {e.fact}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {result.sources.length > 0 && (
              <div>
                <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Sources
                </h3>
                <ul className="space-y-1">
                  {result.sources.map((s, i) => (
                    <li key={i}>
                      <a
                        href={s.url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
                      >
                        <ExternalLink className="size-3.5" aria-hidden />
                        {s.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {result.nextSteps.length > 0 && (
              <div>
                <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Recommended next steps
                </h3>
                <ol className="list-decimal space-y-1 pl-5 text-sm">
                  {result.nextSteps.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}