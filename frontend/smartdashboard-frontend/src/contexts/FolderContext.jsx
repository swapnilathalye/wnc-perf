// src/context/FolderContext.js
import { createContext, useState, useEffect } from "react";
import axios from "axios";

export const FolderContext = createContext();

export function FolderProvider({ children }) {
  const [folderName, setFolderName] = useState(null);
  const [csvFiles, setCsvFiles] = useState([]);

  // Load latest folder on app startup
  useEffect(() => {
    const fetchLatest = async () => {
      try {
        const res = await axios.get("http://localhost:8000/latest-folder");
        if (res.data.folder_name) {
          setFolderName(res.data.folder_name);
          setCsvFiles(res.data.output_files || []);
        }
      } catch (err) {
        console.error("❌ Failed to fetch latest folder:", err);
      }
    };
    fetchLatest();
  }, []);

  return (
    <FolderContext.Provider
      value={{ folderName, setFolderName, csvFiles, setCsvFiles }}
    >
      {children}
    </FolderContext.Provider>
  );
}
