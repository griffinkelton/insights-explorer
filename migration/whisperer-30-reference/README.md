<!-- CAPTURED REFERENCE (2026-08-05) — source: griffinkelton/insights-whisperer-30 @ a71c3712cb5228b477a9147770aac36faa70cb2c.
Reference only — do not edit. Original content below verbatim.
See migration/whisperer-30-reference/WHISPERER-30-REFERENCE.md for why this file was captured. -->

# Insight Navigator

I'm building something I call Insights Explorer. I have a repo already built for it. Connections to GA4, Drive, free Gemini tiers, and Playwright to scrape content from another site the client privately hosts demographic data overlayed with website data.

Lovable Mega Prompt

Copy and paste this entire prompt into Lovable:

Project: GA4 Insight Explorer — a Google Analytics 4 data analysis tool that lets users upload or live-connect GA4 data and explore it through natural language AI chat.

What I need: Redesign the frontend UI from scratch as a modern, polished React web app. The current version is built in Python/Streamlit and I want to replace only the UI layer — the backend logic (data loading, Gemini AI calls, GA4 API, Drive import, exports) stays in Python. Think of this as building the ideal UI shell that would eventually connect to that Python backend via API.

Design Direction: Dark-first analytics dashboard. Think Linear, Vercel Dashboard, or Notion — clean, minimal, high-information-density. Not a colorful BI tool. Calm, confident, pro-grade. Use a dark neutral base (#0D0D0F or similar), subtle surface layers, and a single accent color (electric blue #3B82F6 or indigo #6366F1). Sharp corners or very subtle radius (4–6px max). No drop shadows everywhere — use borders and surface elevation instead.

Typography: Inter or Geist. Tight letter-spacing on headings. Muted secondary text (#6B7280). Clear visual hierarchy between heading, subheading, data label, and body.

Layout & Structure

Build a two-panel layout:

Left sidebar (240px, collapsible):

App logo/name at top — "Insights Explorer" with a small chart icon

Data source section: Upload CSV/XLSX button (drag & drop zone on hover), "Connect GA4" OAuth button, "Import from Drive" button

Active data state: show filename, row count, and date range when data is loaded

Filters section: date range picker, dimension filters (shown as tag chips that can be removed)

Active metrics list with a small + button to add custom metrics

Bottom: "Clear Data" button (destructive, subtle red — not alarming)

Sidebar collapses to icon rail on mobile

Main content area:

Top bar: breadcrumb showing current data source name + row count, theme toggle (dark/light), keyboard shortcut hint area (reserved but empty for now)

Hero state (no data loaded): Large centered empty state with upload drop zone, a "Connect GA4" CTA, and 3 feature cards (Natural Language Chat, Auto Charts, Privacy-First)

Data loaded state: Switch to dashboard layout

Dashboard Layout (data loaded)

Use a responsive grid with these sections:

1. Data Quality Scorecard — compact horizontal strip at top. Show: Row Count, Date Range, Missing Columns (as warning chips), Quality Score (0–100 as a progress bar or donut).

2. AI Summary Card — below scorecard. Shows the one-click AI-generated summary. Has a "Generate Summary" button if not yet generated. When generating: streaming skeleton animation. When complete: rendered markdown text in a card with a subtle left border accent.

3. Charts Row — 2-column grid of Plotly-style charts (line chart for sessions/users over time, bar chart for top pages). Each chart card has: title, subtitle, fullscreen icon, download icon. Charts use dark theme with the accent color.

4. Forecast & Funnel Row — optional, shown only when available. Same card treatment.

5. Chat Interface — full-width card at bottom (or right panel on wide screens). Chat history scrolls. User messages right-aligned in accent-colored bubble. AI responses left-aligned in a surface card. Streaming responses show a blinking cursor. Below the chat: command pill buttons (/summary, /top, /help, /clear) rendered as small ghost-button chips. Chat input at bottom with send button and a paperclip icon for context.

Key Components to Build

Upload Zone:

Large dashed border on hover, accent-colored

Accepts .csv, .xlsx

Shows file validation state: green check / red error with message

Drag-over state: accent border + subtle background fill

Data Preview Table:

Compact, monospace numbers, sortable headers

First 10 rows visible, "Show more" expander

Column type icons (date, number, string)

Filter Tags:

Horizontal scrolling row of chips: date: Jan–Mar 2024 ✕, page: /home ✕

Add filter: small + Filter ghost button

Metric Tags:

Same chip style but with a different accent: show metric name + aggregation type

Chat Message:

Markdown-rendered AI responses (bold, headers, lists, code blocks with syntax highlight)

Each AI message has: copy button, thumbs up/down, "Export this" button

Timestamps on hover

Export Menu:

Triggered by a top-right "Export" button

Dropdown: Download Markdown, Download Excel, Download PDF, Export to Google Sheets

Learn Page (/learn):

Clean educational layout — not a documentation dump

Progress indicator sidebar on left showing section completion

Interactive challenges rendered as cards: question prompt, radio/select inputs, submit button, immediate feedback state (correct/incorrect with explanation)

Sections: Data Lifecycle, Filter Behavior, AI Verification, Privacy & Safety, Architecture Map

Onboarding Tour:

Triggered on first load via localStorage

Modal overlay style (not inline) — step counter 1 of 5, back/next/skip, centered card with icon + title + body

"Replay Tour" as a subtle link in the sidebar footer

States to Design

Every major component needs these states built:

StateTreatmentLoadingSkeleton shimmer in surface colorEmptyCentered icon + muted messageErrorRed border card, error message, retry buttonSuccessBrief green flash then settled stateStreaming (AI)Blinking cursor at text end

Accessibility

All interactive elements keyboard accessible

Focus rings using outline: 2px solid var(--accent) with 2px offset — never removed

Color is never the sole indicator of state (always pair with icon or text)

aria-label on icon-only buttons

role="status" on loading indicators

Responsive Behavior

≥1280px: Two-panel layout, sidebar visible, charts 2-col

768–1279px: Sidebar collapses, hamburger toggle

<768px: Single column, sidebar as drawer, charts full-width

Tech Stack for this Build

React 18 + TypeScript

Tailwind CSS with a custom design token config

Shadcn/ui as base component library (customize heavily — do not use defaults as-is)

Recharts or Nivo for chart components (data is mocked for now)

React Router for / and /learn routes

Framer Motion for micro-animations (loading states, transitions, streaming text)

lucide-react for icons

Mock Data

Since the Python backend isn't wired up yet, populate the UI with realistic mock GA4 data:

90-day date range, ~15,000 rows implied

Pages: /home, /blog/ga4-guide, /pricing, /docs, /signup

Metrics: sessions, users, engagement_rate, bounce_rate

Show a plausible AI summary and 3 chat exchange examples already in the thread

What to NOT build

No actual Gemini API calls

No real OAuth flow

No Python/Streamlit integration

No backend — just the UI with mock data and realistic loading/streaming simulations

Deliverable

A fully interactive, production-quality React app that demonstrates the complete UI for all the above features. Every component should be in its final visual state — not wireframe, not placeholder. This should feel like a real, shippable product.

This gives Lovable everything it needs: clear architecture, design system direction, component specs, states, mock data scope, and explicit exclusions so it doesn't go off-rails into backend territory. The </learn> page spec in particular maps directly to the interactive challenge system you've built, so it should port conceptually well into a React layout even if the logic is mocked.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/2ead2139-9b1c-4aad-82b8-483f168a415e).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
