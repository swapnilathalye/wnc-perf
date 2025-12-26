import React, { useEffect, useMemo, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from "recharts";
import axios from "axios";

export default function ActiveContextsOverallChart({ activeFolder }) {
  const [resolvedFolder, setResolvedFolder] = useState(activeFolder);
  const [rows, setRows] = useState([]);
  const [granularity, setGranularity] = useState("daily");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [message, setMessage] = useState("");

  const [aiInsights, setAiInsights] = useState("");
  const [aiQuestion, setAiQuestion] = useState("");
  const [aiAnswer, setAiAnswer] = useState("");
  const [aiLoading, setAiLoading] = useState(false);

  // ------------------------------------------------------------
  // Resolve active folder
  // ------------------------------------------------------------
  useEffect(() => {
    console.log("[ActiveContextsOverallChart] activeFolder prop:", activeFolder);

    if (activeFolder) {
      console.log("[ActiveContextsOverallChart] Using provided activeFolder:", activeFolder);
      setResolvedFolder(activeFolder);
      return;
    }

    console.log("[ActiveContextsOverallChart] Fetching current-active-folder...");
    axios
      .get("http://localhost:8000/current-active-folder")
      .then((res) => {
        console.log("[ActiveContextsOverallChart] current-active-folder response:", res.data);
        setResolvedFolder(res.data.folder || null);
      })
      .catch((err) => {
        console.error("[ActiveContextsOverallChart] Failed to fetch current-active-folder:", err);
        setResolvedFolder(null);
      });
  }, [activeFolder]);

  const tableName = resolvedFolder ? `${resolvedFolder}_MethodContextStats` : "";
  console.log("[ActiveContextsOverallChart] Resolved tableName:", tableName);

  // ------------------------------------------------------------
  // Pivot rows → chartData
  // ------------------------------------------------------------
  const { chartData, seriesKeys } = useMemo(() => {
    console.log("[ActiveContextsOverallChart] Pivoting rows:", rows.length);

    const map = new Map();
    const series = new Set();

    for (const r of rows) {
      if (!r?.iso) continue;

      if (!map.has(r.iso)) map.set(r.iso, { iso: r.iso });

      const key = `JVM ${r.JVM_ID}`;
      series.add(key);
      map.get(r.iso)[key] = r.max_active;
    }

    const data = Array.from(map.values()).sort(
      (a, b) => new Date(a.iso) - new Date(b.iso)
    );

    console.log("[ActiveContextsOverallChart] Pivot result:", {
      points: data.length,
      series: Array.from(series)
    });

    return { chartData: data, seriesKeys: Array.from(series).sort() };
  }, [rows]);

  // ------------------------------------------------------------
  // Fetch data + AI insights
  // ------------------------------------------------------------
  const fetchDataAndInsights = () => {
    if (!tableName) {
      console.warn("[ActiveContextsOverallChart] No tableName, skipping fetch.");
      return;
    }

    console.log("[ActiveContextsOverallChart] Fetching data + AI insights:", {
      tableName,
      granularity,
      startDate,
      endDate
    });

    axios
      .get("http://localhost:8000/active-contexts-ai-insights", {
        params: {
          table_name: tableName,
          limit: 200,
          granularity,
          start_date: startDate || undefined,
          end_date: endDate || undefined
        }
      })
      .then((res) => {
        console.log("[ActiveContextsOverallChart] Data response:", res.data);

        if (res.data.message && !res.data.rows) {
          console.warn("[ActiveContextsOverallChart] Backend message:", res.data.message);
          setMessage(res.data.message);
          setRows([]);
          setAiInsights("");
          return;
        }

        setMessage("");
        setRows(res.data.rows || []);
        setAiInsights(res.data.ai_insights || "");

        // ------------------------------------------------------------
        // NEW: Auto-set date range from backend min/max
        // ------------------------------------------------------------
        if (res.data.min_iso && res.data.max_iso) {
          const minDate = res.data.min_iso.split("T")[0];
          const maxDate = res.data.max_iso.split("T")[0];

          console.log("[ActiveContextsOverallChart] Setting date range from backend:", {
            minDate,
            maxDate
          });

          setStartDate(minDate);
          setEndDate(maxDate);
        }
      })
      .catch((err) => {
        console.error("[ActiveContextsOverallChart] Error fetching data:", err);
        setMessage("Error fetching data");
        setRows([]);
        setAiInsights("");
      });
  };

  // ------------------------------------------------------------
  // Trigger fetch on folder or granularity change
  // ------------------------------------------------------------
  useEffect(() => {
    console.log("[ActiveContextsOverallChart] Trigger fetch:", {
      resolvedFolder,
      granularity
    });

    if (resolvedFolder) fetchDataAndInsights();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resolvedFolder, granularity]);

  // ------------------------------------------------------------
  // Ask AI
  // ------------------------------------------------------------
  const handleAskAi = () => {
    if (!aiQuestion.trim() || !tableName) {
      console.warn("[ActiveContextsOverallChart] AI question empty or no tableName.");
      return;
    }

    console.log("[ActiveContextsOverallChart] Asking AI:", aiQuestion);

    setAiLoading(true);
    setAiAnswer("");

    axios
      .post(
        "http://localhost:8000/active-contexts-ai-query",
        { question: aiQuestion },
        {
          params: {
            table_name: tableName,
            limit: 200,
            granularity,
            start_date: startDate || undefined,
            end_date: endDate || undefined
          }
        }
      )
      .then((res) => {
        console.log("[ActiveContextsOverallChart] AI response:", res.data);
        setAiAnswer(res.data.answer || "No answer returned.");
      })
      .catch((err) => {
        console.error("[ActiveContextsOverallChart] AI error:", err);
        setAiAnswer("Error getting AI answer.");
      })
      .finally(() => {
        setAiLoading(false);
      });
  };

  // ------------------------------------------------------------
  // Clear dates
  // ------------------------------------------------------------
  const clearDates = () => {
    console.log("[ActiveContextsOverallChart] Clearing dates");
    setStartDate("");
    setEndDate("");
  };

  // ------------------------------------------------------------
  // Reset last 7 days
  // ------------------------------------------------------------
  const resetLast7Days = () => {
    console.log("[ActiveContextsOverallChart] Resetting to last 7 days");

    const today = new Date();
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(today.getDate() - 7);

    setStartDate(sevenDaysAgo.toISOString().split("T")[0]);
    setEndDate(today.toISOString().split("T")[0]);
  };

  // ------------------------------------------------------------
  // UI
  // ------------------------------------------------------------
  return (
    <div className="jvm-chart-container">
      <div className="chart-toolbar">
        <h3 className="chart-title">Active Contexts (All JVMs)</h3>

        <div className="granularity-select">
          <label htmlFor="granularity">Granularity:</label>
          <select
            id="granularity"
            value={granularity}
            onChange={(e) => setGranularity(e.target.value)}
          >
            <option value="raw">Raw</option>
            <option value="hourly">Hourly</option>
            <option value="daily">Daily</option>
          </select>
        </div>

        <div className="date-filter">
          <label>From:</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />

          <label>To:</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            min={startDate || undefined}
          />

          <button className="apply-btn" onClick={fetchDataAndInsights}>
            Apply
          </button>

          <button className="apply-btn secondary" type="button" onClick={resetLast7Days}>
            Last 7 days
          </button>

          <button className="apply-btn ghost" type="button" onClick={clearDates}>
            Clear
          </button>
        </div>
      </div>

      {message ? (
        <div className="no-data">{message}</div>
      ) : (
        <ResponsiveContainer width="100%" height={420}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ccc" />
            <XAxis
              dataKey="iso"
              tickFormatter={(value) => new Date(value).toLocaleDateString()}
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip labelFormatter={(label) => new Date(label).toLocaleString()} />
            <Legend />

            {seriesKeys.map((key) => (
              <Line
                key={key}
                type={granularity === "raw" ? "linear" : "monotone"}
                dataKey={key}
                strokeWidth={2}
                dot={granularity === "raw" ? { r: 2 } : false}
                activeDot={{ r: 5 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}

      <div className="ai-insights">
        <h4>AI Insights</h4>
        <p>{aiInsights || "No AI insights available yet."}</p>
      </div>

      <div className="ai-query-box">
        <h4>Ask AI about this data</h4>
        <div className="ai-query-row">
          <input
            type="text"
            placeholder="e.g. Which JVM has the biggest spike?"
            value={aiQuestion}
            onChange={(e) => setAiQuestion(e.target.value)}
          />
          <button onClick={handleAskAi} disabled={aiLoading || !aiQuestion.trim()}>
            {aiLoading ? "Asking..." : "Ask AI"}
          </button>
        </div>
        {aiAnswer && <div className="ai-answer">{aiAnswer}</div>}
      </div>
    </div>
  );
}
