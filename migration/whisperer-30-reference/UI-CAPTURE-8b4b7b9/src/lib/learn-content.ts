export interface Challenge {
  id: string;
  prompt: string;
  options: { value: string; label: string }[];
  answer: string;
  explanation: string;
}

export interface LearnSection {
  id: string;
  title: string;
  blurb: string;
  body: string[];
  challenges: Challenge[];
}

export const sections: LearnSection[] = [
  {
    id: "lifecycle",
    title: "Data lifecycle",
    blurb: "How an export becomes an answer",
    body: [
      "Data enters through one of three doors: a file upload, a GA4 property connection, or a Drive import. Whichever door it uses, it is normalised into the same tabular shape before anything else happens.",
      "Profiling runs next — row counts, date coverage, column presence and outlier detection produce the quality score you see at the top of the dashboard. Analysis never runs on unprofiled data.",
    ],
    challenges: [
      {
        id: "lc1",
        prompt: "A user uploads a file, then connects a GA4 property. What is the active dataset?",
        options: [
          { value: "a", label: "Both, merged automatically" },
          { value: "b", label: "The GA4 property — the most recent source replaces the previous one" },
          { value: "c", label: "The uploaded file, until it is cleared" },
        ],
        answer: "b",
        explanation:
          "One source is active at a time. Connecting a new source replaces the previous one so results are never silently blended.",
      },
      {
        id: "lc2",
        prompt: "When does the quality score get calculated?",
        options: [
          { value: "a", label: "After profiling, before any analysis" },
          { value: "b", label: "Only when you request a summary" },
          { value: "c", label: "On export" },
        ],
        answer: "a",
        explanation:
          "Profiling runs on load. Every downstream chart and answer assumes the profile already exists.",
      },
    ],
  },
  {
    id: "filters",
    title: "Filter behaviour",
    blurb: "What changes when you remove a chip",
    body: [
      "Filters are additive and conjunctive: every active chip narrows the slice further. Removing a chip widens the slice and recomputes everything that depends on it.",
      "Metrics are separate from filters. A metric chip controls what is measured and how it is aggregated; a filter chip controls which rows are measured at all.",
    ],
    challenges: [
      {
        id: "f1",
        prompt: "You remove the `page: /home` filter. What happens to the AI summary?",
        options: [
          { value: "a", label: "Nothing — summaries are cached per session" },
          { value: "b", label: "It is invalidated and should be regenerated against the wider slice" },
          { value: "c", label: "It updates instantly with no recomputation" },
        ],
        answer: "b",
        explanation:
          "A summary is only valid for the slice it was generated from. Changing filters invalidates it — regenerate before trusting it.",
      },
      {
        id: "f2",
        prompt: "Two filters are active: `device: mobile` and `channel: organic`. Which rows are included?",
        options: [
          { value: "a", label: "Rows matching either condition" },
          { value: "b", label: "Rows matching both conditions" },
          { value: "c", label: "Rows matching the most recently added condition" },
        ],
        answer: "b",
        explanation: "Filters combine with AND. Each additional chip strictly narrows the result set.",
      },
    ],
  },
  {
    id: "verification",
    title: "AI verification",
    blurb: "Trusting a generated answer",
    body: [
      "Every generated claim should be traceable to a number in the loaded dataset. If an answer cites a figure that does not appear in a chart or the preview table, treat it as unverified.",
      "Ask for the same figure two different ways. Consistent answers across different phrasings are a weak but useful signal; inconsistent answers mean the question is under-specified.",
    ],
    challenges: [
      {
        id: "v1",
        prompt: "The assistant reports a metric that does not exist in your columns. What is the correct response?",
        options: [
          { value: "a", label: "Accept it — the model may have inferred it" },
          { value: "b", label: "Reject it and re-ask, scoped to columns that exist" },
          { value: "c", label: "Export it with a caveat" },
        ],
        answer: "b",
        explanation:
          "A metric outside the schema cannot be grounded. Re-ask with explicit column names rather than accepting an inferred figure.",
      },
    ],
  },
  {
    id: "privacy",
    title: "Privacy & safety",
    blurb: "What leaves the workspace",
    body: [
      "Work with de-identified, aggregated exports. Nothing in this interface requires user-level identifiers, and demographic overlays should be joined on a de-identified key.",
      "Free-text fields sourced from the web — campaign names, UTM values, page paths — are untrusted input. They are sanitised before being placed into any model prompt.",
    ],
    challenges: [
      {
        id: "p1",
        prompt: "Why are UTM and campaign strings sanitised before reaching the model?",
        options: [
          { value: "a", label: "To reduce token cost" },
          { value: "b", label: "They are attacker-controllable text and can carry prompt injection" },
          { value: "c", label: "To normalise capitalisation" },
        ],
        answer: "b",
        explanation:
          "Anyone can craft a link with an arbitrary UTM value. Treat those strings as data, never as instructions.",
      },
    ],
  },
  {
    id: "architecture",
    title: "Architecture map",
    blurb: "Where each piece lives",
    body: [
      "This interface is the presentation layer only. Data loading, model calls, GA4 access, Drive import and export generation stay in the Python service behind an API boundary.",
      "That split means the UI can be exercised end to end with mock data — which is exactly what this build does — while the analysis layer evolves independently.",
    ],
    challenges: [
      {
        id: "a1",
        prompt: "Which of these runs in the browser in the shipped architecture?",
        options: [
          { value: "a", label: "Model inference" },
          { value: "b", label: "GA4 API authentication" },
          { value: "c", label: "Chart rendering and interaction state" },
        ],
        answer: "c",
        explanation:
          "The browser owns presentation and interaction. Credentials and model calls stay server-side.",
      },
    ],
  },
];
