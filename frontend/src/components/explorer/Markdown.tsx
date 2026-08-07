// Tiny dependency-free markdown renderer for AI output. Deliberately minimal:
// paragraphs, headings, bold, italic, inline code, fenced code, and bullet lists.
// Not a full CommonMark implementation — Phase 4 scope.
import { Fragment, type ReactNode } from "react";

function renderInline(text: string): ReactNode[] {
  // Split on **bold**, *italic*, and `code` with a single regex pass.
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code
          key={i}
          className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]"
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    return <Fragment key={i}>{part}</Fragment>;
  });
}

export function Markdown({ content }: { content: string }) {
  const lines = content.split("\n");
  const blocks: ReactNode[] = [];
  let list: string[] = [];
  let code: string[] = [];
  let inCode = false;

  const flushList = (key: string) => {
    if (list.length) {
      blocks.push(
        <ul key={key} className="my-2 list-disc space-y-1 pl-5">
          {list.map((item, i) => (
            <li key={i}>{renderInline(item)}</li>
          ))}
        </ul>,
      );
      list = [];
    }
  };

  for (const line of lines) {
    if (line.trim().startsWith("```")) {
      if (inCode) {
        blocks.push(
          <pre key={`pre-${blocks.length}`} className="my-2 overflow-x-auto rounded-md bg-muted p-3 font-mono text-xs">
            <code>{code.join("\n")}</code>
          </pre>,
        );
        code = [];
        inCode = false;
      } else {
        flushList(`list-${blocks.length}`);
        inCode = true;
      }
      continue;
    }
    if (inCode) {
      code.push(line);
      continue;
    }
    if (/^\s*[-*]\s+/.test(line)) {
      flushList(`list-${blocks.length}`);
      list.push(line.replace(/^\s*[-*]\s+/, ""));
      continue;
    }
    flushList(`list-${blocks.length}`);
    if (/^#{1,3}\s+/.test(line)) {
      const level = line.match(/^(#{1,3})\s+/)?.[1].length ?? 1;
      const text = line.replace(/^#{1,3}\s+/, "");
      const Tag = (level <= 2 ? "h3" : "h4") as "h3" | "h4";
      blocks.push(
        <Tag key={`h-${blocks.length}`} className="mt-3 mb-1 font-semibold">
          {renderInline(text)}
        </Tag>,
      );
    } else if (line.trim() === "") {
      blocks.push(<div key={`sp-${blocks.length}`} className="h-2" />);
    } else {
      blocks.push(
        <p key={`p-${blocks.length}`} className="my-1.5 leading-relaxed">
          {renderInline(line)}
        </p>,
      );
    }
  }
  flushList(`list-${blocks.length}`);
  if (inCode) {
    blocks.push(
      <pre key={`pre-${blocks.length}`} className="my-2 overflow-x-auto rounded-md bg-muted p-3 font-mono text-xs">
        <code>{code.join("\n")}</code>
      </pre>,
    );
  }
  return <div className="text-sm">{blocks}</div>;
}
