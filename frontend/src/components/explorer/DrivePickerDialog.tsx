import { useEffect, useRef } from "react";
import { FolderOpen, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useExplorer } from "@/lib/explorer-store";

// Public API key restricted to HTTP referrers (Task 0 Gate 2 / Task 4) — ships
// in the frontend bundle by design; never a secret, never a backend credential.
const PICKER_API_KEY = (import.meta.env as Record<string, string | undefined>)
  .VITE_GOOGLE_PICKER_API_KEY;

// CSV / XLS / XLSX only — Google-native files are rejected server-side
// (workspace_export_required), so the Picker filter drops Sheets (Task 0/4).
const PICKER_MIME_TYPES =
  "text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel";

// Minimal structural types for the Picker JS API (loaded at runtime from
// https://apis.google.com/js/api.js — never bundled).
interface PickerData {
  action?: string;
  docs?: { id?: string; name?: string }[];
}

interface PickerBuilder {
  setVisible(visible: boolean): void;
}

interface PickerBuilderApi {
  setAppId(id: string): PickerBuilderApi;
  setOAuthToken(token: string): PickerBuilderApi;
  setDeveloperKey(key: string): PickerBuilderApi;
  setOrigin(origin: string): PickerBuilderApi;
  addView(view: unknown): PickerBuilderApi;
  setCallback(cb: (data: PickerData) => void): PickerBuilderApi;
  build(): PickerBuilder;
}

interface DocsViewApi {
  setMimeTypes(mimes: string): DocsViewApi;
  setSelectFolderEnabled(enabled: boolean): DocsViewApi;
}

interface GapiPickerModule {
  PickerBuilder: new () => PickerBuilderApi;
  DocsView: new (viewId: string) => {
    setMimeTypes(mimes: string): DocsViewApi;
    setSelectFolderEnabled(enabled: boolean): DocsViewApi;
  };
  ViewId: { DOCS: string };
  Action: { PICKED: string; CANCEL: string };
}

interface GapiNamespace {
  load(api: string, callback: () => void): void;
  picker?: GapiPickerModule;
}

/** Dialog for the Picker-first Drive flow (D1). The JIT access token lives in
 *  component memory only — cleared on select/cancel/close, never persisted
 *  (Task 4 token-containment rules). */
export function DrivePickerDialog() {
  const { drivePickerOpen, pickerToken, closeDrivePicker, downloadFromDrive } = useExplorer();
  const pickerRef = useRef<PickerBuilder | null>(null);

  useEffect(() => {
    if (!drivePickerOpen || !pickerToken) return;

    pickerRef.current?.setVisible(false);
    pickerRef.current = null;

    if (!PICKER_API_KEY) return; // fallback UI below shows the setup hint

    let cancelled = false;

    const boot = () => {
      if (cancelled || !pickerToken) return;
      const gapi = (window as { gapi?: GapiNamespace }).gapi;
      if (!gapi) return;
      gapi.load("picker", () => {
        if (cancelled || !pickerToken) return;
        const pickerApi = gapi.picker;
        if (!pickerApi) return;

        const builder = new pickerApi.PickerBuilder()
          .setAppId(pickerToken.appId ?? "")
          .setOAuthToken(pickerToken.accessToken)
          .setDeveloperKey(PICKER_API_KEY)
          .setOrigin(window.location.origin)
          .addView(
            new pickerApi.DocsView(pickerApi.ViewId.DOCS)
              .setMimeTypes(PICKER_MIME_TYPES)
              .setSelectFolderEnabled(false),
          )
          .setCallback((data: PickerData) => {
            // The token is memory-only: no persistence anywhere (Task 4).
            if (data.action === pickerApi.Action.PICKED && data.docs?.length) {
              const doc = data.docs[0];
              if (doc.id) {
                void downloadFromDrive({ requestId: pickerToken.requestId, fileId: doc.id });
              }
            } else if (data.action === pickerApi.Action.CANCEL) {
              closeDrivePicker();
            }
          });

        const picker = builder.build();
        pickerRef.current = picker;
        picker.setVisible(true);
      });
    };

    const gapi = (window as { gapi?: GapiNamespace }).gapi;
    if (gapi?.load) {
      boot();
    } else {
      const script = document.createElement("script");
      script.src = "https://apis.google.com/js/api.js";
      script.async = true;
      script.onload = boot;
      document.body.appendChild(script);
    }

    return () => {
      cancelled = true;
    };
  }, [drivePickerOpen, pickerToken, downloadFromDrive, closeDrivePicker]);

  return (
    <Dialog
      open={drivePickerOpen}
      onOpenChange={(open) => {
        if (!open) closeDrivePicker();
      }}
    >
      <DialogContent className="sm:max-w-md" data-testid="drive-picker-dialog">
        <DialogHeader className="flex flex-row items-center gap-2">
          <FolderOpen className="h-5 w-5 text-muted-foreground" aria-hidden />
          <DialogTitle>Import from Google Drive</DialogTitle>
        </DialogHeader>
        {PICKER_API_KEY ? (
          <div className="flex flex-col gap-3">
            <p className="text-sm text-muted-foreground">
              Choose a <strong>CSV or Excel</strong> file. It downloads securely on the server
              and becomes your active dataset.
            </p>
            <div className="flex items-center gap-2 rounded-md border bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
              <ShieldCheck className="h-4 w-4 shrink-0" aria-hidden />
              Google Sheets import isn't supported yet — pick a CSV or XLSX file.
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <p className="text-sm text-muted-foreground">
              The Drive Picker needs a referrer-restricted API key
              (<code>VITE_GOOGLE_PICKER_API_KEY</code>) to open. Add it to the frontend env and
              reload to import from Drive.
            </p>
            <Button variant="outline" onClick={closeDrivePicker}>
              Close
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
