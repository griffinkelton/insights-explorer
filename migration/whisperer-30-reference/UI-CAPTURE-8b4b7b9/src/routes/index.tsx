import { useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Loader2 } from "lucide-react";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { ExplorerProvider, useExplorer, useTheme } from "@/lib/explorer-store";
import { SidebarContent } from "@/components/explorer/Sidebar";
import { TopBar } from "@/components/explorer/TopBar";
import { EmptyHero } from "@/components/explorer/EmptyHero";
import { Scorecard } from "@/components/explorer/Scorecard";
import { AiSummary } from "@/components/explorer/AiSummary";
import { ResearchPanel } from "@/components/explorer/ResearchPanel";
import { EvidenceConnectorPanel } from "@/components/explorer/EvidenceConnectorPanel";
import { InsightCandidates } from "@/components/explorer/InsightCandidates";
import { MeasurementContractPanel } from "@/components/explorer/MeasurementContractPanel";
import { EquityPanel } from "@/components/explorer/EquityPanel";
import { ChartsRow, ForecastFunnelRow } from "@/components/explorer/ChartsRow";
import { DataPreview } from "@/components/explorer/DataPreview";
import { Chat } from "@/components/explorer/Chat";
import { OnboardingTour } from "@/components/explorer/OnboardingTour";

const title = "Insights Explorer — GA4 analysis through conversation";
const description =
  "A dark-first GA4 workspace: load an export, read auto-generated charts and quality checks, then interrogate the data in natural language.";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title },
      { name: "description", content: description },
      { property: "og:title", content: title },
      { property: "og:description", content: description },
    ],
  }),
  component: () => (
    <ExplorerProvider>
      <ExplorerPage />
    </ExplorerProvider>
  ),
});

function DashboardSkeleton() {
  return (
    <div className="space-y-4" role="status" aria-label="Loading dashboard">
      <Skeleton className="h-24 w-full" />
      <Skeleton className="h-40 w-full" />
      <div className="grid gap-4 xl:grid-cols-2">
        <Skeleton className="h-72 w-full" />
        <Skeleton className="h-72 w-full" />
      </div>
    </div>
  );
}

function ExplorerPage() {
  const { loadState } = useExplorer();
  const { theme, toggle } = useTheme();
  const [collapsed, setCollapsed] = useState(false);
  const [drawer, setDrawer] = useState(false);
  const [tour, setTour] = useState(false);

  useEffect(() => {
    if (!window.localStorage.getItem("ie-tour-seen")) setTour(true);
  }, []);

  const closeTour = () => {
    window.localStorage.setItem("ie-tour-seen", "1");
    setTour(false);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <aside
        className={`hidden shrink-0 lg:block ${collapsed ? "w-14" : "w-60"}`}
        aria-label="Workspace sidebar"
      >
        <SidebarContent
          collapsed={collapsed}
          onToggle={() => setCollapsed((c) => !c)}
          onReplayTour={() => setTour(true)}
        />
      </aside>

      <Sheet open={drawer} onOpenChange={setDrawer}>
        <SheetContent side="left" className="w-72 p-0">
          <SheetTitle className="sr-only">Workspace navigation</SheetTitle>
          <SidebarContent
            collapsed={false}
            onToggle={() => setDrawer(false)}
            onReplayTour={() => {
              setDrawer(false);
              setTour(true);
            }}
          />
        </SheetContent>
      </Sheet>

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar theme={theme} onToggleTheme={toggle} onOpenSidebar={() => setDrawer(true)} />
        <main className="flex-1 overflow-y-auto">
          {loadState === "ready" ? (
            <div className="mx-auto max-w-[1400px] space-y-4 p-4 md:p-6">
              <Scorecard />
              <AiSummary />
              <EvidenceConnectorPanel />
              <InsightCandidates />
              <ResearchPanel />
              <MeasurementContractPanel />
              <EquityPanel />
              <ChartsRow />
              <ForecastFunnelRow />
              <DataPreview />
              <Chat />
            </div>
          ) : loadState === "loading" ? (
            <div className="mx-auto max-w-[1400px] p-4 md:p-6">
              <p className="mb-4 flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" aria-hidden />
                Parsing and profiling your dataset…
              </p>
              <DashboardSkeleton />
            </div>
          ) : (
            <EmptyHero />
          )}
        </main>
      </div>

      <OnboardingTour open={tour} onClose={closeTour} />
    </div>
  );
}
