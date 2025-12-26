import React, { useState } from "react";

export default function AIQueryBox() {
  const [query, setQuery] = useState("");
  const [insights, setInsights] = useState([
    "Sales increased 12% in Q4",
    "Anomaly detected in region 3",
    "Forecast suggests 8% growth next month"
  ]);

  const runQuery = () => {
    if (!query.trim()) return;
    setInsights(prev => [`AI result for: ${query}`, ...prev]);
    setQuery("");
  };

  return (
    <div className="card small-card">
      <h4 style={{ marginTop: 0 }}>AI Query</h4>
      <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: "0.5rem" }}>
        <input
          className="ai-input"
          placeholder="Search data using AI..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button className="ai-btn" onClick={runQuery}>Query</button>
      </div>
      <ul className="insights">
        {insights.map((i, idx) => <li key={idx}>{i}</li>)}
      </ul>
    </div>
  );
}
