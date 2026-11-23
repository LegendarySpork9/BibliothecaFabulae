import axios from "axios";
import { useState } from "react";

import { useToast } from "../../../hooks/useToast";

interface StorageStepProps {
  onNext: (path: string) => void;
  onBack: () => void;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) {
    return "0 B";
  }
  
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

export function StorageStep({ onNext, onBack }: StorageStepProps) {
  const { showToast } = useToast();

  const [path, setPath] = useState("");
  const [validated, setValidated] = useState(false);
  const [diskInfo, setDiskInfo] = useState<{
    total_bytes: number;
    free_bytes: number;
  } | null>(null);
  const [loading, setLoading] = useState(false);

  const handleValidate = async () => {
    setLoading(true);

    try {
      const response = await axios.post("/api/setup/storage", {
        storage_path: path,
      });
      setDiskInfo(response.data);
      setValidated(true);
      showToast("Storage path validated", "success");
    }

    catch (err) {
      const message =
        axios.isAxiosError(err)
          ? err.response?.data?.detail || "Invalid storage path"
          : "Invalid storage path";
      showToast(message, "error");
      setValidated(false);
    }

    finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
        Storage Path
      </h2>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        Choose where to store your fic files and database.
      </p>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Storage Directory
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={path}
            onChange={(e) => {
              setPath(e.target.value);
              setValidated(false);
            }}
            placeholder="/path/to/storage"
            className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            type="button"
            onClick={handleValidate}
            disabled={loading || !path}
            className="rounded-lg bg-gray-600 px-4 py-2 text-white font-medium hover:bg-gray-700 disabled:opacity-50 transition-colors"
          >
            {loading ? "..." : "Validate"}
          </button>
        </div>
      </div>

      {validated && diskInfo && (
        <div className="rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-3 text-sm text-green-700 dark:text-green-300">
          <p>Path is valid and writable.</p>
          <p>
            Total: {formatBytes(diskInfo.total_bytes)} | Free:{" "}
            {formatBytes(diskInfo.free_bytes)}
          </p>
        </div>
      )}

      <div className="flex gap-3">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-gray-700 dark:text-gray-300 font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        >
          Back
        </button>
        <button
          type="button"
          onClick={() => onNext(path)}
          disabled={!validated}
          className="flex-1 rounded-lg bg-indigo-600 px-4 py-2 text-white font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          Next
        </button>
      </div>
    </div>
  );
}
