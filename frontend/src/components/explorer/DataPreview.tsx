import { Table2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useExplorer } from "@/lib/explorer-store";

const MAX_VISIBLE_COLUMNS = 8;

export function DataPreview() {
  const { previewRows, context } = useExplorer();
  if (!previewRows.length || !context) return null;

  const columns = context.columns.slice(0, MAX_VISIBLE_COLUMNS).map((c) => c.name);
  const rowCount = Math.min(previewRows.length, 10);

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Table2 className="h-4 w-4 text-muted-foreground" aria-hidden />
          Data preview
        </CardTitle>
        <span className="text-xs text-muted-foreground">
          {rowCount} of {context.rowCount.toLocaleString()} rows · {context.columns.length} columns
        </span>
      </CardHeader>
      <CardContent>
        <ScrollArea className="max-h-80 rounded-md border">
          <table className="w-full text-left text-xs">
            <thead className="sticky top-0 bg-muted/60 backdrop-blur">
              <tr>
                {columns.map((col) => (
                  <th key={col} scope="col" className="px-3 py-2 font-medium text-muted-foreground">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {previewRows.slice(0, rowCount).map((row, i) => (
                <tr key={i} className="border-t">
                  {columns.map((col) => {
                    const v = row[col];
                    return (
                      <td key={col} className="max-w-[180px] truncate px-3 py-2">
                        {v === null || v === undefined ? (
                          <span className="text-muted-foreground/60">—</span>
                        ) : (
                          String(v)
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </ScrollArea>
        {context.columns.length > MAX_VISIBLE_COLUMNS && (
          <p className="mt-2 text-[11px] text-muted-foreground">
            +{context.columns.length - MAX_VISIBLE_COLUMNS} more columns not shown
          </p>
        )}
      </CardContent>
    </Card>
  );
}
