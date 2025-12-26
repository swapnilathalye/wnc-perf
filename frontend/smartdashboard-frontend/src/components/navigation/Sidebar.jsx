import React, { useState, useEffect } from "react";
import {
  FaTachometerAlt,
  FaChartLine,
  FaDatabase,
  FaBug,
  FaCogs,
  FaBars,
  FaTable,
  FaUpload,
  FaHistory,
  FaTrash
} from "react-icons/fa";
import { NavLink } from "react-router-dom";
import axios from "axios";

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [perfOpen, setPerfOpen] = useState(false);
  const [analyticsOpen, setAnalyticsOpen] = useState(false); // NEW toggle for Analytics
  const [activeTables, setActiveTables] = useState([]);

  // ✅ Fetch active tables from backend
  useEffect(() => {
    const fetchActiveTables = async () => {
      try {
        const res = await axios.get("http://localhost:8000/active-tables");
        const tables =
          res.data.tables ||
          res.data.active_tables ||
          [];
        setActiveTables(tables);
      } catch (err) {
        console.error("❌ Failed to fetch active tables:", err);
        setActiveTables([]);
      }
    };
    fetchActiveTables();
  }, []);

  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="sidebar-header">
        <button
          className="collapse-btn"
          aria-label="Toggle sidebar"
          onClick={() => setCollapsed(!collapsed)}
        >
          <FaBars />
        </button>
        {!collapsed && <div className="sidebar-brand">SMART AI DASHBOARD</div>}
      </div>

      <nav className="nav">
        <NavLink className="nav-item" to="/upload">
          <FaUpload /> {!collapsed && "Upload Data"}
        </NavLink>
        <NavLink className="nav-item" to="/upload-history">
          <FaHistory /> {!collapsed && "Upload History"}
        </NavLink>
        <NavLink className="nav-item" to="/dashboard">
          <FaTachometerAlt /> {!collapsed && "Dashboard"}
        </NavLink>

        {/* Collapsible Analytics */}
        <div
          className="nav-item nav-item-toggle"
          onClick={() => setAnalyticsOpen(!analyticsOpen)}
        >
          <FaChartLine /> {!collapsed && "Analytics"}
        </div>
        {analyticsOpen && !collapsed && (
          <div className="sub-nav">
           <NavLink className="nav-sub-item" to="/analytics/active-contexts-overall">
  Active Contexts Overall
</NavLink>

            <NavLink className="nav-sub-item" to="/analytics/active-users">
              Active Users
            </NavLink>
             <NavLink className="nav-sub-item" to="/analytics/active-contexts-ai">
              Active Contexts By JVM
            </NavLink>
          </div>
        )}

        <NavLink className="nav-item" to="/database">
          <FaDatabase /> {!collapsed && "Database"}
        </NavLink>
        <NavLink className="nav-item" to="/errors">
          <FaBug /> {!collapsed && "Errors"}
        </NavLink>
        <NavLink className="nav-item" to="/delete-data">
          <FaTrash /> {!collapsed && "Delete Data"}
        </NavLink>
        <NavLink className="nav-item" to="/settings">
          <FaCogs /> {!collapsed && "Settings"}
        </NavLink>
        <NavLink className="nav-item" to="/perf">
          <FaTable /> {!collapsed && "Performance Tables"}
        </NavLink>

     

      </nav>
    </aside>
  );
}
  