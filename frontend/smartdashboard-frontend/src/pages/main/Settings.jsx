import React, { useEffect, useState } from "react";
import axios from "axios";

export default function SettingsPage() {
  const [days, setDays] = useState(7);
  const [autoDelete, setAutoDelete] = useState(false);

  const [languages, setLanguages] = useState([]);
  const [language, setLanguage] = useState("en");

  // ---------------------------------------
  // Fetch supported languages (industry standard)
  // ---------------------------------------
  useEffect(() => {
    const fetchLanguages = async () => {
      try {
        console.log("🌐 Fetching supported languages...");
        const res = await axios.get("http://localhost:8000/settings/languages");
        console.log("✅ Languages loaded:", res.data);

        setLanguages(res.data.languages || []);
        setLanguage(res.data.default || "en");
      } catch (err) {
        console.error("❌ Failed to load languages:", err);
        // fallback (safe default)
        setLanguages([{ code: "en", label: "English" }]);
        setLanguage("en");
      }
    };

    fetchLanguages();
  }, []);

  // ---------------------------------------
  // Save settings
  // ---------------------------------------
  const handleSave = async () => {
    try {
      const payload = {
        days,
        autoDelete,
        language,
      };

      console.log("💾 Saving settings:", payload);

      const res = await axios.post("http://localhost:8000/settings", payload);
      console.log("✅ Settings saved:", res.data);
      alert("Settings saved successfully!");
    } catch (err) {
      console.error("❌ Failed to save settings:", err);
      alert("Failed to save settings");
    }
  };

  return (
    <div className="content">
      <div className="card settings-card">
        <h2 style={{ color: "#66d9ef" }}>Application Settings</h2>
        <p className="panel-subtle">
          Configure data retention and application preferences.
        </p>

        {/* ---------------- Data Retention ---------------- */}
        <div className="settings-section">
          <label className="settings-label">
            Delete data after{" "}
            <span style={{ color: "#ff6b6b", fontWeight: 700 }}>{days}</span> days
          </label>

          <input
            type="range"
            min="1"
            max="30"
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="settings-slider"
          />

          <label className="settings-checkbox">
            <input
              type="checkbox"
              checked={autoDelete}
              onChange={() => setAutoDelete(!autoDelete)}
            />
            Enable auto-delete (unchecked = preserve data)
          </label>
        </div>

        {/* ---------------- Language Selection ---------------- */}
        <div className="settings-section">
          <label className="settings-label">Default Application Language</label>

          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="settings-select"
          >
            {languages.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.label}
              </option>
            ))}
          </select>

          <div className="settings-hint">
           AI will give output in this language.
          </div>
        </div>

        {/* ---------------- Save ---------------- */}
        <div className="settings-actions">
          <button className="dashboard-btn" onClick={handleSave}>
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
}
