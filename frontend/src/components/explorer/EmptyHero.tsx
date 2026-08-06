import { BarChart3 } from "lucide-react";
import { UploadZone } from "./UploadZone";

export function EmptyHero() {
  return (
    <section className="mx-auto flex max-w-2xl flex-col items-center gap-6 py-12 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-primary">
        <BarChart3 className="h-8 w-8" aria-hidden />
      </div>
      <div className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">Explore your analytics data</h2>
        <p className="mx-auto max-w-md text-sm text-muted-foreground">
          Upload a CSV, XLSX, or XLS file to inspect the data, see a quality score, and ask
          AI questions about it. Everything is parsed and analyzed server-side.
        </p>
      </div>
      <div className="w-full">
        <UploadZone />
      </div>
    </section>
  );
}
