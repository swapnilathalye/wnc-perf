
import React from "react";
import { createRoot } from "react-dom/client";
import App from "./app/App";
import './styles/base.css';
import './styles/layout.css';
import './styles/components.css';
import './styles/tables.css';
import './styles/upload.css';
import './styles/sidebar.css';
import './styles/dashboard.css';
import './styles/chart.css';

const root = createRoot(document.getElementById("root"));
root.render(<App />);
