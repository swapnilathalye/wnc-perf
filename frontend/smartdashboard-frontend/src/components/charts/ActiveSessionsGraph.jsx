import React, { useEffect, useState } from "react";

const API_BASE = "http://localhost:8000"; // keep consistent with rest of app

export default function ActiveSessionsGraph() {
  const [data, setData] = useState(null);

  useEffect(() => {
    console.log("📡 [ActiveSessionsGraph] Fetching /active-sessions-graph");
    fetch(`${API_BASE}/active-sessions-graph`)
      .then((res) => res.json())
      .then((json) => {
        console.log("✅ [ActiveSessionsGraph] Response:", json);
        setData(json);
      })
      .catch((e) => {
        console.error("❌ [ActiveSessionsGraph] Fetch failed:", e);
        setData({ nodes: [] });
      });
  }, []);

  if (!data) {
    return (
      <div className="dash-chart-card">
        <div className="dash-chart-head">
          <div>
            <div className="dash-chart-title">Active Sessions</div>
            <div className="dash-chart-sub subtle">Loading...</div>
          </div>
        </div>
        <div className="dash-chart-placeholder">
          <div className="dash-placeholder-line" />
          <div className="dash-placeholder-line" />
          <div className="dash-placeholder-line" />
        </div>
      </div>
    );
  }

  return (
    <div className="dash-chart-card">
      <div className="dash-chart-head">
        <div>
          <div className="dash-chart-title">Active Sessions</div>
          <div className="dash-chart-sub subtle">Topology View</div>
        </div>
        <div className="dash-chart-stat">{(data.nodes || []).length} JVMs</div>
      </div>

      <div className="dash-chart-body">
        <div className="topology-graph">
          {(data.nodes || []).map((node) => (
            <div
              key={node.id}
              className="topology-node"
              style={{
                width: 40 + (node.peak_active || 0) * 20,
                height: 40 + (node.peak_active || 0) * 20,
              }}
              title={`JVM: ${node.id} | peak_active: ${node.peak_active}`}
            >
              {node.id}
            </div>
          ))}
        </div>
      </div>

      <div className="dash-chart-foot subtle">Peak sessions shown by node size</div>
    </div>
  );
}
