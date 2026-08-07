import { useEffect, useRef, useState } from "react";
import { Bot, Loader2, RefreshCw, Send, Square, TriangleAlert, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useExplorer } from "@/lib/explorer-store";
import { Markdown } from "./Markdown";

export function ChatPanel() {
  const { chat, chatState, sendMessage, retryLastTurn, cancelStream, error, loadState } = useExplorer();
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [chat]);

  if (loadState !== "ready") return null;
  const streaming = chatState === "streaming";
  const lastTurnFailed = chatState === "error";

  const submit = () => {
    const text = draft.trim();
    if (!text || streaming) return;
    setDraft("");
    void sendMessage(text);
  };

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Bot className="h-4 w-4 text-muted-foreground" aria-hidden />
          Ask about your data
        </CardTitle>
        {streaming && (
          <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Loader2 className="h-3 w-3 animate-spin" aria-hidden />
            Streaming
          </span>
        )}
      </CardHeader>
      <CardContent className="flex min-h-0 flex-1 flex-col gap-3">
        {error && (
          <div
            role="alert"
            className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive"
          >
            <TriangleAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
            <span>{error}</span>
          </div>
        )}
        <ScrollArea ref={scrollRef} className="min-h-0 flex-1 pr-3">
          <div className="space-y-3">
            {chat.length === 0 && (
              <div className="py-8 text-center">
                <p className="text-sm font-medium text-muted-foreground">Ask a question about your dataset</p>
                <p className="mx-auto mt-1 max-w-xs text-xs text-muted-foreground/80">
                  Try “Summarize the key trends” or “Which metric looks most volatile?”
                </p>
              </div>
            )}
            {chat.map((m, i) => {
              const isUser = m.role === "user";
              return (
                <div key={i} className={`flex gap-2 ${isUser ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`flex max-w-[85%] gap-2 ${
                      isUser ? "flex-row-reverse" : ""
                    }`}
                  >
                    <span
                      className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full ${
                        isUser ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                      }`}
                      aria-hidden
                    >
                      {isUser ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
                    </span>
                    <div
                      className={`rounded-xl px-3 py-2 text-sm ${
                        isUser
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted/60 text-card-foreground"
                      }`}
                    >
                      {isUser ? (
                        <p className="whitespace-pre-wrap">{m.content}</p>
                      ) : m.content ? (
                        <Markdown content={m.content} />
                      ) : (
                        <span className="text-muted-foreground">
                          <Loader2 className="mr-1 inline h-3 w-3 animate-spin" aria-hidden />
                          Thinking…
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
            {lastTurnFailed && (
              <div className="flex items-center justify-center">
                <Button variant="outline" size="sm" onClick={() => void retryLastTurn()}>
                  <RefreshCw className="h-3.5 w-3.5" aria-hidden />
                  Retry
                </Button>
              </div>
            )}
          </div>
        </ScrollArea>
        <div className="flex items-center gap-2">
          <Input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder="Ask about your data…"
            aria-label="Message the AI assistant"
            disabled={streaming}
            maxLength={4000}
          />
          {streaming ? (
            <Button variant="outline" size="icon" onClick={cancelStream} aria-label="Stop generating">
              <Square className="h-4 w-4" aria-hidden />
            </Button>
          ) : (
            <Button size="icon" onClick={submit} disabled={!draft.trim()} aria-label="Send message">
              <Send className="h-4 w-4" aria-hidden />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
