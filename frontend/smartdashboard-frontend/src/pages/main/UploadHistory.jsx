import React, { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function UploadHistory() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await axios.get("http://localhost:8000/upload/history");
        console.log("✅ Upload history response:", res.data);
        setHistory(res.data.history || []);
      } catch (err) {
        console.error("❌ Failed to fetch upload history:", err);
        setError("Failed to load upload history.");
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  if (loading) return <div className="content">⏳ Loading upload history…</div>;
  if (error) return <div className="content">{error}</div>;

  return (
    <div className="content">
      <div className="card">
        <h2 style={{ marginTop: 0, color: "#66d9ef" }}>Upload History</h2>
        <p className="panel-subtle">
          Below are all past uploads with their corresponding converted CSVs.
        </p>

        {history.length === 0 ? (
          <p>No uploads found.</p>
        ) : (
          <table className="perf-table">
            <thead>
              <tr>
                <th>Folder</th>
                <th>Uploaded Files</th>
                <th>Converted CSVs</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {history.map((h, idx) => (
                <tr key={idx}>
                  <td>{h.folder_name}</td>
                  <td>
                    {h.upload_files && h.upload_files.length > 0 ? (
                      <ul>
                        {h.upload_files.map((f, i) => (
                          <li key={i}>{f.split("\\").pop()}</li>
                        ))}
                      </ul>
                    ) : (
                      <em>No uploads</em>
                    )}
                  </td>
                  <td>
                    {h.output_files && h.output_files.length > 0 ? (
                      <ul>
                        {h.output_files.map((f, i) => (
                          <li key={i}>{f.split("\\").pop()}</li>
                        ))}
                      </ul>
                    ) : (
                      <em>No CSVs</em>
                    )}
                  </td>
                  <td style={{ display: "flex", gap: "0.5rem" }}>
                    {/* View Dashboard */}
                    <button
                      className="dashboard-btn"
                      onClick={async () => {
                        console.log("➡️ Updating active tables for:", h.folder_name);

                        try {
                          const res = await axios.post("http://localhost:8000/set-active-tables", {
                            folder_name: h.folder_name,
                          });

                          console.log("🔄 Active tables updated:", res.data.tables);

                          if (res.data.tables && res.data.tables.length > 0) {
                            navigate(`/perf/${res.data.tables[0]}`);
                          } else {
                            navigate(`/dashboard/${res.data.folder}`);
                          }
                        } catch (err) {
                          console.error("❌ Failed to set active tables:", err);
                          navigate(`/dashboard/${h.folder_name}`);
                        }
                      }}
                    >
                      📊 View Dashboard
                    </button>



                    {/* Download CSVs */}
                    {h.output_files && h.output_files.length > 0 && (
                      <a
                        href={`http://localhost:8000/download/${h.folder_name}`}
                        className="download-btn"
                      >
                        ⬇️ Download CSVs
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
