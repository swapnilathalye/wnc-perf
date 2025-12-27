import React, { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";

import ActiveSessionsGraph from "../../components/charts/ActiveSessionsGraph";

export default function Dashboard() {
  const { folderName } = useParams();

  const [activeFolder, setActiveFolder] = useState(null);
  const [tables, setTables] = useState([]);
  const [loading, setLoading] = useState(true);

  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  useEffect(() => {
    const loadActiveFolder = async () => {
      try {
        console.log("📡 [Dashboard] Fetching current active folder...");
        const res = await axios.get("http://localhost:8000/current-active-folder");
        console.log("✅ [Dashboard] Active folder response:", res.data);

        let folder = res.data.folder;
        let tableList = res.data.tables || [];

        if (folderName) {
          console.log("🔄 [Dashboard] URL param overrides active folder:", folderName);
          folder = folderName;
        }

        setActiveFolder(folder || null);
        setTables(tableList);
      } catch (err) {
        console.error("❌ [Dashboard] Failed to fetch active folder:", err);
        setActiveFolder(null);
        setTables([]);
      } finally {
        setLoading(false);
      }
    };

    loadActiveFolder();
  }, [folderName]);

  const demoSystem = useMemo(
    () => ({
      version: "v1.3.0",
      build: "2025.12.24",
      env: "Production-like",
      runtime: "Java 8",
    }),
    []
  );

  const demoParams = useMemo(
    () => [
      { label: "Active Users", value: "320", sub: "Last 24h avg", trend: "+4%" },
      { label: "Errors", value: "12", sub: "Last 24h", trend: "-18%" },
      { label: "Avg Latency", value: "185ms", sub: "P50", trend: "+6%" },
    ],
    []
  );

  const demoCharts = useMemo(
    () => [
      { title: "Active Users Trend", subtitle: "Demo (replace with real chart)", stat: "Peak 410", footer: "Daily view" },
      { title: "Error Rate Trend", subtitle: "Demo (replace with real chart)", stat: "1.2%", footer: "Rolling 7d" },
      { title: "Latency Distribution", subtitle: "Demo (replace with real chart)", stat: "P95 620ms", footer: "Current" },
    ],
    []
  );

  const exportPDF = async () => {
    const node = document.getElementById("dashboard-root");
    if (!node) return;

    try {
      const canvas = await html2canvas(node);
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("p", "mm", "a4");
      const imgProps = pdf.getImageProperties(imgData);
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
      pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);
      pdf.save("dashboard.pdf");
    } catch (e) {
      console.error("❌ [Dashboard] Export PDF failed:", e);
    }
  };

  if (loading) {
    return (
      <div className="app-shell">
        <div className="main">
          <h2 style={{ color: "#66d9ef" }}>⏳ Loading Dashboard…</h2>
        </div>
      </div>
    );
  }

  if (!activeFolder) {
    return (
      <div className="app-shell">
        <div className="main">
          <div className="card">
            <h2 style={{ marginTop: 0, color: "#66d9ef" }}>SMART AI DASHBOARD</h2>
            <p style={{ color: "#bcd3ff" }}>No active folder found. Please upload data or select a folder.</p>
            <div style={{ marginTop: "1rem" }}>
              <Link to="/upload" className="dashboard-btn">
                ➕ Upload Data
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      {/* dashboard-root is now a flex container so the grid can fill viewport height */}
      <div className="main dashboard-root" id="dashboard-root">
        <div className="dashboard-vp-grid">
          {/* ========== SECTION 1 (20%) ========== */}
          <section className="dash-section card dash-s1">
            <div className="dash-section-head">
              <h3 className="dash-h3">Overview</h3>
              <div className="dash-note subtle">Live folder + controls</div>
            </div>

            {/* ✅ Internal scroll container */}
            <div className="dash-section-body dash-s1-body">
              <div className="dash-s1-grid">
                {/* 1) Title */}
                <div className="dash-mini-card">
                  <div className="dash-mini-top">
                    <div>
                      <div className="dash-title">SMART AI DASHBOARD</div>
                      <div className="dash-subtitle">Executive performance overview</div>
                    </div>
                    <div className="dash-chip">LIVE</div>
                  </div>
                  <div className="dash-meta">
                    Viewing: <strong>{activeFolder}</strong>
                  </div>
                  <div className="dash-meta subtle">
                    Tables loaded: <strong>{tables.length}</strong>
                  </div>
                </div>

                {/* 2) Date range */}
                <div className="dash-mini-card">
                  <div className="dash-mini-head">Date Range</div>

                  <div className="date-filter-pro">
                    <div className="date-field">
                      <label className="dash-label">From</label>
                      <input
                        type="date"
                        className="date-input-pro"
                        value={fromDate}
                        onChange={(e) => {
                          console.log("[Dashboard] fromDate:", e.target.value);
                          setFromDate(e.target.value);
                        }}
                      />
                    </div>

                    <div className="date-field">
                      <label className="dash-label">To</label>
                      <input
                        type="date"
                        className="date-input-pro"
                        min={fromDate || undefined}
                        value={toDate}
                        onChange={(e) => {
                          console.log("[Dashboard] toDate:", e.target.value);
                          setToDate(e.target.value);
                        }}
                      />
                    </div>
                  </div>

                  <div className="dash-help subtle">Demo defaults (wire to backend later)</div>
                </div>

                {/* 3) Export / Actions */}
                <div className="dash-mini-card">
                  <div className="dash-mini-head">Actions</div>
                  <div className="dash-actions">
                    <button className="dashboard-btn" onClick={exportPDF}>
                      📄 Export PDF
                    </button>
                    <button className="dashboard-btn" onClick={() => window.print()}>
                      🖨️ Print
                    </button>
                    <button
                      className="dashboard-btn"
                      onClick={() => {
                        const subject = encodeURIComponent("Dashboard Report");
                        const body = encodeURIComponent(
                          "Dashboard link:\n" + window.location.href + "\n\n(Attach exported PDF if needed)"
                        );
                        window.location.href = `mailto:?subject=${subject}&body=${body}`;
                      }}
                    >
                      ✉️ Email
                    </button>
                  </div>
                  <div className="dash-help subtle">Professional export options</div>
                </div>

                {/* 4) System Version */}
                <div className="dash-mini-card">
                  <div className="dash-mini-head">System</div>
                  <div className="kv">
                    <span className="k">Version</span>
                    <span className="v">{demoSystem.version}</span>
                  </div>
                  <div className="kv">
                    <span className="k">Build</span>
                    <span className="v">{demoSystem.build}</span>
                  </div>
                  <div className="kv">
                    <span className="k">Runtime</span>
                    <span className="v">{demoSystem.runtime}</span>
                  </div>
                  <div className="kv">
                    <span className="k">Env</span>
                    <span className="v">{demoSystem.env}</span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* ========== SECTION 2 (20%) ========== */}
          <section className="dash-section card dash-s2">
            <div className="dash-section-head">
              <h3 className="dash-h3">System Parameters</h3>
              <div className="dash-note subtle">Demo KPIs (wire to real metrics later)</div>
            </div>

            <div className="dash-section-body dash-s2-body">
              <div className="dash-s2-grid">
                {demoParams.map((p) => (
                  <div className="dash-kpi-card" key={p.label}>
                    <div className="dash-kpi-top">
                      <div className="dash-kpi-label">{p.label}</div>
                      <div className={`dash-kpi-trend ${p.trend.startsWith("-") ? "down" : "up"}`}>
                        {p.trend}
                      </div>
                    </div>
                    <div className="dash-kpi-value">{p.value}</div>
                    <div className="dash-kpi-sub subtle">{p.sub}</div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* ========== SECTION 3 (30%) ========== */}
          <section className="dash-section card dash-s3">
            <div className="dash-section-head">
              <h3 className="dash-h3">Charts</h3>
              <div className="dash-note subtle">Demo placeholders (current graphs removed)</div>
            </div>

            <div className="dash-section-body dash-s3-body">
              <div className="dash-s3-grid">
                {/* 1️⃣ Active Sessions Graph */}
                 <ActiveSessionsGraph />
                {demoCharts.map((c) => (
                  <div className="dash-chart-card" key={c.title}>
                    <div className="dash-chart-head">
                      <div>
                        <div className="dash-chart-title">{c.title}</div>
                        <div className="dash-chart-sub subtle">{c.subtitle}</div>
                      </div>
                      <div className="dash-chart-stat">{c.stat}</div>
                    </div>

                    <div className="dash-chart-placeholder">
                      <div className="dash-placeholder-line" />
                      <div className="dash-placeholder-line" />
                      <div className="dash-placeholder-line" />
                      <div className="dash-placeholder-bars">
                        <div className="bar" />
                        <div className="bar" />
                        <div className="bar" />
                        <div className="bar" />
                        <div className="bar" />
                      </div>
                    </div>

                    <div className="dash-chart-foot subtle">{c.footer}</div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* ========== SECTION 4 (30%) ========== */}
          <section className="dash-section card dash-s4">
            <div className="dash-section-head">
              <h3 className="dash-h3">AI Assistance</h3>
              <div className="dash-note subtle">Insights + Query (demo text)</div>
            </div>

            <div className="dash-section-body dash-s4-body">
              <div className="dash-s4-grid">
                {/* AI Insights */}
                <div className="dash-ai-card">
                  <div className="dash-ai-head">
                    <div className="dash-ai-title">AI Insights</div>
                    <div className="dash-chip muted">AUTO</div>
                  </div>
                  <div className="dash-ai-body">
                    <ul className="dash-ai-list">
                      <li>Spike detected in demo latency chart around mid-window.</li>
                      <li>Error trend improving week-over-week in sample dataset.</li>
                      <li>Capacity headroom appears stable (demo KPI).</li>
                    </ul>
                  </div>
                  <div className="dash-ai-foot subtle">Replace with live insights API output</div>
                </div>

                {/* AI Query */}
                <div className="dash-ai-card">
                  <div className="dash-ai-head">
                    <div className="dash-ai-title">AI Query</div>
                    <div className="dash-chip">ASK</div>
                  </div>

                  <div className="dash-ai-body">
                    <label className="dash-label">Question</label>
                    <textarea
                      className="dash-textarea"
                      rows={4}
                      placeholder="e.g. What changed in active users between the selected dates?"
                      onChange={(e) => console.log("[Dashboard] AI query typed:", e.target.value)}
                    />
                    <div className="dash-ai-actions">
                      <button
                        className="dashboard-btn"
                        onClick={() => console.log("[Dashboard] Demo AI query submit")}
                      >
                        Run Query
                      </button>
                      <button
                        className="dashboard-btn secondary"
                        onClick={() => console.log("[Dashboard] Demo clear")}
                      >
                        Clear
                      </button>
                    </div>

                    <div className="dash-ai-answer">
                      <div className="dash-ai-answer-head">Answer (Demo)</div>
                      <div className="dash-ai-answer-body subtle">
                        Based on demo data, active users increased slightly while error rates decreased.
                        Replace this with backend AI response.
                      </div>
                    </div>
                  </div>

                  <div className="dash-ai-foot subtle">Wire to /active-users-ai-query (or similar)</div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
