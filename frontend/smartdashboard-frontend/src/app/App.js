import React from "react";
import { BrowserRouter as Router } from "react-router-dom";

import { FolderProvider } from "../contexts/FolderContext";
import AppShell from "../layouts/AppShell";
import { AppRoutes } from "./routes";

export default function App() {
  return (
    <Router>
      <FolderProvider>
        <AppShell>
          <AppRoutes />
        </AppShell>
      </FolderProvider>
    </Router>
  );
}

