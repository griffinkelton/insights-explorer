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

function setStatus(message: string, success = false): void {
  statusEl.textContent = message;
  statusEl.className = success ? "success" : "";
  Streamlit.setFrameHeight();
}

// ── Return channel (sanitized — no file ID, filename, MIME, or raw error) ──

function emit(value: Record<string, unknown>): void {
  Streamlit.setComponentValue(value);
  Streamlit.setFrameHeight();
}

// ── Picker callback ──────────────────────────────────────────────────

function onPickerCallback(data: google.picker.ResponseObject): void {
  if (!currentArgs) return;

  if (data.action === google.picker.Action.PICKED) {
    // Prevent duplicate events for the same request
    if (eventSentForRequestId === currentArgs.requestId) return;

    eventSentForRequestId = currentArgs.requestId;
    emit({
      kind: "transport_verified",
      requestId: currentArgs.requestId,
    });
    button.disabled = true;
    setStatus("✓ Transport verified", true);
    return;
  }

  if (data.action === google.picker.Action.CANCEL) {
    setStatus("Picker closed");
  }
}

// ── Open Picker ──────────────────────────────────────────────────────

function openPicker(): void {
  if (!currentArgs || !pickerReady) {
    setStatus("Picker is unavailable.");
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

    // appId is optional — skip when not configured
    if (currentArgs.appId) {
      builder.setAppId(currentArgs.appId);
    }

    const picker = builder
      .addView(view)
      .setCallback(onPickerCallback)
      .build();

    picker.setVisible(true);
    setStatus("Picker opened.");
  } catch {
    setStatus("Picker could not open");
  }
}

// ── Load gapi / Picker library ───────────────────────────────────────

function loadPickerLibrary(): void {
  if (pickerLibraryLoading || pickerReady) return;
  pickerLibraryLoading = true;

  const script = document.createElement("script");
  script.src = "https://apis.google.com/js/api.js";
  script.async = true;
  script.onload = () => {
    window.gapi?.load("picker", {
      callback: () => {
        pickerReady = true;
        pickerLibraryLoading = false;
        button.disabled = false;
        setStatus("Ready");
      },
    });
  };
  script.onerror = () => {
    pickerLibraryLoading = false;
    setStatus("Picker library could not load.");
  };
  document.head.appendChild(script);
}

// ── Streamlit render callback ────────────────────────────────────────

function onRender(event: Event): void {
  const { args } = (event as CustomEvent<RenderData>).detail;
  currentArgs = args as Args;

  // New requestId means a fresh attempt — allow a new event
  // Always sync button state — pickerReady may have changed since last render
  button.disabled = !pickerReady;

  loadPickerLibrary();
  Streamlit.setFrameHeight();
}

// ── Wire up ──────────────────────────────────────────────────────────

button.addEventListener("click", openPicker);
Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
Streamlit.setComponentReady();
Streamlit.setFrameHeight();
