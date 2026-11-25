import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Bell, BookOpen, Globe, HardDrive, Plus } from "lucide-react";
import { Link } from "react-router-dom";

import { ImportModal } from "../components/fics/ImportModal";
import { getFics, importFic } from "../api/fics";
import { getNotifications } from "../api/notifications";
import { getSources } from "../api/sources";
import { getStorageInfo, getStorageWarnings } from "../api/storage";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useContext } from "react";
import { ToastContext } from "../contexts/ToastContext";

function formatBytes(bytes: number): string {
  if (bytes === 0) {
    return "0 B";
  }
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

const statusColors = {
  valid: "bg-green-500",
  expired: "bg-red-500",
  unknown: "bg-yellow-500",
};

export function DashboardPage() {
  const { showToast } = useContext(ToastContext);
  const queryClient = useQueryClient();
  const [showImport, setShowImport] = useState(false);

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

  const { data: ficsData } = useQuery({
    queryKey: ["fics", "dashboard"],
    queryFn: () => getFics({ sort: "-date_archived", limit: 5 }),
  });

  const { data: sources = [] } = useQuery({
    queryKey: ["sources"],
    queryFn: getSources,
  });

  const importMutation = useMutation({
    mutationFn: (url: string) => importFic(url),
    onSuccess: () => {
      showToast("Import started", "success");
      setShowImport(false);
      queryClient.invalidateQueries({ queryKey: ["fics"] });
    },
    onError: () => {
      showToast("Failed to start import", "error");
    },
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

  const totalFics = ficsData?.total || 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Dashboard
        </h1>
        <button
          onClick={() => setShowImport(true)}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Quick Import
        </button>
      </div>

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

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link
          to="/library"
          className="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 p-4 hover:border-indigo-300 dark:hover:border-indigo-600 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-900/30">
              <BookOpen className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{totalFics}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Fics Archived</p>
            </div>
          </div>
        </Link>

        <Link
          to="/settings/sources"
          className="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 p-4 hover:border-indigo-300 dark:hover:border-indigo-600 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-50 dark:bg-green-900/30">
              <Globe className="h-5 w-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{sources.length}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Sources Configured</p>
            </div>
          </div>
        </Link>

        <div className="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-50 dark:bg-purple-900/30">
              <HardDrive className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {storage ? formatBytes(storage.storage_used_bytes) : "—"}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Storage Used</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Source Health */}
        {sources.length > 0 && (
          <div className="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center gap-2 mb-4">
              <Globe className="h-5 w-5 text-gray-400" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Source Health
              </h2>
            </div>
            <div className="space-y-2">
              {sources.map((source) => (
                <div key={source.id} className="flex items-center justify-between text-sm">
                  <span className="text-gray-700 dark:text-gray-300">{source.label}</span>
                  <div className="flex items-center gap-2">
                    <span
                      className={`h-2.5 w-2.5 rounded-full ${
                        statusColors[source.auth_status as keyof typeof statusColors] || "bg-gray-400"
                      }`}
                    />
                    <span className="text-gray-500 dark:text-gray-400 capitalize text-xs">
                      {source.auth_status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

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

        {/* Recent Imports */}
        <div className="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-4">
            <BookOpen className="h-5 w-5 text-gray-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Recent Imports
            </h2>
          </div>

          {ficsData?.items.length ? (
            <ul className="space-y-2">
              {ficsData.items.map((fic) => (
                <li key={fic.id}>
                  <Link
                    to={`/library/${fic.id}`}
                    className="flex items-center justify-between text-sm hover:text-indigo-600 dark:hover:text-indigo-400"
                  >
                    <span className="text-gray-900 dark:text-gray-100 truncate">{fic.title}</span>
                    <span className="text-xs text-gray-400 shrink-0 ml-2">
                      {fic.source_site.toUpperCase()}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-400 text-sm">No fics imported yet.</p>
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

      {showImport && (
        <ImportModal
          onImport={(url) => importMutation.mutate(url)}
          onClose={() => setShowImport(false)}
          isLoading={importMutation.isPending}
        />
      )}
    </div>
  );
}
