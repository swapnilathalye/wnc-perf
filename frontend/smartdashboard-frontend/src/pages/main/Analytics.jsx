import React from "react";

export default function Analytics() {
  return (
    <div className="content">
      <div className="card">
        <h3 style={{ marginTop: 0 }}>User Growth</h3>
        <p className="panel-subtle">
          Demo data: Active users increased by 15% this quarter.
        </p>
        <div className="chart-wrap">
          {/* Replace with real chart later */}
          <div style={{height:200, display:"flex", alignItems:"center", justifyContent:"center", color:"#9fbbe8"}}>
            [Line Chart Placeholder]
          </div>
        </div>
      </div>

      <div className="card" style={{marginTop:12}}>
        <h3 style={{ marginTop: 0 }}>Engagement Metrics</h3>
        <ul style={{color:"#bcd3ff"}}>
          <li>Average session length: 5m 20s</li>
          <li>Bounce rate: 32%</li>
          <li>Top feature: AI Query Box</li>
        </ul>
      </div>
    </div>
  );
}
