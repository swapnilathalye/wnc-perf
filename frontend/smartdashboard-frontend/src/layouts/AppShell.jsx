import React from "react";
import Sidebar from "../components/navigation/Sidebar";

/**
 * AppShell
 * - Keeps global layout consistent (sidebar + main content)
 * - Styling lives in CSS (layout.css/sidebar.css)
 */
export default function AppShell({ children }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">{children}</main>
    </div>
  );
}
