<!-- CAPTURED REFERENCE (2026-08-05) — source: griffinkelton/insights-whisperer-30 @ a71c3712cb5228b477a9147770aac36faa70cb2c.
Reference only — do not edit. Original content below verbatim.
See migration/whisperer-30-reference/WHISPERER-30-REFERENCE.md for why this file was captured. -->

# Insights Explorer — UI Shell

A dark-first, production-quality analytics UI for GA4 exploration. Frontend only, driven by realistic mock data with simulated loading/streaming. No Gemini calls, no OAuth, no backend.

## Design system

- Dark base `#0D0D0F`, layered surfaces, single accent `#3B82F6`; light theme as a secondary mode via a top-bar toggle.
- Radius capped at 6px, borders over shadows, Inter/Geist typography with tight heading tracking and muted `#6B7280` secondary text.
- All values become semantic tokens in `src/styles.css` (oklch); components use tokens only — no hardcoded colors.

## Pages

**`/` — Explorer**
- Left sidebar (240px, collapsible to an icon rail; drawer under 768px): logo + chart mark, data source actions (Upload CSV/XLSX with drag-drop, Connect GA4, Import from Drive), active data state (filename, row count, date range), filters section with removable chips + date range picker, active metrics list with `+`, footer with Replay Tour link and a subtle destructive Clear Data button.
- Top bar: breadcrumb (source name + row count), Export dropdown (Markdown, Excel, PDF, Google Sheets), theme toggle, reserved shortcut-hint slot.
- Empty hero state: centered upload drop zone, Connect GA4 CTA, three feature cards (Natural Language Chat, Auto Charts, Privacy-First).
- Loaded dashboard: data quality scorecard strip (rows, date range, missing-column warning chips, 0–100 score), AI Summary card with Generate button → streaming skeleton → markdown with accent left border, two-column Recharts row (sessions/users line, top pages bar) with fullscreen + download icons, optional forecast/funnel row, data preview table (first 10 rows, sortable, monospace numbers, column-type icons, Show more), and the chat surface.
- Chat: scrolling history, right-aligned accent user bubbles, left-aligned surface AI cards with markdown rendering, blinking-cursor streaming, per-message copy / thumbs / Export this, hover timestamps, command pill chips (`/summary`, `/top`, `/help`, `/clear`), input with send + paperclip. Seeded with three example exchanges.

**`/learn`**
- Progress sidebar showing section completion; sections: Data Lifecycle, Filter Behavior, AI Verification, Privacy & Safety, Architecture Map.
- Each section renders interactive challenge cards: prompt, radio/select inputs, submit, immediate correct/incorrect feedback with explanation.

**Onboarding tour**
- First-load modal overlay (localStorage flag), 5 steps with counter, back/next/skip, icon + title + body.

## States & accessibility

Every major component ships loading (skeleton shimmer), empty (icon + muted message), error (red-bordered card + retry), success (brief green flash), and AI streaming states. Focus rings are 2px accent with 2px offset and never removed; state is never color-only; icon buttons get `aria-label`; loaders get `role="status"`.

## Mock data

90-day range, ~15,000 implied rows across `/home`, `/blog/ga4-guide`, `/pricing`, `/docs`, `/signup`; metrics sessions, users, engagement_rate, bounce_rate; plausible AI summary text and seeded chat thread. All in `src/lib/mock-ga4.ts`, shaped so a real API can drop in later.

## Technical notes

- Stack is React 19 + TypeScript + Tailwind v4 + shadcn/ui (heavily customized) + Recharts + lucide-react, already in the project.
- Routing uses TanStack Router (this template's router) rather than React Router: `src/routes/index.tsx` becomes the explorer, `src/routes/learn.tsx` the learn page, shared chrome in `__root.tsx`. Each route gets its own head() metadata.
- Micro-animations use Tailwind/tw-animate-css keyframes; Framer Motion added only if a transition genuinely needs it.
- State (data loaded, filters, chat, tour) lives in a client-side context provider so wiring a Python API later is a single swap of the data source functions.
