import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "@tanstack/react-router";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ExplorerProvider } from "@/lib/explorer-store";
import { router } from "./router";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <TooltipProvider delayDuration={200}>
      <ExplorerProvider>
        <RouterProvider router={router} />
      </ExplorerProvider>
    </TooltipProvider>
  </React.StrictMode>,
);
