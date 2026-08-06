import { useState } from "react";
import { BarChart3, Bot, Filter, ShieldCheck, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";

const STEPS = [
  {
    icon: Upload,
    title: "Bring your data in",
    body: "Upload a CSV or XLSX export, connect a GA4 property, or pull a file from Drive. Everything downstream reacts to the active source.",
  },
  {
    icon: Filter,
    title: "Shape the question",
    body: "Filters and metrics live in the sidebar as chips. Remove one and every chart, summary and answer recomputes against the new slice.",
  },
  {
    icon: BarChart3,
    title: "Read the dashboard",
    body: "Quality scorecard first, then trends, top pages, forecast and funnel. Each card can go fullscreen or be downloaded.",
  },
  {
    icon: Bot,
    title: "Ask follow-up questions",
    body: "The chat is grounded in the loaded dataset. Use the command pills for shortcuts, and export any single answer.",
  },
  {
    icon: ShieldCheck,
    title: "Clear when you're done",
    body: "Clear Data drops the session entirely. Nothing persists between visits beyond your theme preference.",
  },
];

export function OnboardingTour({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [step, setStep] = useState(0);
  const current = STEPS[step]!;
  const Icon = current.icon;

  const close = () => {
    setStep(0);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && close()}>
      <DialogContent className="max-w-md">
        <div className="grid size-10 place-items-center rounded-md bg-primary/15 text-primary">
          <Icon className="size-5" aria-hidden />
        </div>
        <DialogTitle className="text-lg tracking-tight">{current.title}</DialogTitle>
        <DialogDescription className="text-sm leading-relaxed">{current.body}</DialogDescription>

        <div className="mt-2 flex items-center gap-1.5" aria-hidden>
          {STEPS.map((s, i) => (
            <span
              key={s.title}
              className={`h-1 flex-1 rounded-full ${i <= step ? "bg-primary" : "bg-surface-2"}`}
            />
          ))}
        </div>

        <div className="mt-3 flex items-center justify-between">
          <span className="num text-xs text-muted-foreground">
            {step + 1} of {STEPS.length}
          </span>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={close} className="text-muted-foreground">
              Skip
            </Button>
            {step > 0 && (
              <Button variant="outline" size="sm" onClick={() => setStep((s) => s - 1)}>
                Back
              </Button>
            )}
            <Button
              size="sm"
              onClick={() => (step === STEPS.length - 1 ? close() : setStep((s) => s + 1))}
            >
              {step === STEPS.length - 1 ? "Get started" : "Next"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
