import {
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  Pencil,
  RefreshCw,
  Save,
  Settings,
  Trash2,
} from "lucide-react";
import { useState } from "react";

import type { Source } from "../../types/source";

interface SourceCardProps {
  source: Source;
  onToggle: (id: number, enabled: boolean) => void;
  onEditAuth: (source: Source) => void;
  onEditConfig: (source: Source) => void;
  onDelete: (source: Source) => void;
  onUpdateCron: (id: number, bookmarkCron: string, updateCron: string) => void;
  onValidate: (id: number) => void;
  isValidating: boolean;
}

const statusConfig = {
  valid: { icon: CheckCircle, color: "text-green-500", label: "Valid" },
  expired: { icon: AlertTriangle, color: "text-red-500", label: "Expired" },
  unknown: { icon: HelpCircle, color: "text-yellow-500", label: "Unknown" },
};

export function SourceCard({
  source,
  onToggle,
  onEditAuth,
  onEditConfig,
  onDelete,
  onUpdateCron,
  onValidate,
  isValidating,
}: SourceCardProps) {
  const status = statusConfig[source.auth_status] || statusConfig.unknown;
  const StatusIcon = status.icon;

  const [editingCron, setEditingCron] = useState(false);
  const [bookmarkCron, setBookmarkCron] = useState(source.sync_interval_bookmarks);
  const [updateCron, setUpdateCron] = useState(source.sync_interval_updates);

  const handleSaveCron = () => {
    onUpdateCron(source.id, bookmarkCron, updateCron);
    setEditingCron(false);
  };

  const handleCancelCron = () => {
    setBookmarkCron(source.sync_interval_bookmarks);
    setUpdateCron(source.sync_interval_updates);
    setEditingCron(false);
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
            {source.label}
          </h3>
          <span className="text-xs text-gray-400 dark:text-gray-500 font-mono">
            {source.site_key}
          </span>
        </div>

        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={source.is_enabled}
            onChange={() => onToggle(source.id, !source.is_enabled)}
            className="sr-only peer"
          />
          <div className="w-9 h-5 bg-gray-200 dark:bg-gray-600 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-indigo-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-600" />
        </label>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm mb-3">
        {source.auth_configured && (
          <>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Auth:</span>{" "}
              <span className="text-gray-900 dark:text-gray-100 capitalize">{source.auth_type}</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-gray-500 dark:text-gray-400">Status:</span>{" "}
              <StatusIcon className={`h-4 w-4 ${status.color}`} />
              <span className={status.color}>{status.label}</span>
            </div>
          </>
        )}
        {source.config_fields && (
          <div className="col-span-2">
            <span className="text-gray-500 dark:text-gray-400">Config:</span>{" "}
            <span className={source.config_configured ? "text-green-500" : "text-amber-500"}>
              {source.config_configured ? "Configured" : "Not configured"}
            </span>
          </div>
        )}

        {editingCron ? (
          <>
            <div>
              <label className="block text-gray-500 dark:text-gray-400 text-xs mb-1">
                Bookmark Sync (cron)
              </label>
              <input
                type="text"
                value={bookmarkCron}
                onChange={(e) => setBookmarkCron(e.target.value)}
                className="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-2 py-1 text-xs font-mono"
              />
            </div>
            <div>
              <label className="block text-gray-500 dark:text-gray-400 text-xs mb-1">
                Update Check (cron)
              </label>
              <input
                type="text"
                value={updateCron}
                onChange={(e) => setUpdateCron(e.target.value)}
                className="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-2 py-1 text-xs font-mono"
              />
            </div>
          </>
        ) : (
          <>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Bookmark Sync:</span>{" "}
              <span className="text-gray-900 dark:text-gray-100 font-mono text-xs">
                {source.sync_interval_bookmarks}
              </span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Update Check:</span>{" "}
              <span className="text-gray-900 dark:text-gray-100 font-mono text-xs">
                {source.sync_interval_updates}
              </span>
            </div>
          </>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => onEditAuth(source)}
          className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 rounded-md hover:bg-indigo-100 dark:hover:bg-indigo-900/50 transition-colors"
        >
          <Pencil className="h-3.5 w-3.5" />
          Auth
        </button>

        {source.auth_type !== "none" && source.auth_configured && (
          <button
            onClick={() => onValidate(source.id)}
            disabled={isValidating}
            className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/30 rounded-md hover:bg-green-100 dark:hover:bg-green-900/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isValidating ? "animate-spin" : ""}`} />
            {isValidating ? "Checking..." : "Validate"}
          </button>
        )}

        {source.config_fields && (
          <button
            onClick={() => onEditConfig(source)}
            className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-cyan-600 dark:text-cyan-400 bg-cyan-50 dark:bg-cyan-900/30 rounded-md hover:bg-cyan-100 dark:hover:bg-cyan-900/50 transition-colors"
          >
            <Settings className="h-3.5 w-3.5" />
            Config
          </button>
        )}

        {editingCron ? (
          <>
            <button
              onClick={handleSaveCron}
              className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/30 rounded-md hover:bg-emerald-100 dark:hover:bg-emerald-900/50 transition-colors"
            >
              <Save className="h-3.5 w-3.5" />
              Save
            </button>
            <button
              onClick={handleCancelCron}
              className="px-3 py-1.5 text-sm font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              Cancel
            </button>
          </>
        ) : (
          <button
            onClick={() => setEditingCron(true)}
            className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            Schedule
          </button>
        )}

        <button
          onClick={() => onDelete(source)}
          className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/30 rounded-md hover:bg-red-100 dark:hover:bg-red-900/50 transition-colors"
        >
          <Trash2 className="h-3.5 w-3.5" />
          Remove
        </button>
      </div>
    </div>
  );
}
