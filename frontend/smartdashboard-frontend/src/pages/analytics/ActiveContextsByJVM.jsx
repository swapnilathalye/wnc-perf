import React, { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Label,
} from "recharts";
import axios from "axios";

export default function ActiveContextByJvmChart({ activeFolder }) {
  const [resolvedFolder, setResolvedFolder] = useState(activeFolder);
  const [data, setData] = useState([]);
  const [granularity, setGranularity] = useState("daily");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [message, setMessage] = useState("");
  const [selectedJvm, setSelectedJvm] = useState("");

  const [aiInsights, setAiInsights] = useState("");
  const [aiQuestion, setAiQuestion] = useState("");
  const [aiAnswer, setAiAnswer] = useState("");
  const [aiLoading, setAiLoading] = useState(false);

  // ------------------------------------------------------------
  // Resolve active folder
  // ------------------------------------------------------------
  useEffect(() => {
    if (activeFolder) {
      console.log("✅ Using activeFolder from parent:", activeFolder);
      setResolvedFolder(activeFolder);
      return;
    }

    console.log("📡 Fetching active folder from API...");
    axios
      .get("http://localhost:8000/current-active-folder")
      .then((res) => {
        console.log("✅ Active folder API response:", res.data);
        setResolvedFolder(res.data.folder || null);
      })
      .catch((err) => {
        console.error("❌ Failed to fetch active folder:", err);
        setResolvedFolder(null);
      });
  }, [activeFolder]);

  const tableName = resolvedFolder ? `${resolvedFolder}_MethodContextStats` : "";

  // ------------------------------------------------------------
  // Fetch data + AI insights + min/max dates
  // ------------------------------------------------------------
  const fetchDataAndInsights = () => {
    if (!resolvedFolder) return;

    console.log("📡 Fetching JVM chart data + AI insights for:", tableName);

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
        console.log("✅ API Response:", res.data);

        if (res.data.message && !res.data.rows) {
          setMessage(res.data.message);
          setData([]);
          setSelectedJvm("");
          setAiInsights("");
          return;
        }

        setMessage("");
        const rows = res.data.rows || [];
        setData(rows);
        setAiInsights(res.data.ai_insights || "");

        // ------------------------------------------------------------
        // NEW: Auto-set date range from backend min/max
        // ------------------------------------------------------------
        if (res.data.min_iso && res.data.max_iso) {
          const minDate = res.data.min_iso.split("T")[0];
          const maxDate = res.data.max_iso.split("T")[0];

          console.log("📅 Setting date range from backend:", { minDate, maxDate });

          setStartDate(minDate);
          setEndDate(maxDate);
        }

        // JVM list
        const jvms = [...new Set(rows.map((r) => r.JVM_ID))].sort((a, b) => a - b);
        console.log("🧵 JVM IDs:", jvms);

        setSelectedJvm(jvms[0] || "");
      })
      .catch((err) => {
        console.error("❌ Failed to fetch JVM chart data + AI insights:", err);
        setMessage("Error fetching data");
        setData([]);
        setSelectedJvm("");
        setAiInsights("");
      });
  };

  // ------------------------------------------------------------
  // Trigger fetch when folder or granularity changes
  // ------------------------------------------------------------
  useEffect(() => {
    console.log("🎯 useEffect triggered. resolvedFolder:", resolvedFolder, "granularity:", granularity);
    if (resolvedFolder) fetchDataAndInsights();
  }, [resolvedFolder, granularity]);

  const allJvmIds = [...new Set(data.map((r) => r.JVM_ID))].sort((a, b) => a - b);

  console.log("🎯 allJvmIds:", allJvmIds);
  console.log("🎯 selectedJvm:", selectedJvm);

  // ------------------------------------------------------------
  // Ask AI
  // ------------------------------------------------------------
  const handleAskAi = () => {
    if (!aiQuestion.trim() || !tableName) return;

    console.log("🤖 Asking AI:", aiQuestion);

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
        console.log("🤖 AI Answer:", res.data.answer);
        setAiAnswer(res.data.answer || "No answer returned.");
      })
      .catch((err) => {
        console.error("❌ Failed to get AI answer:", err);
        setAiAnswer("Error getting AI answer.");
      })
      .finally(() => {
        setAiLoading(false);
      });
  };

  // ------------------------------------------------------------
  // UI
  // ------------------------------------------------------------
  return (
    <div className="jvm-chart-container">
      <div className="chart-toolbar">
        <h3 className="chart-title">Active Contexts by JVM</h3>

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
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />

          <label>To:</label>
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />

          <button className="apply-btn" onClick={fetchDataAndInsights}>
            Apply
          </button>
        </div>

        <div className="jvm-select">
          <label htmlFor="jvm">JVM:</label>
          <select id="jvm" value={selectedJvm} onChange={(e) => setSelectedJvm(e.target.value)}>
            {allJvmIds.map((id) => (
              <option key={id} value={id}>
                JVM {id}
              </option>
            ))}
          </select>
        </div>
      </div>

      {message ? (
        <div className="no-data">{message}</div>
      ) : (
        <ResponsiveContainer width="100%" height={400}>
  <LineChart
    data={selectedJvm ? data.filter((r) => r.JVM_ID === selectedJvm) : data}
    margin={{ top: 10, right: 20, left: 20, bottom: 40 }} // ✅ room for rotated dates
  >
    <CartesianGrid strokeDasharray="3 3" stroke="#ccc" />
    <XAxis
      dataKey="iso"
      tickFormatter={(value) => new Date(value).toLocaleDateString()}
      tick={{ fontSize: 12 }}
      interval="preserveStartEnd"   // ✅ prevents too many labels
      minTickGap={28}               // ✅ spacing between ticks
      angle={-30}                   // ✅ less rotation reduces overlap
      textAnchor="end"
      height={60}                   // ✅ reserve space for labels
      tickMargin={10}
    />
    <YAxis tick={{ fontSize: 12 }}>
      {/* ✅ Y axis label */}
      <Label
        value="Max active contexts"
        angle={-90}
        position="insideLeft"
        offset={-5}
        style={{ textAnchor: "middle" }}
      />
    </YAxis>
    <Tooltip
      labelFormatter={(label) => new Date(label).toLocaleString()}
      formatter={(value) => [`${value}`, `JVM ${selectedJvm}`]}
    />
    <Line
      type="monotone"
      dataKey="max_active"
      stroke="#2d9cff"
      strokeWidth={2}
      dot={false}
    />
  </LineChart>
</ResponsiveContainer>

      )}

      <div className="ai-insights">
        <h4>AI Insights</h4>
        <p>{aiInsights || "No AI insights available yet."}</p>
      </div>

   <div class="ai-section">
	<h3>AI Insights</h3><
		div class="ai-row">
			<input placeholder="e.g. Which JVM shows the biggest spike?" 
			class="ai-input" type="text" value={aiQuestion}
            onChange={(e) => setAiQuestion(e.target.value)}/>
			<button onClick={handleAskAi} disabled={aiLoading || !aiQuestion.trim()}>
            {aiLoading ? "Asking..." : "Ask AI"}
          </button>
		</div>
		{aiAnswer && <div className="ai-answer">{aiAnswer}</div>}
</div>
    </div>
  );
}
