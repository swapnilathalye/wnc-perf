import React, { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from "recharts";
import axios from "axios";

export default function ActiveUsersChart() {
  const [jvmOptions, setJvmOptions] = useState([]);
  const [selectedJvm, setSelectedJvm] = useState("all");

  const [rows, setRows] = useState([]);
  const [granularity, setGranularity] = useState("daily");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [message, setMessage] = useState("");

  const [aiInsights, setAiInsights] = useState("");
  const [aiQuestion, setAiQuestion] = useState("");
  const [aiAnswer, setAiAnswer] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [dateDefaultsLoaded, setDateDefaultsLoaded] = useState(false);


  // Fetch JVM IDs for dropdown
  useEffect(() => {
    axios
      .get("http://localhost:8000/active-users-jvms")
      .then((res) => {
        const jvms = res.data.jvms || [];
        setJvmOptions(jvms);
      })
      .catch((err) => {
        console.error("[ActiveUsersChart] Failed to fetch JVM list:", err);
        setJvmOptions([]);
      });
  }, []);

  useEffect(() => {
  // Only load defaults once
  if (dateDefaultsLoaded) return;

  console.log("[ActiveUsersChart] Fetching default date range from backend...");
  axios
    .get("http://localhost:8000/active-users-date-range")
    .then((res) => {
      console.log("[ActiveUsersChart] Date range response:", res.data);

      if (res.data.start_date && res.data.end_date) {
        setStartDate(res.data.start_date);
        setEndDate(res.data.end_date);
      }
      setDateDefaultsLoaded(true);
    })
    .catch((err) => {
      console.error("[ActiveUsersChart] Failed to fetch date range:", err);
      // Still mark loaded to avoid infinite retries
      setDateDefaultsLoaded(true);
    });
}, [dateDefaultsLoaded]);


  const fetchDataAndInsights = () => {
    console.log("[ActiveUsersChart] Fetching:", {
      selectedJvm,
      granularity,
      startDate,
      endDate
    });

    axios
      .get("http://localhost:8000/active-users-ai-insights", {
        params: {
          jvm: selectedJvm, // "all" or JVM id
          limit: 200,
          granularity,
          start_date: startDate || undefined,
          end_date: endDate || undefined
        }
      })
      .then((res) => {
        if (res.data.message && !res.data.rows) {
          setMessage(res.data.message);
          setRows([]);
          setAiInsights("");
          return;
        }

        setMessage("");
        setRows(res.data.rows || []);
        setAiInsights(res.data.ai_insights || "");
      })
      .catch((err) => {
        console.error("[ActiveUsersChart] fetch error:", err);
        setMessage("Error fetching data");
        setRows([]);
        setAiInsights("");
      });
  };

  // auto refresh on dropdown/granularity change
 useEffect(() => {
  if (!dateDefaultsLoaded) return;
  fetchDataAndInsights();
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, [selectedJvm, granularity, dateDefaultsLoaded]);


  const handleAskAi = () => {
    if (!aiQuestion.trim()) return;

    setAiLoading(true);
    setAiAnswer("");

    axios
      .post(
        "http://localhost:8000/active-users-ai-query",
        { question: aiQuestion },
        {
          params: {
            jvm: selectedJvm,
            limit: 200,
            granularity,
            start_date: startDate || undefined,
            end_date: endDate || undefined
          }
        }
      )
      .then((res) => setAiAnswer(res.data.answer || "No answer returned."))
      .catch((err) => {
        console.error("[ActiveUsersChart] AI error:", err);
        setAiAnswer("Error getting AI answer.");
      })
      .finally(() => setAiLoading(false));
  };

  const clearDates = () => {
    setStartDate("");
    setEndDate("");
  };

  return (
    <div className="jvm-chart-container">
      <div className="chart-toolbar">
        <h3 className="chart-title">Active Users</h3>

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
          <button className="apply-btn ghost" type="button" onClick={clearDates}>
            Clear
          </button>
        </div>

        <div className="jvm-select">
          <label htmlFor="jvm">JVM:</label>
          <select
            id="jvm"
            value={selectedJvm}
            onChange={(e) => setSelectedJvm(e.target.value)}
          >
            <option value="all">All</option>
            {jvmOptions.map((id) => (
              <option key={String(id)} value={String(id)}>
                JVM {id}
              </option>
            ))}
          </select>
        </div>
      </div>

      {message ? (
        <div className="no-data">{message}</div>
      ) : (
        <ResponsiveContainer width="100%" height={420}>
          <LineChart
            data={rows}
            margin={{ top: 10, right: 20, left: 20, bottom: 40 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#ccc" />
            <XAxis
              dataKey="iso"
              tickFormatter={(v) => new Date(v).toLocaleDateString()}
              interval="preserveStartEnd"
              minTickGap={28}
              angle={-30}
              textAnchor="end"
              height={60}
              tickMargin={10}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              label={{
                value: "Total active users",
                angle: -90,
                position: "insideLeft",
                offset: -5
              }}
            />
            <Tooltip labelFormatter={(label) => new Date(label).toLocaleString()} />
            <Line
              type={granularity === "raw" ? "linear" : "monotone"}
              dataKey="total_active_users"
              stroke="#2d9cff"
              strokeWidth={2}
              dot={granularity === "raw" ? { r: 2 } : false}
              activeDot={{ r: 5 }}
            />
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
            placeholder="e.g. Which JVM has the highest peak in this period?"
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
