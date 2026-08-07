import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/explorer/AppShell";

export const Route = createFileRoute("/")({
  component: AppShell,
});
