import React, { useState } from "react";
import axios from "axios";

export default function DeleteDataPage() {
  const [options, setOptions] = useState({
    database: false,
    output_csv: false,
    logs: false,
    uploads: false,
  });
  const [result, setResult] = useState(null);
  const [showConfirm, setShowConfirm] = useState(false);

  const toggleOption = (key) => {
    setOptions({ ...options, [key]: !options[key] });
  };

  const handleDelete = async () => {
    try {
      const res = await axios.post("http://localhost:8000/delete-data", options);
      console.log("✅ Delete response:", res.data);
      setResult(res.data);
    } catch (err) {
      console.error("❌ Delete failed:", err);
      setResult({ error: "Delete failed" });
    }
    setShowConfirm(false); // close modal after action
  };

  return (
    <div className="content">
      <div className="card">
        <h2 style={{ color: "#ff5555" }}>Delete Data</h2>
        <p>Select what you want to delete:</p>

        <label>
          <input type="checkbox" checked={options.database} onChange={() => toggleOption("database")} />
          Database (SQLite)
        </label><br/>
        <label>
          <input type="checkbox" checked={options.output_csv} onChange={() => toggleOption("output_csv")} />
          Output CSV directory
        </label><br/>
        <label>
          <input type="checkbox" checked={options.logs} onChange={() => toggleOption("logs")} />
          Logs directory
        </label><br/>
        <label>
          <input type="checkbox" checked={options.uploads} onChange={() => toggleOption("uploads")} />
          Uploads directory
        </label><br/>

        <button
          onClick={() => setShowConfirm(true)}
          style={{ marginTop: "1rem", background: "#ff5555", color: "white" }}
        >
          Delete Selected
        </button>

        {/* Confirmation Modal */}
        {showConfirm && (
          <div className="modal-overlay">
            <div className="modal">
              <h3 style={{ color: "#ff5555" }}>⚠️ Confirm Deletion</h3>
              <p>
                You are about to delete selected data. This action <strong>cannot be undone</strong>.
                Are you sure you want to proceed?
              </p>
              <div style={{ marginTop: "1rem" }}>
                <button
                  onClick={handleDelete}
                  style={{ background: "#ff5555", color: "white", marginRight: "1rem" }}
                >
                  Yes, Delete
                </button>
                <button onClick={() => setShowConfirm(false)}>Cancel</button>
              </div>
            </div>
          </div>
        )}

        {/* Professional summary output */}
        {result && (
          <div className="result" style={{ marginTop: "1rem" }}>
            <h3>Deletion Summary</h3>
            <table className="summary-table">
              <thead>
                <tr>
                  <th>Component</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(result.summary || {}).map(([key, val]) => (
                  <tr key={key}>
                    <td>{key}</td>
                    <td>{val}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
