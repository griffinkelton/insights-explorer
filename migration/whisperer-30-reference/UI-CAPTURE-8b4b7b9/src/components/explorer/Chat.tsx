import { useEffect, useRef, useState } from "react";
import { Check, Copy, Download, Paperclip, Send, ThumbsDown, ThumbsUp, Bot } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useExplorer } from "@/lib/explorer-store";
import { SUGGESTED_QUESTIONS } from "@/lib/mock-braintree";
import { Markdown } from "./Markdown";

const COMMANDS = ["/summary", "/equity", "/funnel", "/help", "/clear"];

function MessageActions({ content }: { content: string }) {
  const [copied, setCopied] = useState(false);
  const [vote, setVote] = useState<"up" | "down" | null>(null);

  return (
    <div className="mt-2 flex items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
      <Button
        variant="ghost"
        size="icon"
        aria-label="Copy message"
        className="size-7 text-muted-foreground"
        onClick={() => {
          void navigator.clipboard?.writeText(content);
          setCopied(true);
          window.setTimeout(() => setCopied(false), 1500);
        }}
      >
        {copied ? <Check className="size-3.5 text-success" aria-hidden /> : <Copy className="size-3.5" aria-hidden />}
      </Button>
      <Button
        variant="ghost"
        size="icon"
        aria-label="Helpful response"
        aria-pressed={vote === "up"}
        className={cn("size-7 text-muted-foreground", vote === "up" && "text-success")}
        onClick={() => setVote("up")}
      >
        <ThumbsUp className="size-3.5" aria-hidden />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        aria-label="Unhelpful response"
        aria-pressed={vote === "down"}
        className={cn("size-7 text-muted-foreground", vote === "down" && "text-destructive")}
        onClick={() => setVote("down")}
      >
        <ThumbsDown className="size-3.5" aria-hidden />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        className="h-7 gap-1.5 px-2 text-xs text-muted-foreground"
        onClick={() => toast.success("Message exported", { description: "Mock export — no backend wired." })}
      >
        <Download className="size-3.5" aria-hidden />
        Export this
      </Button>
    </div>
  );
}

export function Chat() {
  const { chat, sendMessage, streamingId, clearChat, generateSummary } = useExplorer();
  const [value, setValue] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [chat]);

  const submit = (text: string) => {
    if (!text.trim()) return;
    if (text.trim() === "/clear") {
      clearChat();
      setValue("");
      return;
    }
    if (text.trim() === "/summary") {
      generateSummary();
      setValue("");
      toast.info("Regenerating dataset summary");
      return;
    }
    sendMessage(text);
    setValue("");
  };

  return (
    <section data-tour="chat" className="flex flex-col rounded-md border border-border bg-surface" aria-label="AI chat">
      <header className="flex items-center gap-2 border-b border-border px-4 py-3">
        <Bot className="size-4 text-primary" aria-hidden />
        <h2 className="text-sm font-medium">Ask the data</h2>
        <span className="ml-auto text-xs text-muted-foreground">AI over the linked dataset</span>
      </header>

      <div ref={scrollRef} className="max-h-[520px] min-h-[320px] flex-1 space-y-5 overflow-y-auto p-4">
        {chat.length === 0 && (
          <div className="flex flex-col items-center gap-3 py-12 text-center">
            <Bot className="size-5 text-muted-foreground" aria-hidden />
            <p className="text-sm text-muted-foreground">
              Ask an equity or funnel question about the linked dataset.
            </p>
            <div className="flex max-w-xl flex-wrap justify-center gap-1.5">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => submit(q)}
                  className="rounded-sm border border-border px-2 py-1 text-left text-xs text-muted-foreground transition-colors hover:border-primary/50 hover:text-primary"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {chat.map((m) =>
          m.role === "user" ? (
            <div key={m.id} className="group flex flex-col items-end">
              <div className="max-w-[80%] rounded-md bg-primary px-3 py-2 text-sm text-primary-foreground">
                {m.content}
              </div>
              <span className="num mt-1 text-[10px] text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100">
                {m.timestamp}
              </span>
            </div>
          ) : (
            <div key={m.id} className="group flex gap-3">
              <div className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-sm border border-border bg-surface-2 text-primary">
                <Bot className="size-3.5" aria-hidden />
              </div>
              <div className="min-w-0 flex-1">
                <div className="rounded-md border border-border bg-surface-2/60 px-3 py-2.5">
                  <Markdown content={m.content} />
                  {streamingId === m.id && (
                    <span className="caret-blink-text ml-0.5 inline-block h-3.5 w-[2px] translate-y-0.5 bg-primary" />
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {streamingId !== m.id && <MessageActions content={m.content} />}
                  <span className="num text-[10px] text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100">
                    {m.timestamp}
                  </span>
                </div>
              </div>
            </div>
          ),
        )}
      </div>

      <div className="border-t border-border p-3">
        <div className="mb-2 flex flex-wrap gap-1.5">
          {COMMANDS.map((c) => (
            <button
              key={c}
              onClick={() => submit(c)}
              className="rounded-sm border border-border px-2 py-0.5 font-mono text-[11px] text-muted-foreground transition-colors hover:border-primary/50 hover:text-primary"
            >
              {c}
            </button>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit(value);
          }}
          className="flex items-end gap-2 rounded-md border border-border bg-background p-2 focus-within:border-primary"
        >
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Attach context"
            className="size-8 shrink-0 text-muted-foreground"
            onClick={() => toast.info("Context attachment is mocked in this build")}
          >
            <Paperclip className="size-4" aria-hidden />
          </Button>
          <textarea
            rows={1}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit(value);
              }
            }}
            placeholder="Ask about sessions, pages, funnels…"
            aria-label="Message"
            className="max-h-32 min-h-8 flex-1 resize-none bg-transparent py-1.5 text-sm outline-none placeholder:text-muted-foreground"
          />
          <Button
            type="submit"
            size="icon"
            aria-label="Send message"
            disabled={!value.trim() || streamingId !== null}
            className="size-8 shrink-0"
          >
            <Send className="size-4" aria-hidden />
          </Button>
        </form>
      </div>
    </section>
  );
}
