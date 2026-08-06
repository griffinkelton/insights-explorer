import { Command, Menu, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useExplorer } from "@/lib/explorer-store";
import { ExportMenu } from "./ExportMenu";

export function TopBar({
  theme,
  onToggleTheme,
  onOpenSidebar,
}: {
  theme: "dark" | "light";
  onToggleTheme: () => void;
  onOpenSidebar: () => void;
}) {
  const { source } = useExplorer();

  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-border bg-background/80 px-3 backdrop-blur md:px-5">
      <Button
        variant="ghost"
        size="icon"
        aria-label="Open navigation"
        onClick={onOpenSidebar}
        className="size-9 lg:hidden"
      >
        <Menu className="size-4" aria-hidden />
      </Button>

      <nav aria-label="Breadcrumb" className="min-w-0 flex-1">
        <ol className="flex items-center gap-2 text-sm">
          <li className="text-muted-foreground">Workspace</li>
          <li className="text-muted-foreground" aria-hidden>
            /
          </li>
          <li className="min-w-0 truncate font-medium text-foreground">
            {source ? source.name : "No data source"}
          </li>
          {source && (
            <li className="hidden shrink-0 items-center gap-2 sm:flex">
              <Separator orientation="vertical" className="h-4" />
              <span className="num text-xs text-muted-foreground">
                {source.rowCount.toLocaleString()} rows
              </span>
            </li>
          )}
        </ol>
      </nav>

      <div
        aria-hidden
        className="hidden items-center gap-1 rounded-md border border-border px-2 py-1 text-[11px] text-muted-foreground xl:flex"
      >
        <Command className="size-3" />
        <span className="num">K</span>
      </div>

      <ExportMenu disabled={!source} />

      <Button
        variant="ghost"
        size="icon"
        aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
        onClick={onToggleTheme}
        className="size-9 text-muted-foreground"
      >
        {theme === "dark" ? <Sun className="size-4" aria-hidden /> : <Moon className="size-4" aria-hidden />}
      </Button>
    </header>
  );
}
