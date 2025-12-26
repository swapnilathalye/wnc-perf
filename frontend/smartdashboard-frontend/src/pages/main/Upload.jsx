import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function Upload() {
  const [message, setMessage] = useState("");
  const [details, setDetails] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleFile = async (file) => {
    console.log("📂 Selected file:", file.name);

    if (!file.name.endsWith(".zip")) {
      setMessage("❌ Only .zip files are supported.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      setMessage("⏳ Uploading...");
      const res = await axios.post("http://localhost:8000/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      console.log("✅ Upload response:", res.data);

      setMessage(res.data.message);
      setDetails({
        converter_success: res.data.converter_success,
        csv_count: res.data.csv_count,
        tables: res.data.tables || [],
      });

      // ✅ Refresh Performance page if converter succeeded
      /*   if (res.data.converter_success && res.data.tables && res.data.tables.length > 0) {
           const firstTable = res.data.tables[0].tableName;
           console.log("🔄 Navigating to performance page for:", firstTable);
           navigate(`/perf/${firstTable}`);
         } 
           */
    } catch (err) {
      console.error("❌ Upload failed:", err);
      setMessage("❌ Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    if (e.target.files[0]) handleFile(e.target.files[0]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  };

  return (
    <div className="content">
      <div className="card upload-card">
        <h2 style={{ marginTop: 0, color: "#66d9ef" }}>Upload Data</h2>
        <p className="panel-subtle">
          Upload a zip file. It will be extracted, and if a JMXData file is found,
          it will be passed to the Java converter to generate CSVs.
        </p>

        {/* Drag & Drop Zone */}
        <div
          className={`drop-zone ${dragActive ? "active" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
        >
          <p>Drag & Drop your ZIP file here</p>
          <p style={{ margin: "0.5rem 0" }}>or</p>
          <label className="browse-btn">
            Choose File
            <input type="file" accept=".zip" onChange={handleChange} hidden />
          </label>
        </div>

        {/* Message */}
        {loading && <div className="upload-message">⏳ Uploading…</div>}
        {!loading && message && <div className="upload-message">{message}</div>}

        {/* Upload details */}
        {details && (
          <div className="upload-details">
            <p>Converter Success: {details.converter_success ? "✅ Yes" : "❌ No"}</p>
            <p>CSV Files Registered: {details.csv_count}</p>
          </div>
        )}

        {/* Converted tables */}
        {/* Converted tables */}
        {details && details.tables && details.tables.length > 0 && (
          <div className="upload-summary">
            <h3>Converted Tables</h3>

            {/* ✅ Scroll only the table area */}
            <div className="table-scroll">
              <table className="perf-table">
                <thead>
                  <tr>
                    <th>Table Name</th>
                    <th>Rows</th>
                  </tr>
                </thead>
                <tbody>
                  {details.tables.map((t, idx) => (
                    <tr key={idx}>
                      <td>{t.tableName}</td>
                      <td>{t.rows}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
