import { useExplorer } from "@/lib/explorer-store";
import { useIsMobile } from "@/hooks/use-mobile";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { EmptyHero } from "./EmptyHero";
import { ErrorBanner } from "./ErrorBanner";
import { DataPreview } from "./DataPreview";
import { Scorecard } from "./Scorecard";
import { ChartsRow } from "./ChartsRow";
import { ChatPanel } from "./ChatPanel";
import { AiSummary } from "./AiSummary";
import { DrivePickerDialog } from "./DrivePickerDialog";
import { Toaster } from "@/components/ui/sonner";

export function AppShell() {
  const { loadState, source } = useExplorer();
  const isMobile = useIsMobile();
  const hasDataset = loadState === "ready" && source;

  return (
    <div className="flex h-dvh overflow-hidden bg-background text-foreground">
      {!isMobile && <Sidebar className="w-60 shrink-0" />}
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar />
        <main className="min-h-0 flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-7xl p-4 sm:p-6">
            <ErrorBanner />
            {!hasDataset ? (
              <EmptyHero />
            ) : (
              <div className="grid gap-4 lg:grid-cols-5">
                <div className="space-y-4 lg:col-span-3">
                  <Scorecard />
                  <DataPreview />
                  <ChartsRow />
                  <AiSummary />
                </div>
                <div className="min-h-[420px] lg:col-span-2 lg:h-[calc(100dvh-7.5rem)]">
                  <ChatPanel />
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
      <DrivePickerDialog />
      <Toaster />
    </div>
  );
}
