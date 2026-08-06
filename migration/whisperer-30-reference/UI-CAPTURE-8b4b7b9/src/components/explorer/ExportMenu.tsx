import { Download, FileSpreadsheet, FileText, Sheet, Share2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const items = [
  { label: "Download Markdown", icon: FileText },
  { label: "Download Excel", icon: FileSpreadsheet },
  { label: "Download PDF", icon: Download },
  { label: "Export to Google Sheets", icon: Sheet },
];

export function ExportMenu({ disabled }: { disabled?: boolean }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" disabled={disabled} className="gap-1.5">
          <Share2 className="size-3.5" aria-hidden />
          Export
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="text-xs text-muted-foreground">
          Export current view
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {items.map(({ label, icon: Icon }) => (
          <DropdownMenuItem
            key={label}
            onSelect={() => toast.success(`${label} started`, { description: "Mock export — no backend wired." })}
          >
            <Icon className="size-4 text-muted-foreground" aria-hidden />
            {label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
