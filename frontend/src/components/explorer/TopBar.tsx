import { Activity, Moon, Sun } from "lucide-react";
import { useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useExplorer } from "@/lib/explorer-store";

export function TopBar() {
  const { theme, toggleTheme, usage, refreshUsage } = useExplorer();
  const hydrated = useRef(false);

  useEffect(() => {
    if (hydrated.current) return;
    hydrated.current = true;
    void refreshUsage();
  }, [refreshUsage]);

  return (
    <header className="flex h-14 items-center justify-between border-b bg-card px-4">
      <div className="flex items-center gap-3">
        <h1 className="text-sm font-semibold">Workspace</h1>
        {usage && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="h-7 gap-1.5 px-2 text-xs"
                aria-label={`AI usage — ${usage.requestCount} requests`}
              >
                <Activity className="h-3.5 w-3.5 text-muted-foreground" aria-hidden />
                {usage.requestCount} req
                <span className="text-muted-foreground">
                  · {usage.failureCount} fail
                </span>
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              {usage.requestCount} AI requests · {usage.failureCount} failures ·{" "}
              {usage.totalTokens.toLocaleString()} tokens total (this session)
            </TooltipContent>
          </Tooltip>
        )}
      </div>
      <Button
        variant="ghost"
        size="icon"
        onClick={toggleTheme}
        aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
      >
        {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </Button>
    </header>
  );
}
