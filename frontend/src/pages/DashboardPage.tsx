import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Bell, HardDrive } from "lucide-react";

import { getNotifications } from "../api/notifications";
import { getStorageInfo, getStorageWarnings } from "../api/storage";

function formatBytes(bytes: number): string {
  if (bytes === 0) {
    return "0 B";
  }
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

export function DashboardPage() {
  const { data: storage } = useQuery({
    queryKey: ["storage"],
    queryFn: getStorageInfo,
  });

  const { data: warnings } = useQuery({
    queryKey: ["storage", "warnings"],
    queryFn: getStorageWarnings,
  });

  const { data: notifications } = useQuery({
    queryKey: ["notifications", "recent"],
    queryFn: () => getNotifications({ limit: 5 }),
  });

  const usagePercent = storage
    ? Math.round((storage.storage_used_bytes / storage.disk_free_bytes) * 100)
    : 0;

  const usageColor =
    usagePercent >= 90
      ? "bg-red-500"
      : usagePercent >= 70
        ? "bg-yellow-500"
        : "bg-green-500";

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
        Dashboard
      </h1>

      <div className="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3 mb-3">
          <img src="/logo.png" alt="Logo" className="h-10 w-10" />
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Bibliotheca Fabulae
            </h2>
            <p className="text-xs text-gray-400 italic">Latin: Library of Tales</p>
          </div>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Your self-hosted personal fanfiction archive. Download and preserve fics from 100+ supported sites,
          organise your library, and read offline — all from a private web interface that you control.
        </p>
      </div>

      {warnings && warnings.length > 0 && (
        <div className="rounded-lg bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-4">
          <div className="flex items-center gap-2 text-yellow-800 dark:text-yellow-200">
            <AlertTriangle className="h-5 w-5" />
            <span className="font-medium">{warnings[0].message}</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Storage Card */}
        <div className="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-4">
            <HardDrive className="h-5 w-5 text-gray-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Storage
            </h2>
          </div>

          {storage ? (
            <>
              <div className="mb-2 flex justify-between text-sm text-gray-600 dark:text-gray-400">
                <span>{formatBytes(storage.storage_used_bytes)} used</span>
                <span>{formatBytes(storage.disk_free_bytes)} available</span>
              </div>
              <div className="h-3 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${usageColor}`}
                  style={{ width: `${Math.min(usagePercent, 100)}%` }}
                />
              </div>
            </>
          ) : (
            <div className="h-20 flex items-center justify-center text-gray-400">
              Loading...
            </div>
          )}
        </div>

        {/* Recent Notifications Card */}
        <div className="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Bell className="h-5 w-5 text-gray-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Recent Notifications
            </h2>
          </div>

          {notifications?.items.length ? (
            <ul className="space-y-3">
              {notifications.items.map((n) => (
                <li
                  key={n.id}
                  className="flex items-start gap-3 text-sm"
                >
                  <span
                    className={`mt-1 h-2 w-2 rounded-full shrink-0 ${
                      n.is_read ? "bg-gray-300 dark:bg-gray-600" : "bg-indigo-500"
                    }`}
                  />
                  <div>
                    <p className="font-medium text-gray-900 dark:text-gray-100">
                      {n.title}
                    </p>
                    <p className="text-gray-500 dark:text-gray-400 line-clamp-1">
                      {n.message}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-400 text-sm">No notifications yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
