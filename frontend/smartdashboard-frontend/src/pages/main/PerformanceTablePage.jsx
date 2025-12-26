import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";

const API_BASE = "http://localhost:8000";

function prettifyTableName(t) {
  // Handles: 20251224_upload1_MethodContextStats -> MethodContextStats
  // Handles: MethodContextStats -> MethodContextStats
  const parts = String(t).split("_");
  if (parts.length >= 3 && parts[0].match(/^\d{8}$/) && parts[1].startsWith("upload")) {
    return parts.slice(2).join("_");
  }
  return t;
}

export default function PerformanceTablesPage() {
  const [tables, setTables] = useState([]);
  const [selectedTable, setSelectedTable] = useState("");

  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [searchTerm, setSearchTerm] = useState("");
  const [visibleCols, setVisibleCols] = useState([]);

  // sorting
  const [sortConfig, setSortConfig] = useState({ key: null, direction: "asc" });

  // AI (uses your tabular endpoint: /perf-ai-query)
  const [aiQuery, setAiQuery] = useState("");
  const [aiAnswer, setAiAnswer] = useState("");
  const [aiLoading, setAiLoading] = useState(false);

  // ---------------------------------------
  // Fetch active tables
  // ---------------------------------------
  useEffect(() => {
    const fetchTables = async () => {
      try {
        console.log("📡 [PerfTables] Fetching active tables...");
        const res = await axios.get(`${API_BASE}/active-tables`);
        const list = res.data.tables || res.data.active_tables || [];
        console.log("✅ [PerfTables] Active tables:", list);

        setTables(list);

        // Auto-select first table (same behavior)
        if (list.length > 0) setSelectedTable(list[0]);
      } catch (e) {
        console.error("❌ [PerfTables] Failed to fetch tables:", e);
        setTables([]);
      }
    };

    fetchTables();
  }, []);

  // ---------------------------------------
  // Fetch rows for selected table
  // ---------------------------------------
  useEffect(() => {
    const fetchRows = async () => {
      if (!selectedTable) return;

      setLoading(true);
      setError("");
      setRows([]);

      try {
        console.log("📥 [PerfTables] Fetching rows:", { table: selectedTable, limit: 200 });
        const res = await axios.get(`${API_BASE}/table/${selectedTable}?limit=200`);
        const data = res.data.rows || [];
        console.log("✅ [PerfTables] Rows fetched:", data.length);

        setRows(data);

        if (data.length > 0) {
          const cols = Object.keys(data[0]);
          setVisibleCols(cols);
          console.log("🧱 [PerfTables] Columns:", cols);
        } else {
          setVisibleCols([]);
        }

        // Reset sorting when switching table (keeps old behavior)
        setSortConfig({ key: null, direction: "asc" });

        // Reset search for clarity (optional; comment out if you want persistent search)
        setSearchTerm("");
      } catch (e) {
        console.error("❌ [PerfTables] Failed to fetch rows:", e);
        setError("Failed to load table rows.");
      } finally {
        setLoading(false);
      }
    };

    fetchRows();
  }, [selectedTable]);

  // ---------------------------------------
  // Filter + sort
  // ---------------------------------------
  const filteredRows = useMemo(() => {
    if (!searchTerm.trim()) return rows;

    const needle = searchTerm.toLowerCase();
    return rows.filter((row) =>
      Object.entries(row).some(([col, val]) => {
        if (!visibleCols.includes(col)) return false;
        return String(val ?? "").toLowerCase().includes(needle);
      })
    );
  }, [rows, searchTerm, visibleCols]);

  const sortedRows = useMemo(() => {
    const data = [...filteredRows];
    if (!sortConfig.key) return data;

    const key = sortConfig.key;
    const dir = sortConfig.direction;

    data.sort((a, b) => {
      const valA = a[key];
      const valB = b[key];

      if (valA == null && valB == null) return 0;
      if (valA == null) return 1;
      if (valB == null) return -1;

      const numA = Number(valA);
      const numB = Number(valB);
      const bothNumeric = !Number.isNaN(numA) && !Number.isNaN(numB);

      if (bothNumeric) return dir === "asc" ? numA - numB : numB - numA;

      const comp = String(valA).localeCompare(String(valB), undefined, {
        numeric: true,
        sensitivity: "base",
      });
      return dir === "asc" ? comp : -comp;
    });

    return data;
  }, [filteredRows, sortConfig]);

  const handleSort = (col) => {
    setSortConfig((prev) => {
      if (prev.key === col) {
        return { key: col, direction: prev.direction === "asc" ? "desc" : "asc" };
      }
      return { key: col, direction: "asc" };
    });
  };

  // ---------------------------------------
  // Columns
  // ---------------------------------------
  const toggleColumn = (col) => {
    setVisibleCols((prev) => (prev.includes(col) ? prev.filter((c) => c !== col) : [...prev, col]));
  };

  const toggleAllColumns = () => {
    if (rows.length === 0) return;
    const allCols = Object.keys(rows[0]);
    setVisibleCols((prev) => (prev.length === allCols.length ? [] : allCols));
  };

  // ---------------------------------------
  // AI Query (tabular endpoint)
  // ---------------------------------------
  const toShortTable = (t) => {
  // 20251225_upload1_CacheStatistics -> CacheStatistics
  // CacheStatistics -> CacheStatistics
  const parts = String(t).split("_");
  if (parts.length >= 3 && /^\d{8}$/.test(parts[0]) && parts[1].startsWith("upload")) {
    return parts.slice(2).join("_");
  }
  return t;
};

  const askAI = async () => {
  if (!aiQuery.trim() || !selectedTable) return;

  const shortTable = toShortTable(selectedTable);

  try {
    setAiLoading(true);
    setAiAnswer("");

    console.log("[PerfTables] AI query:", { table: shortTable, question: aiQuery });

    const res = await axios.post(
      `http://localhost:8000/tabular/perf-ai-query?table=${encodeURIComponent(shortTable)}&limit=200&sample=latest`,
      { question: aiQuery },
      { headers: { "Content-Type": "application/json" } }
    );

    console.log("✅ [PerfTables] AI response:", res.data);
    setAiAnswer(res.data.answer || "No answer returned.");
  } catch (e) {
    console.error("❌ [PerfTables] AI error:", e);
    setAiAnswer("AI failed. Check backend logs.");
  } finally {
    setAiLoading(false);
  }
};


  return (
    <div className="content">
      <div className="card page-card perf-page">
        {/* Header */}
        <div className="perf-head">
          <div>
            <h2 style={{ marginTop: 0, color: "#66d9ef" }}>Performance Tables</h2>
            <div className="panel-subtle">
              Explore converted tables, filter columns, sort, and ask AI questions over the selected table.
            </div>
          </div>

          <div className="perf-head-right">
            <div className="perf-pill">AI: Ollama</div>
          </div>
        </div>

        {/* Controls Row */}
        <div className="perf-controls">
          {/* Table dropdown */}
          <div className="perf-control-card">
            <label className="dropdown-label">Select Table</label>
            <select
              value={selectedTable}
              onChange={(e) => setSelectedTable(e.target.value)}
              className="dropdown"
            >
              {tables.map((t, idx) => (
                <option key={idx} value={t}>
                  {prettifyTableName(t)}
                </option>
              ))}
            </select>
            <div className="perf-meta subtle">
              Rows: <strong>{rows.length}</strong> • Visible columns: <strong>{visibleCols.length}</strong>
            </div>
          </div>

          {/* Search */}
          <div className="perf-control-card">
            <label className="dropdown-label">Search</label>
            <input
              type="text"
              placeholder="🔍 Search within visible columns..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
            <div className="perf-meta subtle">
              Filtered: <strong>{sortedRows.length}</strong>
            </div>
          </div>

          {/* Columns */}
          <div className="perf-control-card">
            <div className="perf-cols-head">
              <label className="dropdown-label">Columns</label>
              <button className="dashboard-btn" onClick={toggleAllColumns} type="button">
                {rows.length > 0 && visibleCols.length === Object.keys(rows[0]).length ? "Deselect All" : "Select All"}
              </button>
            </div>

            {rows.length === 0 ? (
              <div className="subtle">No columns (table is empty)</div>
            ) : (
              <div className="perf-cols-scroll scrollbar">
                {Object.keys(rows[0]).map((col) => (
                  <label key={col} className="col-option">
                    <input
                      type="checkbox"
                      checked={visibleCols.includes(col)}
                      onChange={() => toggleColumn(col)}
                    />
                    {col}
                  </label>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* AI Block */}
        <div className="perf-ai card">
          <div className="perf-ai-head">
            <div>
              <h3 style={{ margin: 0, color: "#66d9ef" }}>AI Query</h3>
              <div className="panel-subtle">Ask about anomalies, top offenders, trends, spikes, or summaries.</div>
            </div>
            <div className="perf-pill">Table: {prettifyTableName(selectedTable || "")}</div>
          </div>

          <div className="perf-ai-row">
            <input
              type="text"
              placeholder="Ask AI about this table… e.g., 'What are the top 5 slowest entries and why?'"
              value={aiQuery}
              onChange={(e) => setAiQuery(e.target.value)}
              className="ai-input"
              onKeyDown={(e) => {
                if (e.key === "Enter") askAI();
              }}
            />
            <button onClick={askAI} disabled={aiLoading} className="ai-btn" type="button">
              {aiLoading ? "Thinking..." : "Ask AI"}
            </button>
            <button
              onClick={() => {
                setAiQuery("");
                setAiAnswer("");
              }}
              className="ai-btn secondary"
              type="button"
            >
              Clear
            </button>
          </div>

          {aiAnswer && <div className="ai-output">{aiAnswer}</div>}
        </div>

        {/* Errors */}
        {error && <p style={{ color: "salmon", marginTop: 10 }}>{error}</p>}

        {/* Table (internal scroll only) */}
        <div className="table-scroll-container scrollbar perf-table-scroll">
          {loading ? (
            <p>⏳ Loading rows…</p>
          ) : rows.length === 0 ? (
            <p>No rows found.</p>
          ) : visibleCols.length === 0 ? (
            <p>No visible columns selected.</p>
          ) : (
            <table className="perf-table">
              <thead>
                <tr>
                  {visibleCols.map((col) => (
                    <th
                      key={col}
                      onClick={() => handleSort(col)}
                      style={{ cursor: "pointer", userSelect: "none" }}
                      title="Click to sort"
                    >
                      {col}
                      {sortConfig.key === col && (
                        <span style={{ marginLeft: 6 }}>
                          {sortConfig.direction === "asc" ? "▲" : "▼"}
                        </span>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sortedRows.map((row, idx) => (
                  <tr key={idx}>
                    {visibleCols.map((col) => (
                      <td key={col}>{row[col]}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
