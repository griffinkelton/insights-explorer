import { Fragment, type ReactNode } from "react";
import { cn } from "@/lib/utils";

function inline(text: string, keyBase: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).filter(Boolean);
  return parts.map((p, i) => {
    if (p.startsWith("**") && p.endsWith("**")) {
      return (
        <strong key={`${keyBase}-${i}`} className="font-semibold text-foreground">
          {p.slice(2, -2)}
        </strong>
      );
    }
    if (p.startsWith("`") && p.endsWith("`")) {
      return (
        <code
          key={`${keyBase}-${i}`}
          className="rounded-sm border border-border bg-surface-2 px-1 py-0.5 font-mono text-[0.85em] text-primary"
        >
          {p.slice(1, -1)}
        </code>
      );
    }
    return <Fragment key={`${keyBase}-${i}`}>{p}</Fragment>;
  });
}

/** Minimal markdown renderer: headings, bold, inline code, code blocks, lists, tables. */
export function Markdown({ content, className }: { content: string; className?: string }) {
  const lines = content.split("\n");
  const blocks: ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i]!;

    if (line.startsWith("```")) {
      const buf: string[] = [];
      i++;
      while (i < lines.length && !lines[i]!.startsWith("```")) buf.push(lines[i++]!);
      i++;
      blocks.push(
        <pre
          key={`c${i}`}
          className="overflow-x-auto rounded-md border border-border bg-surface-2 p-3 font-mono text-xs leading-relaxed text-foreground"
        >
          <code>{buf.join("\n")}</code>
        </pre>,
      );
      continue;
    }

    if (/^\|.*\|$/.test(line) && /^\|[\s:|-]+\|$/.test(lines[i + 1] ?? "")) {
      const cells = (l: string) =>
        l.split("|").slice(1, -1).map((c) => c.trim());
      const header = cells(line);
      i += 2;
      const rows: string[][] = [];
      while (i < lines.length && /^\|.*\|$/.test(lines[i]!)) rows.push(cells(lines[i++]!));
      blocks.push(
        <div key={`t${i}`} className="overflow-x-auto rounded-md border border-border">
          <table className="w-full text-sm">
            <thead className="bg-surface-2">
              <tr>
                {header.map((h, hi) => (
                  <th
                    key={hi}
                    className="px-3 py-2 text-left text-xs font-medium tracking-wide text-muted-foreground uppercase"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, ri) => (
                <tr key={ri} className="border-t border-border">
                  {r.map((c, ci) => (
                    <td key={ci} className={cn("px-3 py-2", ci > 0 && "num text-right")}>
                      {inline(c, `${ri}-${ci}`)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }

    const heading = /^(#{1,4})\s+(.*)$/.exec(line);
    if (heading) {
      const level = heading[1]!.length;
      const text = heading[2]!;
      const sizes = ["text-lg", "text-base", "text-sm", "text-sm"];
      blocks.push(
        <p
          key={`h${i}`}
          className={cn("font-semibold tracking-tight text-foreground", sizes[level - 1])}
        >
          {inline(text, `h${i}`)}
        </p>,
      );
      i++;
      continue;
    }

    if (/^\s*([-*]|\d+\.)\s+/.test(line)) {
      const ordered = /^\s*\d+\./.test(line);
      const items: string[] = [];
      while (i < lines.length && /^\s*([-*]|\d+\.)\s+/.test(lines[i]!)) {
        items.push(lines[i++]!.replace(/^\s*([-*]|\d+\.)\s+/, ""));
      }
      const ListTag = ordered ? "ol" : "ul";
      blocks.push(
        <ListTag
          key={`l${i}`}
          className={cn(
            "space-y-1 pl-5 text-sm leading-relaxed text-muted-foreground",
            ordered ? "list-decimal" : "list-disc",
          )}
        >
          {items.map((it, ii) => (
            <li key={ii}>{inline(it, `l${i}-${ii}`)}</li>
          ))}
        </ListTag>,
      );
      continue;
    }

    if (line.trim() === "") {
      i++;
      continue;
    }

    const para: string[] = [];
    while (i < lines.length && lines[i]!.trim() !== "" && !/^([-*#>|`]|\d+\.)/.test(lines[i]!)) {
      para.push(lines[i++]!);
    }
    blocks.push(
      <p key={`p${i}`} className="text-sm leading-relaxed text-muted-foreground">
        {inline(para.join(" "), `p${i}`)}
      </p>,
    );
  }

  return <div className={cn("space-y-3", className)}>{blocks}</div>;
}
