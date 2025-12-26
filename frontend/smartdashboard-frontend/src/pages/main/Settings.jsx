import React, { useState } from "react";

import axios from "axios";

export default function SettingsPage() {
  const [days, setDays] = useState(7); // default 7 days
  const [autoDelete, setAutoDelete] = useState(false);

  const handleSave = async () => {
  try {
    const res = await axios.post("http://localhost:8000/settings", { days, autoDelete });
    console.log("✅ Settings saved:", res.data);
    alert("Settings saved successfully!");
  } catch (err) {
    console.error("❌ Failed to save settings:", err);
    alert("Failed to save settings");
  }
};


  return (
    <div className="content">
      <div className="card">
        <h2 style={{ color: "#66d9ef" }}>Data Retention Settings</h2>
        <p>Configure how long data should be kept before deletion.</p>

        {/* Slider */}
        <label style={{ fontWeight: "bold" }}>
          Delete data after <span style={{ color: "#ff5555" }}>{days}</span> days
        </label>
        <input
          type="range"
          min="1"
          max="30"
          value={days}
          onChange={(e) => setDays(parseInt(e.target.value))}
          style={{ width: "100%", marginTop: "1rem" }}
        />

        {/* Checkbox */}
        <div style={{ marginTop: "1rem" }}>
          <label>
            <input
              type="checkbox"
              checked={autoDelete}
              onChange={() => setAutoDelete(!autoDelete)}
            />
            Enable auto‑delete (unchecked = preserve data)
          </label>
        </div>

        {/* Save button */}
        <button
          onClick={handleSave}
          style={{
            marginTop: "1.5rem",
            background: "#66d9ef",
            color: "white",
            padding: "0.5rem 1rem",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
          }}
        >
          Save Settings
        </button>
      </div>
    </div>
  );
}
