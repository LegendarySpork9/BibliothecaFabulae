import {
  AlertTriangle,
  Clock,
  Loader2,
  Play,
  Square,
  XCircle,
} from "lucide-react";

import type { SyncState } from "../../types/source";
import type { Source } from "../../types/source";

interface SyncStatusCardProps {
  source: Source;
  syncState: SyncState | null;
  onSync: (sourceId: number) => void;
  onCancel: (sourceId: number) => void;
  isSyncing: boolean;
  isCancelling: boolean;
}

export function SyncStatusCard({
  source,
  syncState,
  onSync,
  onCancel,
  isSyncing,
  isCancelling,
}: SyncStatusCardProps) {
  const status = syncState?.sync_status || "idle";
  const isActive = status === "syncing" || isSyncing;
  const progressCurrent = syncState?.sync_progress_current || 0;
  const progressTotal = syncState?.sync_progress_total;
  const progressPercent = progressTotal && progressTotal > 0
    ? Math.round((progressCurrent / progressTotal) * 100)
    : 0;

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-base font-medium text-gray-900 dark:text-gray-100">
          {source.label}
        </h3>
        {isActive ? (
          <button
            onClick={() => onCancel(source.id)}
            disabled={isCancelling}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Square className="h-3.5 w-3.5" />
            {isCancelling ? "Stopping..." : "Stop Sync"}
          </button>
        ) : (
          <button
            onClick={() => onSync(source.id)}
            disabled={!source.is_enabled}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Play className="h-3.5 w-3.5" />
            Sync Now
          </button>
        )}
      </div>

      {status === "syncing" && (
        <div className="mb-3 space-y-2">
          <div className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>
              {progressTotal
                ? `${progressCurrent} / ${progressTotal}`
                : "Starting..."}
            </span>
          </div>
          {progressTotal && progressTotal > 0 && (
            <div className="h-2 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
              <div
                className="h-full rounded-full bg-blue-500 transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          )}
          {syncState?.sync_message && (
            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
              {syncState.sync_message}
            </p>
          )}
        </div>
      )}

      {status === "blocked" && (
        <div className="mb-3 flex items-start gap-2 p-2 rounded bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
          <AlertTriangle className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
          <p className="text-xs text-amber-700 dark:text-amber-300">
            {syncState?.sync_message || "Blocked by Cloudflare — try again later"}
          </p>
        </div>
      )}

      {status === "failed" && (
        <div className="mb-3 flex items-start gap-2 p-2 rounded bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <XCircle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
          <p className="text-xs text-red-700 dark:text-red-300">
            {syncState?.sync_message || "Sync failed"}
          </p>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <span className="text-gray-500 dark:text-gray-400">Last Synced</span>
          <p className="font-medium text-gray-900 dark:text-gray-100">
            {syncState?.last_synced
              ? new Date(syncState.last_synced).toLocaleString()
              : "Never"}
          </p>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">Total Synced</span>
          <p className="font-medium text-gray-900 dark:text-gray-100">
            {syncState?.total_synced || 0}
          </p>
        </div>
        <div className="flex items-center gap-1 text-gray-500 dark:text-gray-400">
          <Clock className="h-3.5 w-3.5" />
          <span className="text-xs font-mono">{source.sync_interval_bookmarks}</span>
        </div>
      </div>
    </div>
  );
}
