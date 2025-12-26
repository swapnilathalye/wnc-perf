import React from "react";
import { Routes, Route } from "react-router-dom";

import Dashboard from "../pages/main/Dashboard";
import Analytics from "../pages/main/Analytics";
import ActiveUsers from "../pages/analytics/ActiveUsers";
import ActiveContextsByJVM from "../pages/analytics/ActiveContextsByJVM";
import ActiveContextsOverall from "../pages/analytics/ActiveContextsOverall";


import Database from "../pages/main/Database";
import Errors from "../pages/main/Errors";
import Settings from "../pages/main/Settings";
import PerformanceTablePage from "../pages/main/PerformanceTablePage";
import Upload from "../pages/main/Upload";
import UploadHistory from "../pages/main/UploadHistory";
import DeleteDataPage from "../pages/main/DeleteDataPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />

      <Route path="/dashboard/:folderName" element={<Dashboard />} />
      <Route path="/analytics" element={<Analytics />} />
      <Route path="/database" element={<Database />} />
      <Route path="/errors" element={<Errors />} />
      <Route path="/settings" element={<Settings />} />
      <Route path="/upload" element={<Upload />} />
      <Route path="/upload-history" element={<UploadHistory />} />
      <Route path="/delete-data" element={<DeleteDataPage />} />

      <Route path="/perf" element={<PerformanceTablePage />} />
      <Route path="/perf/:tableName" element={<PerformanceTablePage />} />

      <Route path="/analytics/active-contexts-overall" element={<ActiveContextsOverall />} />

      <Route path="/analytics/active-users" element={<ActiveUsers />} />
      <Route path="/analytics/active-contexts-ai" element={<ActiveContextsByJVM />} />

      <Route path="*" element={<Dashboard />} />
    </Routes>
  );
}
