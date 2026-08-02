import {
  Streamlit,
  type RenderData,
} from "streamlit-component-lib";

// ── Types ────────────────────────────────────────────────────────────

type Args = {
  oauthToken: string;
  developerKey: string;
  appId: string;
  appOrigin: string;
  requestId: string;
  theme: string; // "dark" | "light"
};

// ── Declare global gapi / google.picker ──────────────────────────────

declare global {
  interface Window {
    gapi?: {
      load: (name: string, options: { callback: () => void }) => void;
    };
    google?: typeof google;
  }
}

// ── State ────────────────────────────────────────────────────────────

let currentArgs: Args | null = null;
let pickerReady = false;
let pickerLibraryLoading = false;
let eventSentForRequestId: string | null = null;
// ── DOM ──────────────────────────────────────────────────────────────

const button = document.querySelector<HTMLButtonElement>("#open-picker")!;
const statusEl = document.querySelector<HTMLElement>("#status")!;

function setStatus(message: string, kind: "info" | "success" | "error" = "info"): void {
  statusEl.textContent = message;
  statusEl.className = kind;
  Streamlit.setFrameHeight();
}

function setButtonLabel(text: string): void {
  button.textContent = text;
}

// ── Return channel (sanitized) ───────────────────────────────────────

function emit(value: Record<string, unknown>): void {
  Streamlit.setComponentValue(value);
  Streamlit.setFrameHeight();
}

// ── Picker callback ──────────────────────────────────────────────────

function onPickerCallback(data: google.picker.ResponseObject): void {
  if (!currentArgs) return;

  if (data.action === google.picker.Action.PICKED) {
    if (eventSentForRequestId === currentArgs.requestId) return;

    const doc = data.docs?.[0];
    if (!doc?.id) {
      setStatus("No file selected.", "error");
      return;
    }

    eventSentForRequestId = currentArgs.requestId;
    emit({
      kind: "picked",
      requestId: currentArgs.requestId,
      fileId: doc.id,
    });
    button.disabled = false;
    setButtonLabel("✔ Imported — Open Another File");
    setStatus(`✓ ${doc.name} selected`, "success");
    return;
  }

  if (data.action === google.picker.Action.CANCEL) {
    setButtonLabel("Open Google Drive Picker");
    setStatus("Picker closed — no file selected.");
  }
}

// ── Open Picker ──────────────────────────────────────────────────────

function openPicker(): void {
  if (!currentArgs || !pickerReady) {
    setStatus("Picker is unavailable.", "error");
    return;
  }

  try {
    const mimeTypes = [
      "application/vnd.google-apps.spreadsheet",
      "text/csv",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ].join(",");

    const view = new google.picker.DocsView(google.picker.ViewId.SPREADSHEETS)
      .setMimeTypes(mimeTypes);

    const builder = new google.picker.PickerBuilder()
      .setDeveloperKey(currentArgs.developerKey)
      .setOAuthToken(currentArgs.oauthToken)
      .setOrigin(currentArgs.appOrigin);

    if (currentArgs.appId) {
      builder.setAppId(currentArgs.appId);
    }

    const picker = builder
      .addView(view)
      .setCallback(onPickerCallback)
      .build();

    picker.setVisible(true);
    setButtonLabel("Opening Google Drive…");
    setStatus("Choose a spreadsheet or CSV file.");
  } catch {
    setStatus("Picker could not open.", "error");
  }
}

// ── Load gapi / Picker library ───────────────────────────────────────

function loadPickerLibrary(): void {
  if (pickerLibraryLoading || pickerReady) return;
  pickerLibraryLoading = true;

  setStatus("Loading Google Drive Picker…");
  setButtonLabel("Loading…");

  const script = document.createElement("script");
  script.src = "https://apis.google.com/js/api.js";
  script.async = true;
  script.onload = () => {
    window.gapi?.load("picker", {
      callback: () => {
        pickerReady = true;
        pickerLibraryLoading = false;
        button.disabled = false;
        setButtonLabel("Open Google Drive Picker");
        setStatus("Ready");
      },
    });
  };
  script.onerror = () => {
    pickerLibraryLoading = false;
    setButtonLabel("Retry");
    setStatus("Picker library could not load.", "error");
  };
  document.head.appendChild(script);
}

// ── Theme application ────────────────────────────────────────────────

function applyTheme(theme: string): void {
  document.body.setAttribute("data-theme", theme);
}

// ── Streamlit render callback ────────────────────────────────────────

function onRender(event: Event): void {
  const { args } = (event as CustomEvent<RenderData>).detail;
  currentArgs = args as Args;

  applyTheme(currentArgs.theme ?? "dark");

  // New requestId means a fresh attempt — reset state, allow a new event.
  if (eventSentForRequestId !== currentArgs.requestId) {
    eventSentForRequestId = null;
  }

  button.disabled = !pickerReady;

  loadPickerLibrary();
  Streamlit.setFrameHeight();
}

// ── Wire up ──────────────────────────────────────────────────────────

button.addEventListener("click", openPicker);
Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
Streamlit.setComponentReady();
Streamlit.setFrameHeight();
