import React from "react";

export default function Database() {
  return (
    <div className="content">
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Database Overview</h3>
        <p className="panel-subtle">Demo data: 3 active clusters, 120 tables.</p>
        <ul style={{color:"#bcd3ff"}}>
          <li>Cluster A — 45 tables</li>
          <li>Cluster B — 50 tables</li>
          <li>Cluster C — 25 tables</li>
        </ul>
      </div>

      <div className="card" style={{marginTop:12}}>
        <h3 style={{ marginTop: 0 }}>Recent Queries</h3>
        <ul style={{color:"#bcd3ff"}}>
          <li>SELECT * FROM users — 0.8s</li>
          <li>UPDATE orders SET status='shipped' — 1.1s</li>
          <li>DELETE FROM sessions WHERE expired=1 — 0.6s</li>
        </ul>
      </div>
    </div>
  );
}
