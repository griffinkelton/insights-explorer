import { LineChart, MessagesSquare, ShieldCheck, Plug } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useExplorer } from "@/lib/explorer-store";
import { UploadZone } from "./UploadZone";

const features = [
  {
    icon: MessagesSquare,
    title: "Natural language chat",
    body: "Ask questions in plain English and get grounded answers with the numbers attached.",
  },
  {
    icon: LineChart,
    title: "Auto charts",
    body: "Trends, top pages, funnels and forecasts are drawn the moment your data lands.",
  },
  {
    icon: ShieldCheck,
    title: "Privacy-first",
    body: "Analysis runs against de-identified exports. Nothing is retained after you clear data.",
  },
];

export function EmptyHero() {
  const { loadData } = useExplorer();

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col items-center px-4 py-14 text-center">
      <span className="rounded-sm border border-border bg-surface px-2.5 py-1 text-[11px] tracking-wide text-muted-foreground uppercase">
        GA4 workspace
      </span>
      <h1 className="mt-4 text-3xl font-semibold tracking-tight md:text-4xl">
        Explore your analytics by asking
      </h1>
      <p className="mt-3 max-w-xl text-sm text-muted-foreground">
        Load a GA4 export or connect a property, then interrogate the data through charts and
        conversation. No dashboards to configure.
      </p>

      <div className="mt-8 w-full">
        <UploadZone />
      </div>

      <div className="mt-4 flex items-center gap-3">
        <Button onClick={() => loadData("GA4 · property 284910233")} className="gap-2">
          <Plug className="size-4" aria-hidden />
          Connect GA4
        </Button>
        <Button variant="ghost" onClick={() => loadData()} className="text-muted-foreground">
          Load sample dataset
        </Button>
      </div>

      <div className="mt-12 grid w-full gap-3 sm:grid-cols-3">
        {features.map(({ icon: Icon, title, body }) => (
          <div
            key={title}
            className="rounded-md border border-border bg-surface p-4 text-left transition-colors hover:border-primary/40"
          >
            <Icon className="size-4 text-primary" aria-hidden />
            <p className="mt-3 text-sm font-medium">{title}</p>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
