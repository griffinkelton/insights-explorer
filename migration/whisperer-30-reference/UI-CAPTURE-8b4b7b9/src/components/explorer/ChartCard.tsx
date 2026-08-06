import { useState, type ReactNode } from "react";
import { Download, Maximize2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

export function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  const [full, setFull] = useState(false);

  return (
    <>
      <section className="flex flex-col rounded-md border border-border bg-surface">
        <header className="flex items-start justify-between gap-3 border-b border-border px-4 py-3">
          <div>
            <h3 className="text-sm font-medium">{title}</h3>
            <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p>
          </div>
          <div className="flex shrink-0 items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              aria-label={`View ${title} fullscreen`}
              onClick={() => setFull(true)}
              className="size-8 text-muted-foreground"
            >
              <Maximize2 className="size-3.5" aria-hidden />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              aria-label={`Download ${title}`}
              onClick={() => toast.success(`${title} downloaded`, { description: "Mock download." })}
              className="size-8 text-muted-foreground"
            >
              <Download className="size-3.5" aria-hidden />
            </Button>
          </div>
        </header>
        <div className="h-64 p-3">{children}</div>
      </section>

      <Dialog open={full} onOpenChange={setFull}>
        <DialogContent className="max-w-5xl">
          <DialogHeader>
            <DialogTitle className="text-base">{title}</DialogTitle>
          </DialogHeader>
          <div className="h-[60vh]">{children}</div>
        </DialogContent>
      </Dialog>
    </>
  );
}
