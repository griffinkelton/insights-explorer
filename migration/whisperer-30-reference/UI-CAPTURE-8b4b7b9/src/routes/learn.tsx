import { useMemo, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft, BarChart3, Check, CircleCheck, CircleDot, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { sections, type Challenge } from "@/lib/learn-content";

const title = "Learn — Insights Explorer";
const description =
  "Short interactive lessons on the Insights Explorer data lifecycle, filter behaviour, AI verification, privacy and architecture.";

export const Route = createFileRoute("/learn")({
  head: () => ({
    meta: [
      { title },
      { name: "description", content: description },
      { property: "og:title", content: title },
      { property: "og:description", content: description },
    ],
  }),
  component: LearnPage,
});

function ChallengeCard({
  challenge,
  onSolved,
}: {
  challenge: Challenge;
  onSolved: (id: string) => void;
}) {
  const [choice, setChoice] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const correct = choice === challenge.answer;

  return (
    <div
      className={cn(
        "rounded-md border border-border bg-surface p-4",
        submitted && correct && "border-success/50",
        submitted && !correct && "border-destructive/50",
      )}
    >
      <p className="text-sm font-medium">{challenge.prompt}</p>
      <RadioGroup
        value={choice}
        onValueChange={(v) => {
          setChoice(v);
          setSubmitted(false);
        }}
        className="mt-3 gap-2"
      >
        {challenge.options.map((o) => (
          <div key={o.value} className="flex items-start gap-2.5">
            <RadioGroupItem value={o.value} id={`${challenge.id}-${o.value}`} className="mt-0.5" />
            <Label
              htmlFor={`${challenge.id}-${o.value}`}
              className="text-sm leading-relaxed font-normal text-muted-foreground"
            >
              {o.label}
            </Label>
          </div>
        ))}
      </RadioGroup>

      <div className="mt-4 flex items-center gap-3">
        <Button
          size="sm"
          disabled={!choice}
          onClick={() => {
            setSubmitted(true);
            if (choice === challenge.answer) onSolved(challenge.id);
          }}
        >
          Check answer
        </Button>
        {submitted && (
          <span
            className={cn(
              "flex items-center gap-1.5 text-xs font-medium",
              correct ? "text-success" : "text-destructive",
            )}
          >
            {correct ? <Check className="size-3.5" aria-hidden /> : <X className="size-3.5" aria-hidden />}
            {correct ? "Correct" : "Not quite"}
          </span>
        )}
      </div>

      {submitted && (
        <p
          role="status"
          className={cn(
            "mt-3 rounded-md border p-3 text-xs leading-relaxed",
            correct
              ? "border-success/30 bg-success/5 text-muted-foreground"
              : "border-destructive/30 bg-destructive/5 text-muted-foreground",
          )}
        >
          {challenge.explanation}
        </p>
      )}
    </div>
  );
}

function LearnPage() {
  const [solved, setSolved] = useState<string[]>([]);
  const total = useMemo(() => sections.reduce((n, s) => n + s.challenges.length, 0), []);
  const markSolved = (id: string) => setSolved((s) => (s.includes(id) ? s : [...s, id]));

  const sectionDone = (id: string) => {
    const s = sections.find((x) => x.id === id)!;
    return s.challenges.every((c) => solved.includes(c.id));
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-10 flex h-14 items-center gap-3 border-b border-border bg-background/85 px-4 backdrop-blur md:px-6">
        <Link
          to="/"
          className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="size-4" aria-hidden />
          Back to workspace
        </Link>
        <div className="ml-auto flex items-center gap-2">
          <BarChart3 className="size-4 text-primary" aria-hidden />
          <span className="text-sm font-semibold tracking-tight">Insights Explorer</span>
        </div>
      </header>

      <div className="mx-auto flex max-w-6xl gap-10 px-4 py-10 md:px-6">
        <nav
          aria-label="Section progress"
          className="sticky top-24 hidden h-fit w-56 shrink-0 lg:block"
        >
          <p className="text-[10px] font-semibold tracking-[0.12em] text-muted-foreground uppercase">
            Progress
          </p>
          <p className="num mt-2 text-sm">
            {solved.length}
            <span className="text-muted-foreground"> / {total} challenges</span>
          </p>
          <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-surface-2">
            <div
              className="h-full bg-primary transition-all"
              style={{ width: `${(solved.length / total) * 100}%` }}
            />
          </div>
          <ul className="mt-5 space-y-1">
            {sections.map((s) => (
              <li key={s.id}>
                <a
                  href={`#${s.id}`}
                  className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm text-muted-foreground hover:bg-accent hover:text-foreground"
                >
                  {sectionDone(s.id) ? (
                    <CircleCheck className="size-3.5 shrink-0 text-success" aria-hidden />
                  ) : (
                    <CircleDot className="size-3.5 shrink-0 opacity-50" aria-hidden />
                  )}
                  <span className="truncate">{s.title}</span>
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <main className="min-w-0 flex-1">
          <h1 className="text-3xl font-semibold tracking-tight">Learn the platform</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Five short sections on how data moves through Insights Explorer, and how to tell a
            trustworthy answer from a confident one. Each ends with a check.
          </p>

          <div className="mt-10 space-y-14">
            {sections.map((s) => (
              <section key={s.id} id={s.id} className="scroll-mt-24">
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-semibold tracking-tight">{s.title}</h2>
                  {sectionDone(s.id) && (
                    <span className="flex items-center gap-1 rounded-sm border border-success/40 bg-success/10 px-1.5 py-0.5 text-[11px] text-success">
                      <Check className="size-3" aria-hidden />
                      Complete
                    </span>
                  )}
                </div>
                <p className="mt-1 text-xs tracking-wide text-muted-foreground uppercase">
                  {s.blurb}
                </p>
                <div className="mt-4 space-y-3">
                  {s.body.map((p) => (
                    <p key={p.slice(0, 24)} className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
                      {p}
                    </p>
                  ))}
                </div>
                <div className="mt-6 space-y-3">
                  {s.challenges.map((c) => (
                    <ChallengeCard key={c.id} challenge={c} onSolved={markSolved} />
                  ))}
                </div>
              </section>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}
