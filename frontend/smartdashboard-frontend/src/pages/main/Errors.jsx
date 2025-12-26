import React from "react";

export default function Errors() {
  return (
    <div className="content">
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Error Logs</h3>
        <ul style={{color:"#f87171"}}>
          <li>[12:01] API /login — Timeout</li>
          <li>[12:05] DB connection lost — Cluster B</li>
          <li>[12:10] Null pointer in MethodPerformance</li>
        </ul>
      </div>

      <div className="card" style={{marginTop:12}}>
        <h3 style={{ marginTop: 0 }}>Error Trends</h3>
        <div style={{height:200, display:"flex", alignItems:"center", justifyContent:"center", color:"#9fbbe8"}}>
          [Error Chart Placeholder]
        </div>
      </div>
    </div>
  );
}
